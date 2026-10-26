---
name: tasks
description: Break an approved spec or plan into thin end-to-end tasks with blockers and acceptance criteria, one file per task under docs/work/<feature>/tasks/. Use after a spec is approved and before any build starts.
---

# tasks

Turn a spec into a task graph that agents can pick up one at a time, each with a fresh context.

## Slice vertically

Each task is a **tracer bullet**: a narrow path through every layer it needs (schema, API, UI, tests), so it can be demonstrated or verified on its own. "User can filter search by date" is a task. "Write all the database code" is not.

- **Size:** one task fits in one agent session, usually 1–5 files. If it needs more than about 8 files, split it.
- **Prefactor first.** If the code needs reshaping to make the feature easy, that reshaping is its own task, and it comes first.
- **Risk first.** Put the slice that proves the riskiest assumption early, so a bad assumption costs one task, not ten.
- **Wide refactors** (renaming a column used everywhere) can't be a single green slice. Do them as expand → migrate → contract: add the new form next to the old, move callers over in batches (one task each), then remove the old form once nothing uses it.

## Blockers, not order

Give each task the tasks that must finish before it can start. A task with no blockers can start now. Tasks without a blocking edge between them can run in parallel, so only add an edge when one task really needs the other's result.

## Task file

Write one file per task: `docs/work/<feature>/tasks/NN-<slug>.md`, numbered in dependency order.

```markdown
# NN: <Title>

**Owner:** backend-dev | frontend-dev | qa | devops
**Blocked by:** <NN, NN> or none
**Stories:** <spec user story numbers>
**Status:** ready

## What to build
The behavior this task makes work, from the user's side.

## Done when
- [ ] <testable condition>
- [ ] Tests at the agreed seam pass: `<the repo's focused test command>`
- [ ] Build and lint pass
```

No file paths or code snippets in the task: the implementing agent finds those.

## Check with the user

Before writing files, show the breakdown as a numbered list: title, owner, blockers, what it delivers. Ask:

- Is the granularity right?
- Does each blocker really gate its task?
- Should anything be merged or split?

Write the files once the user approves. If the project uses GitHub Issues and the user wants them there, create one issue per task in dependency order with `gh issue create`, and record the issue number in each task file.

## Status

Agents update `Status:` as they work: `ready` → `in progress` → `done` (or `blocked: <reason>`). The lead reads the folder to find the frontier: tasks that are `ready` and whose blockers are `done`.
