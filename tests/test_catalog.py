"""Every rule in the setup skill's catalog parses, and catches what it says without over-matching."""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "plugins", "devkit", "skills")
GUARD = os.path.join(ROOT, "guard", "scripts", "guard.py")
CATALOG = os.path.join(ROOT, "setup", "references", "rules-catalog.md")

CASES = [
    ("npx prisma migrate reset", "ask"), ("npx prisma migrate dev", None),
    ("npx prisma db push --accept-data-loss", "ask"), ("npx prisma db push", None),
    ("npx drizzle-kit push", "ask"), ("npx drizzle-kit generate", None),
    ("migrate -path migrations -database $DB down 1", "ask"),
    ("migrate -path migrations -database $DB force 3", "ask"),
    ("migrate -path migrations -database $DB up", None),
    ("npm run db:migrate && docker compose down", None),
    ("goose postgres $DB reset", "ask"), ("goose -dir migrations postgres $DB down", "ask"),
    ("goose postgres $DB up", None),
    ("bin/rails db:reset", "ask"), ("bin/rails db:migrate", None),
    ("python manage.py flush", "ask"), ("python manage.py migrate shop zero", "ask"),
    ("python manage.py migrate", None),
    ("alembic downgrade -1", "ask"), ("alembic upgrade head", None),
    ("php artisan migrate:fresh", "ask"), ("php artisan migrate", None),
    ("flyway clean", "ask"), ("flyway migrate", None), ("liquibase rollback-count 1", "ask"),
    ("supabase db reset", "ask"), ("supabase db push", None),
    ("knex migrate:rollback", "ask"), ("knex migrate:latest", None),
    ("PAYMENTS_LIVE=true npm start", "ask"), ("PAYMENTS_LIVE=false npm start", None),
    ("NODE_ENV=production npm run db:migrate", "ask"),
    ("npm run db:reset", "ask"), ("make db-reset", "ask"), ("make test", None),
    ("make deploy-prod", "deny"),
    ("psql -c \"UPDATE orders SET status = 'paid' WHERE id = 1\"", "ask"),
    ('psql -c "DELETE FROM audit_log WHERE id = 1"', "ask"),
]


def catalog_rules():
    merged = {"ask": [], "deny": [], "protect_paths": []}
    with open(CATALOG, encoding="utf-8") as fh:
        text = fh.read()
    for block in re.findall(r"```json\n(.*?)```", text, re.S):
        try:
            objs = [json.loads(block)]
        except json.JSONDecodeError:
            objs = [json.loads(line) for line in block.strip().splitlines()]
        for obj in objs:
            if "pattern" in obj:
                merged["ask"].append(obj)
            elif "glob" in obj:
                merged["protect_paths"].append(obj)
            else:
                for key in merged:
                    merged[key] += obj.get(key, [])
    return merged


class Catalog(unittest.TestCase):
    def test_rules_parse_and_compile(self):
        rules = catalog_rules()
        self.assertGreater(len(rules["ask"]), 20)
        for rule in rules["ask"] + rules["deny"]:
            re.compile(rule["pattern"])
            self.assertTrue(rule.get("reason"), rule)
        for rule in rules["protect_paths"]:
            self.assertTrue(rule.get("glob") and rule.get("reason"), rule)

    def test_rules_match_what_they_claim(self):
        repo = tempfile.mkdtemp()
        subprocess.run(["git", "-C", repo, "init", "-q"], check=True, capture_output=True)
        os.makedirs(os.path.join(repo, ".claude"))
        with open(os.path.join(repo, ".claude", "guard.json"), "w") as fh:
            json.dump(catalog_rules(), fh)
        env = dict(os.environ, HOME=tempfile.mkdtemp())
        env.pop("CLAUDE_PROJECT_DIR", None)
        failures = []
        for command, expected in CASES:
            out = subprocess.run([sys.executable, GUARD, "check", command], cwd=repo, env=env,
                                 capture_output=True, text=True, check=True).stdout
            got = "deny" if "Blocked" in out else "ask" if "Needs your OK" in out else None
            if got != expected:
                failures.append(f"{command!r}: expected {expected}, got {got} ({out.strip()})")
        self.assertFalse(failures, "\n" + "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
