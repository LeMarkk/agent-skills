# agent-skills

Claude Code skills and hooks that make agent work safer, for any project. Add them to your repo and everyone who opens it in Claude Code, including subagents, gets:

| Part | What it does |
|---|---|
| **guard** hook | Runs before every shell command and file edit. Blocks the catastrophic (recursive delete of `/` or `~`, force-push to `main`, writing to a raw disk) and asks before the risky (other recursive deletes, `git reset --hard`, SQL `DROP`/`TRUNCATE`, Docker prunes and `stack rm`, `terraform destroy`, AWS/OCI deletes, `curl \| sh`). Never auto-approves. |
| `/devkit:guard` | Explains a stopped command, locks edits to one folder (`freeze`), shows status, tests a command with `check`. |
| `/devkit:debug` | Root cause before any fix: reproduce, lock scope, test one hypothesis at a time, stop after 3 misses, write a regression test that fails first, then report. Claude also uses it on its own when something is broken. |
| `/devkit:setup` | Adds devkit to a project and writes guard rules that fit its stack: Prisma, Drizzle, Rails, Django, Alembic, Laravel, golang-migrate, goose, Flyway, Supabase, Knex, plus live-mode switches and rules from your docs. |

**New to coding?** Start with the [beginner's guide](GUIDE.md): what devkit does in plain words, setup from zero, and what to do when guard asks a question.

Nothing here calls an outside service or records usage. The methods are adapted from [garrytan/gstack](https://github.com/garrytan/gstack); see [NOTICE](NOTICE).

## Quick start

**Needs:** [Claude Code](https://docs.claude.com/en/docs/claude-code/overview), `git`, and Python 3.8 or later as `python3` or `python` (macOS gets it with Apple's developer tools, most Linux has it, Windows needs it installed). If Python is missing, Claude Code shows a hook error and commands run without guard's check. New to all this? Read the [beginner's guide](GUIDE.md).

### For yourself, in every project

```sh
claude plugin marketplace add LeMarkk/agent-skills
claude plugin install devkit@lemarkk
```

### For a team, in one repository

Open the repo in Claude Code and ask:

```
/devkit:setup
```

It adds the plugin to `.claude/settings.json`, looks at your stack, proposes a `.claude/guard.json` for you to approve, tests each rule, and offers a short `CLAUDE.md` note. Commit those files and every teammate gets devkit the next time they open the project and trust the folder.

To do it by hand, put this in `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "lemarkk": {
      "source": { "source": "github", "repo": "LeMarkk/agent-skills" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "devkit@lemarkk": true
  }
}
```

The marketplace is named `lemarkk` (the name inside the repo's `marketplace.json`); the repo is `LeMarkk/agent-skills`. Check it loaded with `/plugin` (Installed tab), or ask Claude to run `/devkit:guard status`.

### Starting a new project

Add devkit before the first commit, then run `/devkit:setup` again once the project has migrations or a deploy script. Rules work best when they come from real folders and real commands.

## Project rules

Each project can add rules in `.claude/guard.json`:

```json
{
  "ask":   [{"pattern": "PAYMENTS_LIVE=(true|1)\\b", "reason": "live payment keys only in prod"}],
  "deny":  [{"pattern": "\\bmake\\s+deploy-prod\\b", "reason": "production deploys go through CI"}],
  "allow": [{"pattern": "rm -rf \\./\\.local-cache"}],
  "protect_paths": [{"glob": "db/migrate/*.rb", "reason": "applied migrations never change; add a new one"}]
}
```

`ask` and `deny` are regexes searched in the whole command, `allow` must match the whole command and skips every check, and `protect_paths` makes editing an existing matching file need an OK. Ready-made rules by tool are in the [rule catalog](plugins/devkit/skills/setup/references/rules-catalog.md), and the full format is in [the guard skill](plugins/devkit/skills/guard/SKILL.md#project-rules-claudeguardjson).

## What guard is and isn't

guard reads command text before it runs. It can't see what a script, Makefile target or SQL file does inside, and a person who wants to get around it can. It's a seatbelt against an agent's mistakes, not a security boundary. To turn it off, disable the plugin with `/plugin`; Claude can't do that for you.

## Using your own copy

Fork the repo, change the skills or rules, and point `repo` in the settings above at your fork (`your-name/agent-skills`). Plugins run with your user's permissions, so read a fork's `hooks/` and `scripts/` before installing it.

## Contributing

1. Edit under `plugins/devkit/`. Keep each `SKILL.md` under about 12 KB; put long material in a `references/` file the skill points to.
2. Run the tests: `python3 -m unittest discover -s tests`, and with Claude Code installed, `claude plugin validate .` and `claude plugin validate plugins/devkit`.
3. A new built-in guard rule needs cases in `tests/test_guard.py`: a command it should catch and a near miss it should leave alone. A new catalog rule needs the same in `tests/test_catalog.py`.
4. Bump `version` in `plugins/devkit/.claude-plugin/plugin.json` and open a pull request. Projects with `autoUpdate` pick up merged changes at the start of a later session.

## Roadmap

- **Now:** guard, debug, setup.
- **Next:** code review, test strategy, security audit.
- **Later:** a ship workflow (GitHub and GitLab, ECS, Docker Swarm, plain VPS), a docs check on release, and plan review.

## License

[GPL-3.0](LICENSE).
