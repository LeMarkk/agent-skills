---
name: safe-rename
description: Rename a symbol, file, folder, route or config key across a codebase without missing a reference or changing behavior. Finds every use first (code, tests, strings, config, docs), changes them all, then proves it with the type check, lint and tests. Use for any rename or move, especially when a cheaper model does it.
---

# safe-rename

A rename is done when nothing still uses the old name and nothing behaves differently. Most broken renames miss a string, a config file or a test, so find everything before changing anything.

## 1. Refuse the renames that aren't mechanical

Stop and hand back, unless the request names it explicitly and accepts the consequence:

- a **database** table, column, enum value or index (needs a migration and, for live data, an expand/contract plan)
- a **public API**: an HTTP route or field, an event or webhook name, a package export other repos import, a CLI flag
- anything **persisted or external**: environment variable names in deployed environments, feature-flag keys, analytics event names, storage keys, Jira-visible names
- a name inside **generated** files (regenerate from the source instead)

## 2. Find every reference

Search for the old name in all its forms before editing:

- exact identifier, with word boundaries (`\bOldName\b`)
- case variants: `oldName`, `OldName`, `old_name`, `OLD_NAME`, `old-name`
- file and import paths, including barrel files and re-exports
- strings: route paths, i18n keys, test names, mocks, snapshots, log event names
- config: tsconfig paths, bundler aliases, CI workflows, Docker and compose files, `.env.example`
- docs and comments: README, ADRs, `CLAUDE.md`

Ignore dependency and build folders (`node_modules`, `.next`, `dist`, `vendor`, `target`, `coverage`). List what you found, grouped by file, before changing anything. If a hit is ambiguous (the same word meaning something else), leave it and say so.

## 3. Change it

- Prefer the language's own rename (an IDE or language-server rename, `gopls rename`, `ts-morph`) over text replacement for code symbols. Use text replacement only for strings, config and docs.
- Move files with `git mv` so history follows.
- One rename per commit, message `Rename <old> to <new>`, no other changes mixed in.

## 4. Prove nothing changed

- Search again: the old name returns zero hits outside the intended exceptions you listed.
- Run the project's type check, lint and unit tests, plus integration tests if the renamed code touches the database. All pass, with no new suppressions, skipped tests or edited expectations.
- If a snapshot changed, the only difference is the name.

## Report

The rename, the files changed with counts, intentional leftovers and why, and the commands run with results.
