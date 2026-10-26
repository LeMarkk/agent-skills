#!/usr/bin/env python3
"""guard: checks shell commands and file edits before Claude Code runs them.

Hook mode (PreToolUse, reads the hook JSON on stdin):
    guard.py hook
CLI mode:
    guard.py check "<command>"     show what guard would decide for a command
    guard.py freeze <dir>          only allow file edits inside <dir> for this project
    guard.py unfreeze              remove this project's edit lock
    guard.py status                show this project's lock and rule files

Decisions: "deny" stops the command, "ask" makes Claude Code ask the person,
no output means guard has no objection and the normal permission flow applies.
guard never auto-approves anything.

Method credit: gstack /careful and /freeze (MIT), see NOTICE in the repo root.
Standard library only; needs Python 3.8+.
"""

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

DENY, ASK, OK = "deny", "ask", None
RANK = {DENY: 2, ASK: 1, OK: 0}

STATE_DIR = os.path.join(os.path.expanduser("~"), ".claude", "devkit", "guard")
FREEZE_FILE = os.path.join(STATE_DIR, "freeze.json")

# Targets whose recursive deletion is never what anyone means.
CATASTROPHIC = {
    "/", "/*", "~", "~/", "~/*", "$HOME", "$HOME/", "$HOME/*", "${HOME}", "${HOME}/",
    "${HOME}/*", "/home", "/home/", "/home/*", "/root", "/etc", "/usr", "/var",
    "/bin", "/sbin", "/lib", "/boot", "/opt", "/srv", "/mnt", "/dev", "/proc", "/sys",
    "C:\\", "C:/", "%USERPROFILE%",
}
# Build output and caches that are safe to delete when named relatively.
SAFE_DIRS = {
    "node_modules", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit", ".turbo",
    "coverage", ".nyc_output", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".parcel-cache", ".cache", "target", "tmp", ".tmp", ".dart_tool",
    "playwright-report", "test-results", "storybook-static", "bin", "obj",
}
PROTECTED_BRANCHES = {"main", "master", "production", "prod", "release"}
SECRET_FILE = re.compile(
    r"(^|/)(\.env(\.(?!example$|sample$|template$)[\w.-]+)?|.*\.(jks|keystore|p12|pfx|pem|key)"
    r"|google-services\.json|GoogleService-Info\.plist|id_(rsa|ed25519|ecdsa))$"
)

SQL_RULES = [
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|OWNED|ROLE|USER)\b", re.I), ASK,
     "SQL DROP deletes data or access"),
    (re.compile(r"\bTRUNCATE\s+(TABLE\s+)?[\w.\"`]+", re.I), ASK, "SQL TRUNCATE empties a table"),
    (re.compile(r"\bALTER\s+TABLE\s+\S+\s+DROP\b", re.I), ASK, "ALTER TABLE ... DROP removes a column or constraint"),
    (re.compile(r"\bFLUSHALL\b|\bFLUSHDB\b", re.I), ASK, "Redis FLUSH wipes keys"),
    (re.compile(r"\bdropDatabase\s*\(", re.I), ASK, "dropDatabase deletes a database"),
]
DELETE_NO_WHERE = re.compile(r"\bDELETE\s+FROM\s+[\w.\"`]+(?P<rest>[^;]*)", re.I)
UPDATE_NO_WHERE = re.compile(r"\bUPDATE\s+[\w.\"`]+\s+SET\b(?P<rest>[^;]*)", re.I)
RAW_RULES = [
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"), DENY, "fork bomb"),
    (re.compile(r">\s*/dev/(sd[a-z]|nvme\d|disk\d|hd[a-z]|vd[a-z])"), DENY, "writes over a raw disk"),
    (re.compile(r"\b(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(ba|z|da)?sh\b"), ASK,
     "pipes a download straight into a shell"),
]

SEPARATORS = re.compile(r"\|\||&&|;|\||\n|&(?!>)")
COMMIT_MSG = re.compile(r"""(-m|--message)(=|\s+)("(\\.|[^"\\])*"|'[^']*'|\S+)""")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n.*?\n\1\b", re.S)
WRAPPERS = {"sudo", "doas", "nice", "nohup", "time", "command", "builtin", "exec", "stdbuf", "ionice"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish"}


# ---------------------------------------------------------------- helpers

def git(cwd, *args):
    try:
        out = subprocess.run(["git", "-C", cwd or ".", *args], capture_output=True, text=True, timeout=3)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def project_root(cwd):
    root = os.environ.get("CLAUDE_PROJECT_DIR") or git(cwd, "rev-parse", "--show-toplevel") or cwd or os.getcwd()
    return os.path.realpath(root)


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def project_rules(root):
    rules = load_json(os.path.join(root, ".claude", "guard.json"), {})
    return rules if isinstance(rules, dict) else {}


def split_words(text):
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.split()


def worst(findings):
    decision = OK
    for d, _ in findings:
        if RANK[d] > RANK[decision]:
            decision = d
    return decision


# ---------------------------------------------------------------- commands

def strip_noise(command):
    """Drop git/gh message text (commit -m, PR bodies in heredocs), which is prose, not commands.

    Heredocs fed to anything else (psql, bash) are kept: they are commands.
    """
    if re.match(r"^\s*(git|gh)\b", command):
        command = HEREDOC.sub(" ", command)
        command = re.sub(r"""(--body|--title|-b|-t)(=|\s+)("(\\.|[^"\\])*"|'[^']*')""", r"\1 TEXT", command)
    return COMMIT_MSG.sub(r"\1 MSG", command)


def segments(command):
    for part in SEPARATORS.split(command):
        part = part.strip().lstrip("({").rstrip(")}").strip()
        if part:
            yield part


def unwrap(argv):
    """Remove sudo/env/xargs-style prefixes; return (argv, via_xargs)."""
    via_xargs = False
    while argv:
        head = os.path.basename(argv[0])
        if head in WRAPPERS:
            argv = argv[1:]
            while argv and argv[0].startswith("-"):
                takes_value = head in ("sudo", "doas") and argv[0] in ("-u", "-g", "-U", "-C", "-h", "-p", "-r", "-t")
                argv = argv[2:] if takes_value else argv[1:]
        elif head == "env" or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", argv[0]):
            argv = argv[1:]
            while argv and (argv[0].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", argv[0])):
                argv = argv[1:]
        elif head == "xargs":
            via_xargs = True
            argv = argv[1:]
            while argv and argv[0].startswith("-"):
                argv = argv[1:]
        elif head == "timeout" and len(argv) > 2:
            argv = argv[2:]
        else:
            break
    return argv, via_xargs


def check_rm(args, via_xargs):
    flags = [a for a in args if a.startswith("-") and a != "-"]
    recursive = any(a == "--recursive" or re.match(r"^-[a-zA-Z]*[rR]", a) for a in flags)
    if not recursive:
        return []
    targets = [a for a in args if not a.startswith("-")]
    if via_xargs or not targets:
        return [(ASK, "recursive rm on paths guard can't see")]
    out = []
    for t in targets:
        norm = t.rstrip("/") or "/"
        if t in CATASTROPHIC or norm in CATASTROPHIC or re.match(r"^/+\*?$", t):
            out.append((DENY, f"recursive delete of {t}"))
        elif norm in {".", "..", "*", "./*"}:
            out.append((ASK, f"recursive delete of everything in {t}"))
        elif "$" in t:
            out.append((ASK, f"recursive delete of {t}; an empty variable would make this a much bigger delete"))
        elif t.startswith("/tmp/") or t.startswith("/var/tmp/"):
            continue
        elif not os.path.isabs(t) and ".." not in t.split("/") and os.path.basename(norm) in SAFE_DIRS:
            continue
        else:
            out.append((ASK, f"recursive delete of {t}"))
    return out


def check_git(args, cwd):
    # skip global options such as -C <dir> and -c key=value
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree") else 1
    if i >= len(args):
        return []
    sub, rest = args[i], args[i + 1:]
    out = []
    if "--no-verify" in rest and sub in ("commit", "push", "merge", "am"):
        out.append((ASK, f"git {sub} --no-verify skips the repo's checks"))
    if sub == "push":
        force = [a for a in rest if a in ("-f", "--force") or re.match(r"^-[a-zA-Z]*f", a) and not a.startswith("--")]
        lease = [a for a in rest if a.startswith("--force-with-lease") or a.startswith("--force-if-includes")]
        plus = [a for a in rest if a.startswith("+")]
        if "--delete" in rest or "-d" in rest or any(a.startswith(":") and len(a) > 1 for a in rest):
            out.append((ASK, "git push deletes a remote branch"))
        if force or lease or plus:
            positional = [a for a in rest if not a.startswith("-")]
            refs = positional[1:] if len(positional) > 1 else []
            branches = {r.lstrip("+").split(":")[-1].replace("refs/heads/", "") for r in refs}
            if not branches:
                current = git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
                branches = {current} if current else set()
            default = git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").split("/")[-1]
            protected = PROTECTED_BRANCHES | ({default} if default else set())
            if not branches or branches & protected:
                out.append((DENY, "force-push to the default or a protected branch rewrites shared history"))
            elif force or plus:
                out.append((ASK, "force-push rewrites the branch history on the remote"))
    elif sub == "reset" and "--hard" in rest:
        out.append((ASK, "git reset --hard throws away uncommitted work"))
    elif sub == "clean" and any(re.match(r"^-[a-zA-Z]*f", a) or a == "--force" for a in rest):
        out.append((ASK, "git clean deletes untracked files"))
    elif sub in ("checkout", "restore") and any(a in (".", "--", ":/") for a in rest) and "--staged" not in rest:
        if sub == "restore" or "." in rest or ":/" in rest:
            out.append((ASK, f"git {sub} discards local changes"))
    elif sub == "branch" and any(a in ("-D", "--delete") or a == "-d" and "--force" in rest for a in rest):
        out.append((ASK, "git branch -D deletes a branch even if unmerged"))
    elif sub == "stash" and rest[:1] and rest[0] in ("drop", "clear"):
        out.append((ASK, f"git stash {rest[0]} deletes stashed work"))
    elif sub in ("filter-branch", "filter-repo"):
        out.append((ASK, f"git {sub} rewrites history"))
    elif sub == "add":
        if any(a in ("-f", "--force") for a in rest):
            out.append((ASK, "git add --force adds ignored files, which are often secrets"))
        for a in rest:
            if SECRET_FILE.search(a):
                out.append((ASK, f"git add {a} looks like a secret or key file"))
    return out


def check_docker(args):
    words = [a for a in args if not a.startswith("-")]
    flags = set(a for a in args if a.startswith("-"))
    if words[:1] == ["compose"]:
        words = words[1:]
        if words[:1] == ["down"] and (flags & {"-v", "--volumes"}):
            return [(ASK, "docker compose down -v deletes the project's volumes and their data")]
        if words[:1] == ["rm"] and (flags & {"-f", "--force", "-v"}):
            return [(ASK, "docker compose rm removes containers")]
        return []
    pair = " ".join(words[:2])
    if words[:1] == ["rm"] and (flags & {"-f", "--force", "-v", "--volumes"}):
        return [(ASK, "docker rm -f stops and removes containers")]
    if words[:1] == ["rmi"] or pair in ("image rm", "image prune", "system prune", "container prune",
                                         "volume rm", "volume prune", "network prune", "builder prune"):
        return [(ASK, f"docker {pair or words[0]} deletes images, containers or volumes")]
    if pair in ("stack rm", "service rm", "secret rm", "config rm", "node rm"):
        return [(ASK, f"docker {pair} removes it from the Swarm")]
    if pair == "swarm leave" and flags & {"-f", "--force"}:
        return [(ASK, "docker swarm leave --force can take the node out of the cluster")]
    return []


def check_cloud(tool, args):
    words = [a for a in args if not a.startswith("-")]
    if tool == "aws":
        if len(words) >= 2:
            svc, op = words[0], words[1]
            if svc == "s3" and op == "rm" and "--recursive" in args:
                return [(ASK, "aws s3 rm --recursive deletes every object under the prefix")]
            if svc == "s3" and op == "rb":
                return [(ASK, "aws s3 rb deletes a bucket")]
            if svc == "s3" and op == "sync" and "--delete" in args:
                return [(ASK, "aws s3 sync --delete removes files at the destination")]
            if re.match(r"^(delete|terminate|remove|deregister|purge|disable|stop|revoke)-", op):
                return [(ASK, f"aws {svc} {op} changes or removes live resources")]
            if svc == "ecs" and op == "update-service":
                return [(ASK, "aws ecs update-service changes a running service")]
        return []
    if tool in ("oci", "gcloud", "az", "doctl", "flyctl", "fly", "heroku", "vercel"):
        if any(w in ("delete", "terminate", "destroy", "remove", "rm", "purge") for w in words):
            return [(ASK, f"{tool} command deletes live resources")]
        return []
    if tool in ("terraform", "tofu", "terragrunt", "pulumi"):
        if words[:1] in (["destroy"], ["down"]):
            return [(ASK, f"{tool} destroy tears down infrastructure")]
        if words[:1] in (["apply"], ["up"]) and any(a in ("-destroy", "--destroy", "-auto-approve", "--auto-approve", "--yes", "-y") for a in args):
            return [(ASK, f"{tool} {words[0]} without a review step changes infrastructure")]
        if words[:2] in (["state", "rm"], ["workspace", "delete"]):
            return [(ASK, f"{tool} {' '.join(words[:2])} removes state")]
        return []
    if tool in ("kubectl", "oc") and words[:1] in (["delete"], ["drain"]):
        return [(ASK, f"{tool} {words[0]} affects running workloads")]
    if tool == "helm" and words[:1] in (["uninstall"], ["delete"], ["rollback"]):
        return [(ASK, f"helm {words[0]} changes a release")]
    return []


def check_argv(argv, cwd, depth):
    argv, via_xargs = unwrap(argv)
    if not argv:
        return []
    tool = os.path.basename(argv[0])
    args = argv[1:]
    if tool in SHELLS and "-c" in args and depth < 3:
        idx = args.index("-c")
        if idx + 1 < len(args):
            return check_command(args[idx + 1], cwd, depth + 1)
    if tool == "rm":
        return check_rm(args, via_xargs)
    if tool == "find" and ("-delete" in args or any(a in ("rm", "/bin/rm") for a in args)):
        return [(ASK, "find ... -delete removes every match")]
    if tool == "git":
        return check_git(args, cwd)
    if tool in ("docker", "podman"):
        return check_docker(args)
    if tool == "docker-compose":
        return check_docker(["compose", *args])
    if tool in ("dropdb", "dropuser"):
        return [(ASK, f"{tool} deletes a database object")]
    if tool.startswith("mkfs") or tool in ("wipefs", "fdisk", "parted", "sfdisk"):
        return [(DENY, f"{tool} rewrites a disk")]
    if tool == "dd" and any(a.startswith("of=/dev/") for a in args):
        return [(DENY, "dd onto a device overwrites it")]
    if tool == "shred":
        return [(ASK, "shred destroys file contents")]
    if tool in ("chmod", "chown") and any(re.match(r"^-[a-zA-Z]*R", a) or a == "--recursive" for a in args):
        targets = [a for a in args if not a.startswith("-")][1:]
        if any(t.rstrip("/") in CATASTROPHIC or t in CATASTROPHIC for t in targets):
            return [(DENY, f"recursive {tool} on a system path")]
        if tool == "chmod" and any(a in ("777", "a+rwx") for a in args):
            return [(ASK, "chmod -R 777 makes everything writable by anyone")]
        return []
    if tool == "crontab" and "-r" in args:
        return [(ASK, "crontab -r deletes every scheduled job")]
    if tool in ("shutdown", "reboot", "halt", "poweroff") or (tool == "systemctl" and args[:1] and args[0] in ("reboot", "poweroff", "halt")):
        return [(ASK, f"{tool} takes this machine offline")]
    return check_cloud(tool, args)


def check_command(command, cwd, depth=0):
    text = strip_noise(command)
    findings = []
    for rx, decision, reason in RAW_RULES + SQL_RULES:
        if rx.search(text):
            findings.append((decision, reason))
    for rx, what in ((DELETE_NO_WHERE, "DELETE"), (UPDATE_NO_WHERE, "UPDATE")):
        for m in rx.finditer(text):
            if not re.search(r"\bWHERE\b", m.group("rest"), re.I):
                findings.append((ASK, f"SQL {what} without WHERE touches every row"))
    for seg in segments(text):
        findings.extend(check_argv(split_words(seg), cwd, depth))
    return findings


def check_project_rules(command, root):
    rules = project_rules(root)
    out = []
    for decision in (DENY, ASK):
        for rule in rules.get(decision, []) or []:
            try:
                if re.search(rule["pattern"], command):
                    out.append((decision, rule.get("reason") or f"matches this project's guard rule {rule['pattern']}"))
            except (KeyError, re.error, TypeError):
                continue
    for rule in rules.get("allow", []) or []:
        try:
            if re.fullmatch(rule["pattern"], command.strip()):
                return [], True
        except (KeyError, re.error, TypeError):
            continue
    return out, False


# ---------------------------------------------------------------- edits

def check_edit(path, cwd, tool):
    if not path:
        return []
    root = project_root(cwd)
    full = os.path.realpath(os.path.join(cwd or root, os.path.expanduser(path)))
    out = []
    frozen = load_json(FREEZE_FILE, {}).get(root)
    if frozen:
        home_claude = os.path.realpath(os.path.join(os.path.expanduser("~"), ".claude"))
        inside = lambda base: full == base or full.startswith(base.rstrip(os.sep) + os.sep)
        scratch = not inside(root) and (inside(home_claude) or inside("/tmp"))
        if not (inside(frozen) or scratch):
            out.append((DENY, f"edits are locked to {frozen} for this project; ask the person before unfreezing"))
    if full.startswith(root + os.sep) and os.path.exists(full) and tool != "NotebookEdit":
        rel = os.path.relpath(full, root)
        for rule in project_rules(root).get("protect_paths", []) or []:
            try:
                if fnmatch.fnmatch(rel, rule["glob"]):
                    out.append((ASK, rule.get("reason") or f"{rel} is protected in this project"))
            except (KeyError, TypeError):
                continue
    return out


# ---------------------------------------------------------------- entry points

def decide(payload):
    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    if tool in ("Bash", "PowerShell"):
        command = tin.get("command") or ""
        root = project_root(cwd)
        extra, allowed = check_project_rules(command, root)
        findings = [] if allowed else check_command(command, cwd) + extra
    elif tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        findings = check_edit(tin.get("file_path") or tin.get("notebook_path"), cwd, tool)
    else:
        findings = []
    decision = worst(findings)
    if decision is OK:
        return None
    reasons = []
    for d, r in findings:
        if d == decision and r not in reasons:
            reasons.append(r)
    lead = "Blocked" if decision == DENY else "Needs your OK"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": f"[guard] {lead}: " + "; ".join(reasons[:3]),
        }
    }


def hook():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    try:
        result = decide(payload)
    except Exception as exc:  # a bug in guard must not silently wave a command through
        result = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                         "permissionDecisionReason": f"[guard] could not check this ({exc.__class__.__name__}); approve only after reading it"}}
    if result:
        print(json.dumps(result))
    return 0


def save_freeze(data):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = FREEZE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, FREEZE_FILE)


def cli(argv):
    cmd = argv[0] if argv else "status"
    cwd = os.getcwd()
    root = project_root(cwd)
    data = load_json(FREEZE_FILE, {})
    if cmd == "check" and len(argv) > 1:
        result = decide({"tool_name": "Bash", "tool_input": {"command": argv[1]}, "cwd": cwd})
        print(result["hookSpecificOutput"]["permissionDecisionReason"] if result else "[guard] no objection")
        return 0
    if cmd == "freeze" and len(argv) > 1:
        target = os.path.realpath(os.path.expanduser(argv[1]))
        if not os.path.isdir(target):
            print(f"[guard] {target} is not a folder", file=sys.stderr)
            return 1
        data[root] = target
        save_freeze(data)
        print(f"[guard] edits in {root} are now locked to {target}")
        return 0
    if cmd == "unfreeze":
        removed = data.pop(root, None)
        save_freeze(data)
        print(f"[guard] edit lock removed ({removed})" if removed else "[guard] no edit lock was set")
        return 0
    if cmd == "status":
        print(f"project: {root}")
        print(f"edit lock: {data.get(root) or 'none'}")
        rules_path = os.path.join(root, ".claude", "guard.json")
        rules = project_rules(root)
        if rules:
            counts = {k: len(rules.get(k) or []) for k in ("deny", "ask", "allow", "protect_paths")}
            print(f"project rules: {rules_path} {counts}")
        else:
            print("project rules: none")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["hook"]:
        sys.exit(hook())
    sys.exit(cli(args))
