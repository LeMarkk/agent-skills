---
name: test-plan
description: Plan and check testing for a feature: map each acceptance criterion to a test at the right level, find gaps, write the missing tests, and run end-to-end checks of the main flows. Use when a feature needs a test strategy or before review.
---

# test-plan

Your job is confidence that the feature does what the spec says, and that it keeps doing it. More tests isn't the goal; the right tests are.

## 1. Map criteria to tests

Read the spec's user stories, success criteria and test seams, and the task files' "Done when" lists. Build a table in `docs/work/<feature>/test-plan.md`:

```markdown
| Story / criterion | Level | Test | Status |
|---|---|---|---|
| 3. Refund over total is rejected | API | `refunds.test.ts › rejects over-refund` | passing |
| 5. Admin sees refund history | e2e | — | missing |
```

## 2. Choose the level

- **Unit:** pure logic with many cases (pricing, parsing, permissions rules). Fast, many.
- **Integration / API:** a module or endpoint with its real database or a local double. Most feature behavior belongs here.
- **End-to-end:** a few critical user flows through the real UI (sign up, checkout, the feature's main path). Slow, so few.

Push each check down to the lowest level that can catch the bug. Use end-to-end only for what only end-to-end can catch: wiring, routing, the UI and API agreeing.

## 3. Look for gaps

For each story, check the cases teams usually forget:

- Empty input, maximum size, unusual characters, wrong types
- Missing or expired auth, the wrong user's data, a role without permission
- The external service failing, timing out, or answering twice
- Concurrent edits, double submits, retries
- Time: time zones, daylight saving, month and year ends

Add a row for each case that matters. Mark the ones you deliberately won't test and why.

## 4. Write the missing tests

Write them with the `tdd` skill's rules: at the agreed seam, expected values from the spec, deterministic. A new test that passes immediately for behavior that should already work is fine; confirm it can fail by breaking the code briefly.

## 5. Run the flows

Run the full suite and the end-to-end flows. In a web app, also walk the main path in a real browser when a browser tool is available, and check the console.

Flaky test? Don't retry until it passes. Treat it as a bug: use the devkit `debug` skill if installed.

## Report

Update the table's Status column, then report in under 200 words: criteria covered, gaps left and why, any failing or flaky tests with the command to reproduce them.
