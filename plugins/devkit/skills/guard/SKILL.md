---
name: guard
description: Explains and controls the always-on guard hook that stops destructive shell commands, and locks file edits to one folder ("freeze") for focused or production work. Use when a command was stopped with "[guard]", or the user says freeze, lock edits, be careful, guard status, unfreeze, or asks what guard blocks.
---

# guard

guard is a PreToolUse hook that runs on every Bash, PowerShell, Edit, Write, MultiEdit and NotebookEdit call while the devkit plugin is enabled. It is always on; this skill is how you explain it and use its edit lock. Its script is `scripts/guard.py` in this skill's base directory (shown when the skill loads). Below, `GUARD` means `python3 "<base directory>/scripts/guard.py"`.

## What it decides

- **Blocked** (`deny`): things nobody means to do. Recursive delete of `/`, `~`, `$HOME` or a system folder; force-push to `main`, `master`, the remote's default branch or another protected branch; `dd`/`mkfs` onto a disk; fork bombs; edits outside a frozen folder.
- **Needs your OK** (`ask`): risky but sometimes right. Any other recursive `rm` (build folders like `node_modules`, `dist`, `.next`, `coverage` and anything under `/tmp` pass); `find -delete`; `git reset --hard`, `clean -f`, `checkout -- .`, `branch -D`, `stash clear`, force-push to a feature branch, `--no-verify`, adding `.env`/keys/`google-services.json`; SQL `DROP`, `TRUNCATE`, `DELETE`/`UPDATE` without `WHERE`; Docker removes and prunes, `compose down -v`, `stack rm`, `service rm`; `kubectl delete`, `terraform destroy`/`apply -auto-approve`; AWS/OCI/gcloud delete, terminate and `ecs update-service`; `curl … | sh`; reboot/shutdown.
- Everything else gets no objection from guard and goes through Claude Code's normal permissions. guard never auto-approves.

Project rules add to this from `.claude/guard.json` in the repo (format below).

## When a command is stopped

1. Tell the person, in one line, what was stopped and guard's reason.
2. Never reword, split, wrap or encode the command to get past guard, and never edit `guard.json` or the freeze state to loosen a rule unless the person asks for that change.
3. For **Needs your OK**, the person approves or declines in Claude Code's prompt. If they decline, offer a safer route (a dry run, a narrower path, a backup first).
4. For **Blocked**, explain the safe alternative. If the person truly needs it, they run it themselves.

## Edit lock (freeze)

Use when debugging one module, working near production config, or when the person says "only touch X".

- Lock: `GUARD freeze <folder>` (run from inside the project). Edits outside that folder are blocked for this project, in every session, until unlocked. `~/.claude` and `/tmp` stay editable when they are outside the project.
- Status: `GUARD status` shows the lock and any project rules.
- Unlock: `GUARD unfreeze` — only when the person asks or the focused task is done; say that you unlocked it.
- The lock covers Claude's file-edit tools, not shell redirects. Don't use `sed -i`, `>` or `tee` to change files outside the lock either.

## Checking a command

`GUARD check "<command>"` prints what guard would decide, without running anything. Use it to answer "would guard stop this?" or to test a new project rule.

## Project rules: `.claude/guard.json`

```json
{
  "ask":   [{"pattern": "PAYMENTS_LIVE=(true|1)\\b", "reason": "live payment keys only in prod"}],
  "deny":  [{"pattern": "\\bmake\\s+db-reset\\b", "reason": "resets the shared dev database"}],
  "allow": [{"pattern": "rm -rf \\./\\.local-cache"}],
  "protect_paths": [{"glob": "backend/migrations/*.sql", "reason": "applied migrations never change; add a new one"}]
}
```

- `ask`/`deny`: Python regexes searched in the whole command.
- `allow`: a regex that must match the whole command; a match skips every check for that command, so keep these narrow.
- `protect_paths`: globs relative to the repo root; editing or overwriting an existing matching file needs the person's OK (new files are fine).

## Limits to be honest about

guard reads command text. It can't see what a script, Makefile target or SQL file will do when run, and a determined person can always get around it. It is a seatbelt against mistakes, not a security boundary. Turning it off is done by a person, by disabling the devkit plugin with `/plugin`.
