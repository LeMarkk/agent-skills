---
name: spec
description: Write a feature or project spec to docs/work/<feature>/spec.md from an interview or the conversation: problem, user stories, success criteria, test seams, boundaries. Use before building anything that touches more than a few files.
---

# spec

A spec is the contract between the user and the team: what we're building, why, and how we'll know it's done. Write it from what's already settled. If a decision that matters is still open, run the `interview` skill first, or list it under Open questions; don't invent an answer.

## Before writing

1. Read the parts of the codebase the feature touches, the project's `CLAUDE.md`, `GLOSSARY.md` and any ADRs in that area. Use the project's own words.
2. **Scope check.** If the request bundles several capabilities that could ship and be tested separately (accounts, billing, notifications), propose splitting it: one spec per capability, plus a one-line build order. Ask before continuing.
3. **Pick the test seams.** A seam is the public boundary where tests observe behavior: an HTTP endpoint, a module's exported function, a screen. Prefer existing seams and as few as possible, as high up as possible. Confirm them with the user.

## Template

Save to `docs/work/<feature-slug>/spec.md`:

```markdown
# <Feature name>

## Problem
What the user faces today, in their words.

## Solution
What changes for the user. No implementation detail.

## User stories
1. As a <who>, I want <what>, so that <why>.
(Cover the main path, edge cases, errors and permissions. Number them; tasks refer to them.)

## Success criteria
- Specific and testable: "Search returns results in under 300 ms for 10k items", not "search is fast".

## Decisions
Modules to add or change, interfaces, schema changes, API contracts, choices made and why.
No file paths or code: they go stale. (A schema or type shape that encodes a decision is fine.)

## Test seams
Each seam, what it catches, what it misses, and similar tests already in the repo.

## Boundaries
- Always: <what agents always do here, e.g. run migrations through the tool>
- Ask first: <e.g. new dependencies, schema changes on existing tables>
- Never: <e.g. touch the payments module, log card data>

## Out of scope
## Open questions
```

Add sections only when the feature needs them: commands to run, project structure, or code style for a new project.

## After writing

Show the user the spec's path and a five-line summary, then stop and wait for approval in their next message. Don't write tasks or code in the same turn.

When decisions change later, update the spec first, then the work. A spec that drifts from the code is worse than none.
