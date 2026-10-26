---
name: build
description: Implement a task in thin, verified increments: read the task and spec, change one thing at a time, keep the build green, test at the agreed seam, commit, and report. Use for any feature work or change beyond a one-liner.
---

# build

Deliver the task completely and nothing more, in small steps that each leave the code working.

## Before you start

1. Read the task file, the spec sections it points to, and any ADRs for the area. Use the glossary's words in names.
2. Find the project's own commands for tests, lint, types and build (`CLAUDE.md`, `package.json`, `Makefile`, `pyproject.toml`). Use those, not guesses.
3. Run the relevant tests once before changing anything, so you know what was already failing.
4. Set the task's `Status:` to `in progress`.

## The loop

Repeat until the task's "Done when" list is all checked:

1. **Pick the next smallest piece** that moves a criterion forward.
2. **Write the test first** at the agreed seam (see the `tdd` skill), watch it fail for the right reason.
3. **Write the least code** that makes it pass.
4. **Run** the focused tests, then lint and type checks. Fix anything you broke before moving on.
5. **Commit** with a message that says what behavior now works: `search: filter results by date range`.

## Rules

- **Simplest thing that works.** No abstraction, option or hook the task doesn't need. Three similar lines beat a premature helper.
- **Stay in scope.** If you notice something else worth fixing, write it down in your report; don't fix it now. Unrelated changes make review harder and hide bugs.
- **Keep it compiling.** Never leave the branch in a state where the build or existing tests fail between commits.
- **Unfinished features stay off.** If a slice is user-visible but incomplete, put it behind a flag or keep it unreachable.
- **Safe defaults.** New config defaults to the old behavior; new permissions default to denied.
- **Easy to roll back.** Database changes are additive in this task (new columns nullable, old ones kept). Removing things is a separate, later task.
- **Ask, don't guess.** If the task or spec is ambiguous in a way that changes behavior, stop and report the question instead of picking an answer.

## Bugs

If something breaks and the cause isn't obvious within a couple of minutes, stop patching. Use the devkit `debug` skill if it's installed: reproduce, prove the root cause, write a failing regression test, then fix.

## Finish

Before reporting done, check:

- [ ] Every "Done when" item is met
- [ ] Full test suite, lint, type check and build pass
- [ ] No debug prints, commented-out code or TODOs you added
- [ ] Work is committed; nothing left unstaged

Set `Status:` to `done` (or `blocked: <reason>`), then report in under 150 words: status, what changed, the test command you ran and its result, anything you noticed but left alone.
