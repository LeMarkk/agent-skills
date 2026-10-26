# agent-skills

Claude Code plugins for any project, in one marketplace:

- **devkit** makes agent work safer: a guard hook against destructive commands, root-cause debugging, and per-project setup.
- **devteam** gives Claude Code a development team: eight role agents, from product manager to DevOps, each loading only the skills its role needs.

## How it works

```
LeMarkk/agent-skills                      marketplace "lemarkk"
├── devkit
│   ├── hook   guard.py                   runs before every shell command and file edit
│   └── skills guard · debug · setup
└── devteam
    ├── skill  team                       the lead, runs in your own session
    ├── agents pm · architect · backend-dev · frontend-dev
    │          qa · reviewer · security · devops
    └── skills interview · spec · tasks · design · decisions · build
               tdd · ui · test-plan · review · security · ship
```

Inside a project, the pieces fit together like this:

```
you ──▶ /devteam:team (lead, your session)
          │  brief: file paths + "done when", never pasted context
          ▼
        role agent (fresh context, preloads its 1–3 skills)
          │  reads and writes docs/work/<feature>/…, code, commits
          │  every command and edit passes the guard hook ──▶ allow · ask you · block
          ▼
        short report (under 150–400 words) ──▶ lead starts the next ready task
```

- **guard** is a `PreToolUse` hook. It reads each command or edit before it runs and blocks the catastrophic, asks you about the risky, and lets everyday work through. A project adds its own rules in `.claude/guard.json`.
- **The lead** (`team` skill) sizes each request: a one-liner goes straight to a developer, a feature goes spec → build → review, and anything risky runs the full loop with your approval at the spec and the task list.
- **Role agents** each run in their own context with only their own skills, so the main session stays small. The reviewer and security agents are read-only.
- **Files are the shared memory.** Specs, tasks, test plans, ADRs and the glossary live in the repo, so any agent, or a new session, picks up from them.
- **Bugs** from any role go to devkit's `debug` skill: root cause first, a failing regression test before the fix.

## How it was built

- **Adapted methods, original writing.** devkit's methods come from [garrytan/gstack](https://github.com/garrytan/gstack). devteam combines the short, composable flows of [mattpocock/skills](https://github.com/mattpocock/skills) (interview rounds, tracer-bullet tasks, two-axis review) with the full-lifecycle coverage of [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) (security, shipping, CI, observability, accessibility), rewritten as one skill per job in one style. No source files are copied; [NOTICE](NOTICE) lists what came from where.
- **Built for low token cost.** devkit skills stay under 12 KB and devteam skills under 6 KB (all 13 together are about 39 KB). Descriptions, which load in every session, are a sentence or two. Each agent preloads only its own skills and reports back briefly.
- **No dependencies, no network.** guard is plain Python 3.8+ standard library and never calls an outside service.
- **Tested.** Unit tests cover every guard rule and catalog rule (with near misses), plus devteam's wiring: names, size budgets, and that every agent preloads skills that exist. CI runs them on Python 3.8 and 3.13. Both plugins pass `claude plugin validate --strict`, and a live session confirmed that all eight agents register and receive their preloaded skills.

## Get started: `/devkit:setup`

Open your project in Claude Code and type:

```
/devkit:setup
```

It wires the plugins into the repository so everyone who opens it gets the same setup:

1. **Enables the plugins** in `.claude/settings.json`: devkit always, devteam if you want the team. Existing settings are kept.
2. **Looks at your stack:** migration folders and tools, reset scripts, generated files, live-mode switches, and rules already written in your docs.
3. **Proposes `.claude/guard.json`** with one line of reason per rule, and waits for your OK.
4. **Tests every rule** against a command it should catch and one it shouldn't.
5. **Offers a short `CLAUDE.md` note** so teammates know how the skills are used.

Commit those files; teammates get the plugins the next time they open the project and trust the folder. Run `/devkit:setup` again once the project gains a database or a deploy script, so the rules can catch up.

Then, to build with the team, type `/devteam:team` and describe what you want.

First time using Claude Code, or don't have the plugins yet? The [beginner's guide](GUIDE.md) covers installing everything from zero. Each teammate needs Python 3.8 or later on their PATH (as `python3` or `python`) for the guard hook.

<details>
<summary>What setup writes to <code>.claude/settings.json</code></summary>

```json
{
  "extraKnownMarketplaces": {
    "lemarkk": {
      "source": { "source": "github", "repo": "LeMarkk/agent-skills" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "devkit@lemarkk": true,
    "devteam@lemarkk": true
  }
}
```

The marketplace is named `lemarkk` (the name in the repo's `marketplace.json`); the repo is `LeMarkk/agent-skills`.
</details>

## devkit

| Part | What it does |
|---|---|
| **guard** hook | Runs before every shell command and file edit. Blocks the catastrophic (recursive delete of `/` or `~`, force-push to `main`, writing to a raw disk) and asks before the risky (other recursive deletes, `git reset --hard`, SQL `DROP`/`TRUNCATE`, Docker prunes and `stack rm`, `terraform destroy`, AWS/OCI deletes, `curl \| sh`). Never auto-approves. |
| `/devkit:guard` | Explains a stopped command, locks edits to one folder (`freeze`), shows status, tests a command with `check`. |
| `/devkit:debug` | Root cause before any fix: reproduce, lock scope, test one hypothesis at a time, stop after 3 misses, write a regression test that fails first, then report. Claude also uses it on its own when something is broken. |
| `/devkit:setup` | Adds the plugins to a project and writes guard rules that fit its stack: Prisma, Drizzle, Rails, Django, Alembic, Laravel, golang-migrate, goose, Flyway, Supabase, Knex, plus live-mode switches and rules from your docs. |

### Project rules

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

### What guard is and isn't

guard reads command text before it runs. It can't see what a script, Makefile target or SQL file does inside, and a person who wants to get around it can. It's a seatbelt against an agent's mistakes, not a security boundary. To turn it off, disable the plugin with `/plugin`; Claude can't do that for you.

## devteam

| Agent | Skills it preloads | Job |
|---|---|---|
| `devteam:pm` | interview, spec, tasks | Find out what to build, write the spec, slice it into tasks |
| `devteam:architect` | design, decisions, tasks | Module and API shape, ADRs, glossary |
| `devteam:backend-dev` | build, tdd | Server, data, APIs, jobs |
| `devteam:frontend-dev` | build, tdd, ui | Screens, components, client state |
| `devteam:qa` | test-plan, tdd | Map acceptance criteria to tests, fill gaps, run the flows |
| `devteam:reviewer` | review | Standards and spec review before merge (read-only) |
| `devteam:security` | security | Threat model and hardening review (read-only) |
| `devteam:devops` | ship | CI gates, release, rollback, observability, the PR |

The full loop, for features that need it:

```
pm: interview → spec (you approve) → architect: design → tasks (you approve)
  → backend-dev / frontend-dev, task by task → qa → reviewer (+ security) → devops: ship
```

What the team writes:

```
docs/work/<feature>/spec.md        what and why, success criteria, test seams, boundaries
docs/work/<feature>/tasks/NN-*.md  one task per file, with owner, blockers and "done when"
docs/work/<feature>/test-plan.md   acceptance criteria mapped to tests
docs/work/<feature>/handoff.md     where things stand, for the next session
docs/adr/NNNN-*.md                 hard-to-reverse decisions
GLOSSARY.md                        the project's terms
```

Routine roles run on Sonnet; the architect, reviewer and security agents use your session's model.

## Using your own copy

Fork the repo, change the skills or rules, and point `repo` in the settings above at your fork (`your-name/agent-skills`). Plugins run with your user's permissions, so read a fork's `hooks/` and `scripts/` before installing it.

## Contributing

1. Edit under `plugins/devkit/` or `plugins/devteam/`. Keep each `SKILL.md` under 12 KB (devteam's under 6 KB); put long material in a `references/` file the skill points to.
2. Run the tests: `python3 -m unittest discover -s tests`, and with Claude Code installed, `claude plugin validate .`, `claude plugin validate plugins/devkit` and `claude plugin validate plugins/devteam`.
3. A new built-in guard rule needs cases in `tests/test_guard.py`: a command it should catch and a near miss it should leave alone. A new catalog rule needs the same in `tests/test_catalog.py`.
4. Bump `version` in the plugin's `.claude-plugin/plugin.json` and open a pull request. Projects with `autoUpdate` pick up merged changes at the start of a later session.

## Roadmap

- **Now:** devkit (guard, debug, setup) and devteam (eight role agents and their skills).
- **Next:** platform-specific ship recipes (GitHub and GitLab, ECS, Docker Swarm, plain VPS) and a docs check on release.
- **Later:** plan review and evals for the devteam agents.

## License

[MIT](LICENSE). Versions published before this change remain available under GPL-3.0.
