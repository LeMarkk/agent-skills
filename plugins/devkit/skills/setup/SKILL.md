---
name: setup
description: Adds devkit to a project so everyone who opens it in Claude Code gets the guard hook and the debug skill, and writes guard rules that fit the project's stack (migrations, ORMs, payment keys, generated files). Use when someone says set up devkit, add devkit to this repo, configure guard for this project, or starts a new project and wants these skills in it.
---

# setup

Wire devkit into the current repository and give guard rules that fit it. Work from the repository root (`git rev-parse --show-toplevel`). Change only `.claude/settings.json`, `.claude/guard.json` and, if the person agrees, a few lines of `CLAUDE.md`. Don't commit or push unless asked.

## 1. Enable the plugin for the project

Read `.claude/settings.json` if it exists and merge; never drop keys that are already there. Add:

```json
{
  "extraKnownMarketplaces": {
    "agent-skills": {
      "source": { "source": "github", "repo": "LeMarkk/agent-skills" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "devkit@agent-skills": true
  }
}
```

If the person installs devkit from a fork, use their fork's `owner/repo` instead. If the marketplace is already listed under another name, keep that name and use it in `enabledPlugins` (`devkit@<that name>`).

## 2. Look at the stack

Before proposing rules, find out what the project actually uses. Check, without changing anything:

- Migration folders and tools: `migrations/`, `db/migrate/`, `prisma/migrations/`, `alembic/versions/`, `*/migrations/*.py`, a Drizzle `out` folder (in `drizzle.config.*`), `supabase/migrations/`, Flyway or Liquibase config.
- Package scripts and Makefile targets that reset or drop data (`db:reset`, `migrate:fresh`, `make db-reset`).
- Generated files that must not be edited by hand (snapshots, golden or fixture files the project regenerates by script, lockfiles are fine to leave alone).
- Live-mode switches in `.env.example` (anything like `*_LIVE`, `*_PRODUCTION`, a payment provider's live key prefix).
- Append-only or audit tables the docs or schema describe.
- Rules already written in `CLAUDE.md`, `CONTRIBUTING.md` or `README.md` ("never edit an applied migration", "status changes only through …"). These are the best source: turn each into a guard rule where a command or a path can express it.

## 3. Propose `.claude/guard.json`

Build the rules from what you found, using the matching entries in `references/rules-catalog.md`. Adjust paths to the project's real folders. Prefer `ask` over `deny`: `deny` is for things nobody on the team should ever run from an agent. Keep `allow` entries rare and narrow.

Show the person the proposed file, one line of reason per rule, and wait for their OK before writing it. If `.claude/guard.json` already exists, propose additions to it instead of replacing it.

## 4. Test every rule

Load the `guard` skill to find its script, then for each rule run its `check` command from the repo root with a command that should match and one that shouldn't, for example:

```
python3 "<guard skill base directory>/scripts/guard.py" check "npx prisma migrate reset"
python3 "<guard skill base directory>/scripts/guard.py" check "npx prisma migrate dev"
```

For `protect_paths`, confirm the glob matches an existing file with `git ls-files '<glob>'`; it should list the files you meant and nothing else. Fix any rule that misses or over-matches before reporting.

## 5. Tell the team

Offer to add a short section to `CLAUDE.md`:

```markdown
## Agent skills
- `.claude/settings.json` enables the `devkit` plugin (guard hook and /devkit:debug). Project-specific guard rules are in `.claude/guard.json`.
- Use /devkit:debug for bugs and failing tests: root cause first, a regression test that fails before the fix.
- If guard stops a command, don't reword it to get past the check; ask.
```

Finish with what changed, the rules added, and two things each teammate needs: read access to the marketplace repo if it's private, and `python3` (3.10 or later) on their PATH for the hook. They get the plugin the next time they open the project in Claude Code and trust the folder; `/plugin` shows it under Installed.
