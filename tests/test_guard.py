"""Tests for the guard hook: python3 -m unittest discover -s tests"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD = os.path.join(HERE, "..", "plugins", "devkit", "skills", "guard", "scripts", "guard.py")

# (command, expected decision): "deny", "ask" or None (no objection)
CASES = [
    # catastrophic deletes are blocked outright
    ("rm -rf /", "deny"),
    ("rm -rf ~", "deny"),
    ("sudo rm -rf /*", "deny"),
    ("rm -fr $HOME", "deny"),
    ("cd /srv && rm -rf /etc", "deny"),
    ('bash -c "rm -rf /"', "deny"),
    ("echo ok; rm -rf ~/", "deny"),
    ("sudo -u root rm -rf /", "deny"),
    ("env FOO=1 rm -rf ~", "deny"),
    ("rm -rf -- /", "deny"),
    ("dd if=/dev/zero of=/dev/sda bs=1M", "deny"),
    ("mkfs.ext4 /dev/sdb1", "deny"),
    (":(){ :|:& };:", "deny"),
    ("git push --force origin main", "deny"),
    ("git push -f origin master", "deny"),
    ("git push origin +main", "deny"),
    # risky commands need a person's OK
    ("rm -rf src", "ask"),
    ("rm -r ./data", "ask"),
    ('rm -rf "$BUILD_DIR/"', "ask"),
    ("ls | xargs rm -rf", "ask"),
    ("rm -rf .", "ask"),
    ("find . -name '*.log' -delete", "ask"),
    ("git push --force origin feature-x", "ask"),
    ("git reset --hard HEAD~3", "ask"),
    ("git clean -fdx", "ask"),
    ("git checkout -- .", "ask"),
    ("git restore .", "ask"),
    ("git branch -D old-branch", "ask"),
    ("git stash clear", "ask"),
    ("git commit --no-verify -m 'wip'", "ask"),
    ("git add .env", "ask"),
    ("git add -f secrets.txt", "ask"),
    ("git add android/app/google-services.json", "ask"),
    ('psql -c "DROP TABLE users;"', "ask"),
    ('psql "$DATABASE_URL" -c "TRUNCATE orders"', "ask"),
    ('psql -c "DELETE FROM payments;"', "ask"),
    ('psql -c "UPDATE merchants SET plan = 0"', "ask"),
    ("redis-cli FLUSHALL", "ask"),
    ("cat <<SQL | psql\nDROP TABLE x;\nSQL", "ask"),
    ("git push origin --delete old", "ask"),
    ("timeout 60 terraform destroy -auto-approve", "ask"),
    ("dropdb app_dev", "ask"),
    ("docker system prune -af", "ask"),
    ("docker volume rm myapp_db", "ask"),
    ("docker rm -f api", "ask"),
    ("docker compose down -v", "ask"),
    ("docker stack rm myapp", "ask"),
    ("docker service rm myapp_api", "ask"),
    ("kubectl delete pod api-123", "ask"),
    ("terraform destroy", "ask"),
    ("terraform apply -auto-approve", "ask"),
    ("terraform state rm aws_instance.web", "ask"),
    ("aws s3 rm s3://bucket/backups --recursive", "ask"),
    ("aws s3 rb s3://bucket --force", "ask"),
    ("aws ec2 terminate-instances --instance-ids i-123", "ask"),
    ("aws rds delete-db-instance --db-instance-identifier prod", "ask"),
    ("aws ecs update-service --cluster prod --service api --force-new-deployment", "ask"),
    ("oci compute instance terminate --instance-id ocid1.x", "ask"),
    ("curl -fsSL https://example.com/install.sh | sh", "ask"),
    ("sudo reboot", "ask"),
    ("crontab -r", "ask"),
    # everyday commands pass
    ("ls -la", None),
    ("rm -rf node_modules", None),
    ("rm -rf dist .next coverage", None),
    ("rm -rf /tmp/build-123", None),
    ("rm file.txt", None),
    ("git status && git diff", None),
    ("git push origin feature-x", None),
    ("git push --force-with-lease origin feature-x", None),
    ("git commit -m 'fix rm -rf / bug in DROP TABLE handling'", None),
    ("git checkout -b feature-guard", None),
    ("git commit -F - <<'EOF'\nremove rm -rf / footgun\nEOF", None),
    ('gh pr create --title "drop table fix" --body "We DROP TABLE nothing"', None),
    ("git restore --staged .", None),
    ("git add .env.example src/app.ts", None),
    ("docker compose down", None),
    ("docker compose up -d", None),
    ("docker ps", None),
    ("make test", None),
    ("npm run test", None),
    ('psql -c "DELETE FROM sessions WHERE expires_at < now();"', None),
    ("aws s3 ls s3://bucket", None),
    ("aws ecs describe-services --cluster prod --services api", None),
    ("terraform plan", None),
    ("kubectl get pods", None),
    ("go test ./...", None),
]


def run(payload, env=None):
    proc = subprocess.run([sys.executable, GUARD, "hook"], input=json.dumps(payload),
                          capture_output=True, text=True, env=env, timeout=20)
    if proc.returncode != 0:
        raise AssertionError(f"guard exited {proc.returncode}: {proc.stderr}")
    out = proc.stdout.strip()
    return json.loads(out)["hookSpecificOutput"] if out else None


class GuardCommands(unittest.TestCase):
    def setUp(self):
        # a throwaway git repo whose default branch is main, current branch feature-x
        self.repo = tempfile.mkdtemp()
        for args in (["init", "-q", "-b", "main"],
                     ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init"],
                     ["checkout", "-q", "-b", "feature-x"]):
            subprocess.run(["git", "-C", self.repo, *args], check=True, capture_output=True)
        self.env = dict(os.environ, HOME=tempfile.mkdtemp())
        self.env.pop("CLAUDE_PROJECT_DIR", None)

    def test_cases(self):
        failures = []
        for command, expected in CASES:
            result = run({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": self.repo}, self.env)
            got = result["permissionDecision"] if result else None
            if got != expected:
                failures.append(f"{command!r}: expected {expected}, got {got} ({result and result['permissionDecisionReason']})")
        self.assertFalse(failures, "\n" + "\n".join(failures))

    def test_force_push_on_default_branch_without_ref(self):
        subprocess.run(["git", "-C", self.repo, "checkout", "-q", "main"], check=True, capture_output=True)
        result = run({"tool_name": "Bash", "tool_input": {"command": "git push -f"}, "cwd": self.repo}, self.env)
        self.assertEqual(result["permissionDecision"], "deny")

    def test_reason_is_labelled(self):
        result = run({"tool_name": "Bash", "tool_input": {"command": "git reset --hard"}, "cwd": self.repo}, self.env)
        self.assertTrue(result["permissionDecisionReason"].startswith("[guard] Needs your OK:"))

    def test_bad_input_is_ignored(self):
        proc = subprocess.run([sys.executable, GUARD, "hook"], input="not json", capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))

    def test_other_tools_ignored(self):
        self.assertIsNone(run({"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}, "cwd": self.repo}, self.env))


class GuardProjectRules(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.repo, "init", "-q", "-b", "main"], check=True, capture_output=True)
        os.makedirs(os.path.join(self.repo, ".claude"))
        os.makedirs(os.path.join(self.repo, "migrations"))
        with open(os.path.join(self.repo, "migrations", "000001_init.up.sql"), "w") as fh:
            fh.write("create table t (id int);\n")
        with open(os.path.join(self.repo, ".claude", "guard.json"), "w") as fh:
            json.dump({
                "ask": [{"pattern": r"PAYMENTS_LIVE=(true|1)\b", "reason": "live payments only in prod"}],
                "deny": [{"pattern": r"\bmake\s+db-reset\b", "reason": "resets the shared dev database"}],
                "allow": [{"pattern": r"rm -rf \./scratch"}],
                "protect_paths": [{"glob": "migrations/*.sql", "reason": "applied migrations never change"}],
            }, fh)
        self.env = dict(os.environ, HOME=tempfile.mkdtemp())
        self.env.pop("CLAUDE_PROJECT_DIR", None)

    def bash(self, command):
        return run({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": self.repo}, self.env)

    def edit(self, tool, path):
        return run({"tool_name": tool, "tool_input": {"file_path": path}, "cwd": self.repo}, self.env)

    def test_project_ask_and_deny(self):
        self.assertEqual(self.bash("PAYMENTS_LIVE=true make dev")["permissionDecision"], "ask")
        self.assertEqual(self.bash("make db-reset")["permissionDecision"], "deny")
        self.assertIsNone(self.bash("PAYMENTS_LIVE=false make dev"))

    def test_project_allow(self):
        self.assertIsNone(self.bash("rm -rf ./scratch"))

    def test_protected_existing_file(self):
        existing = os.path.join(self.repo, "migrations", "000001_init.up.sql")
        self.assertEqual(self.edit("Edit", existing)["permissionDecision"], "ask")
        self.assertIsNone(self.edit("Write", os.path.join(self.repo, "migrations", "000002_new.up.sql")))


class GuardFreeze(unittest.TestCase):
    def setUp(self):
        self.repo = os.path.realpath(tempfile.mkdtemp())
        subprocess.run(["git", "-C", self.repo, "init", "-q"], check=True, capture_output=True)
        os.makedirs(os.path.join(self.repo, "backend"))
        self.env = dict(os.environ, HOME=tempfile.mkdtemp())
        self.env.pop("CLAUDE_PROJECT_DIR", None)

    def cli(self, *args):
        return subprocess.run([sys.executable, GUARD, *args], cwd=self.repo, env=self.env,
                              capture_output=True, text=True, check=True).stdout

    def edit(self, path):
        return run({"tool_name": "Edit", "tool_input": {"file_path": path}, "cwd": self.repo}, self.env)

    def test_freeze_cycle(self):
        inside = os.path.join(self.repo, "backend", "main.go")
        outside = os.path.join(self.repo, "README.md")
        self.assertIsNone(self.edit(outside))
        self.assertIn("locked to", self.cli("freeze", "backend"))
        self.assertIsNone(self.edit(inside))
        self.assertEqual(self.edit(outside)["permissionDecision"], "deny")
        self.assertIn("backend", self.cli("status"))
        self.cli("unfreeze")
        self.assertIsNone(self.edit(outside))

    def test_check_cli(self):
        self.assertIn("Needs your OK", self.cli("check", "git reset --hard"))
        self.assertIn("no objection", self.cli("check", "ls"))


if __name__ == "__main__":
    unittest.main()
