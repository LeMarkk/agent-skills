# agent-skills

Shared Claude Code skills and hooks for John Mark's projects: Chariot and PosMoTo. One place to improve them, picked up by every project that enables the plugin.

The repo is a Claude Code plugin **marketplace** (`.claude-plugin/marketplace.json`) holding one plugin, **devkit**.

| Part | What it does |
|---|---|
| `guard` hook | Runs before every shell command and file edit. Blocks the catastrophic (recursive delete of `/` or `~`, force-push to `main`, writing to a raw disk) and asks before the risky (other recursive deletes, `git reset --hard`, SQL `DROP`/`TRUNCATE`, Docker prunes and `stack rm`, `terraform destroy`, AWS/OCI deletes, `curl \| sh`). Never auto-approves. |
| `/devkit:guard` | Explains a stopped command, locks edits to one folder (`freeze`), shows status, tests a command with `check`. |
| `/devkit:debug` | Root cause before any fix: reproduce, lock scope, test one hypothesis at a time, stop after 3 misses, regression test that fails first, report. Claude also picks it up on its own when something is broken. |

Methods are adapted from [garrytan/gstack](https://github.com/garrytan/gstack); see [NOTICE](NOTICE). Nothing here calls an outside service or records usage.

## Use it in a project

Add this to the project's `.claude/settings.json` and commit it:

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

The next time someone opens the project in Claude Code and trusts the folder, the marketplace is added and devkit is enabled. Each person needs read access to this GitHub repo while it's private.

To use it everywhere on your own machine instead (including sessions started in `~/Work`):

```sh
claude plugin marketplace add LeMarkk/agent-skills
claude plugin install devkit@agent-skills
```

Check it loaded with `/plugin` (Installed tab) or by asking Claude to run `/devkit:guard status`.

**Needs:** `git` and Python 3.10+ as `python3` on the PATH (standard on macOS and Linux; on Windows install Python and make sure `python3` resolves). If `python3` is missing, Claude Code shows a hook error and the command runs without guard's check.

## Project rules for guard

A project can add its own rules in `.claude/guard.json`: extra `ask`/`deny` regexes, narrow `allow` exceptions, and `protect_paths` globs whose existing files need an OK before they're edited (for applied migrations). The format is in [the guard skill](plugins/devkit/skills/guard/SKILL.md#project-rules-claudeguardjson).

## Changing a skill

1. Edit under `plugins/devkit/`. Keep each `SKILL.md` under about 12 KB; put long material in a `references/` file the skill points to.
2. Run the tests: `python3 -m unittest discover -s tests` and, with Claude Code installed, `claude plugin validate .` and `claude plugin validate plugins/devkit`.
3. Bump `version` in `plugins/devkit/.claude-plugin/plugin.json`.
4. Open a PR. Once merged, projects with `autoUpdate` pick it up at the start of a later session.

A new guard rule needs a case in `tests/test_guard.py`, both a command it should catch and a near-miss it should leave alone.

## Roadmap

From the [upgrade plan](https://claude.ai/artifact/AZhD9QjnGMuvsrMKKZGHf3):

- **Phase 1 (this release):** guard, debug.
- **Phase 2:** code-review, testing-strategy, security-audit.
- **Phase 3:** ship (GitLab/GitHub, ECS, Swarm via Portainer, VPS), documentation release check, plan review, and light updates to standup, incident-response and tech-debt.
