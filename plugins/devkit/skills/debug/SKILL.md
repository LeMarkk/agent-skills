---
name: debug
description: Use before changing code to fix any bug, failing or flaky test, error, crash, wrong output, regression, or "works locally but not in staging/prod" — including when the user just says "X fails, fix it". Proves the root cause first, fixes it at the source with a regression test that fails before the fix, stops to escalate after 3 failed hypotheses, and ends with a debug report. Skip only for typos and one-line changes the user has already diagnosed.
---

# debug

**The rule: no fix without a proven root cause.** A fix for a symptom moves the bug somewhere harder to find. Until you can say what is wrong, where, and show the evidence, you are still investigating and you don't edit product code.

Work through the phases in order. Keep a short running log in your replies (hypothesis, test, result) so the person can follow and redirect.

## 1. Understand and reproduce

1. **Symptom.** Get the exact error, stack trace, failing test or wrong output, and what "right" looks like. If something essential is missing, ask one question at a time.
2. **Reproduce.** Find the smallest command that shows the bug every time: a single test (`go test ./internal/x -run TestY`, `npx vitest run path -t name`), a `curl` against the local API, a script. Use the project's own commands from `CLAUDE.md`, the Makefile or `package.json`. If you can't reproduce it, keep collecting evidence; don't guess.
3. **What changed.** `git log --oneline -20 -- <files>` and `git diff <last-good>..HEAD -- <files>`. If it used to work, the cause is almost always in that diff; `git bisect run <repro>` finds it fast when the range is long.
4. **Logs, read-only.** Local: the test output or `docker compose logs <svc>`. Swarm: `docker service logs <svc>`. ECS: `aws logs tail <group> --since 1h`. VPS: `journalctl -u <unit>`. ELK: query by request or trace ID. Never change production data or config while investigating.

## 2. Lock the scope

Once you know the area, lock edits to it so the fix can't sprawl: load the `guard` skill and run its `freeze <folder>` command with the narrowest folder that holds the affected code. Skip this if the bug genuinely spans the repo, and say why. Unlock at the end of the investigation.

## 3. Match known patterns

| Pattern | Signs | Look at |
|---|---|---|
| Race or ordering | Intermittent, depends on timing or test order | Shared state, goroutines, async handlers, test setup and teardown |
| Null or missing value | nil pointer, `undefined`, TypeError | Optional fields, unhandled error returns, early returns |
| Partial update | Inconsistent rows, half-applied changes | Transactions, retries, webhooks processed twice |
| Boundary failure | Timeout, unexpected status or shape | External APIs (payment gateways, auth providers), service-to-service calls |
| Config drift | Works locally, fails in staging or prod | Env vars, secrets, image tag, migrations not applied, feature flags |
| Stale data | Fixed by a restart or cache clear | Caches, CDN, connection pools, build artifacts |
| Money or time math | Off by a cent, a day or a few hours | Floats instead of integer minor units, rounding order, UTC vs local time, end-of-day and end-of-month boundaries |
| Scoping leak | One tenant or merchant sees another's data | Missing tenant or merchant filter, RLS context not set |

Also check `git log` for earlier fixes in the same files: a bug that keeps coming back there is a design problem, not bad luck.

For a test that fails only sometimes, only in CI, or only alongside other tests, read `references/flaky.md` before anything else. Rerunning, raising a timeout or skipping the test is never a fix.

## 4. Test hypotheses, one at a time

1. State it as a claim you can disprove: "**Hypothesis:** `X` returns stale `Y` because `Z` is cached before the migration runs."
2. Run the smallest check that could prove it wrong: a temporary log or assertion, a focused test, a query against the local database. Remove temporary instrumentation afterwards.
3. Record the result. If the evidence doesn't match, drop the hypothesis and form the next one from what you learned.

**Three strikes.** After 3 disproven hypotheses, stop and report to the person with:

```
STATUS: BLOCKED
TRIED: <each hypothesis and the evidence against it>
KNOWN: <what is now ruled out or confirmed>
NEXT: continue with <new hypothesis> | get someone who knows <area> | add logging at <place> and wait for the next occurrence
```

Slow down if you notice yourself saying "quick fix for now", proposing a fix before tracing where the bad value comes from, or each fix revealing a new failure somewhere else. That last one means you're working at the wrong layer.

## 5. Fix at the source

1. **Regression test first.** Write a test that reproduces the bug and run it: it must fail, for the right reason, before the fix.
2. **Fix the cause.** The smallest change that removes the actual problem. When the bug lives in a shared function, fix it there once rather than guarding every caller. Reuse what exists before writing new code: a helper in the repo, then the standard library, then a platform feature, then a dependency already installed. Ask before adding a new dependency.
3. **No side quests.** Don't refactor neighbouring code, rename things or reformat files in the same change. Note follow-ups instead.
4. **Blast radius.** If the fix touches more than 5 files, stop and ask whether to proceed, split it, or look for a narrower fix.
5. The regression test now passes. Run the project's full relevant suite (for example `make test` and `make vet`, or `npm run typecheck && npm run lint && npm test`) and include the result.

Never weaken a test, widen a timeout, add a skip or suppress a lint rule to make the failure go away. If one of those is genuinely the right fix, say so explicitly and get the person's OK.

## 6. Verify and report

Re-run the original reproduction and confirm the bug is gone. Unlock any freeze you set. Then report:

```
DEBUG REPORT
Symptom:      <what was observed>
Root cause:   <what was wrong and why, with file:line>
Evidence:     <what proved it: test output, log line, query result>
Fix:          <what changed, file:line>
Regression:   <test file:line; failed before, passes now>
Checks:       <suite commands run and their result>
Follow-ups:   <related risks or cleanup, if any>
Status:       DONE | DONE_WITH_CONCERNS | BLOCKED
```

Don't commit, push or open a PR unless the person or the project's workflow asks you to; leave the change for review.

## Data care

Logs and databases often hold personal data: names, emails, phone numbers, health or payment details, ID numbers. Quote only the lines you need, mask personal values (`jane.d***@…`, `*** *** 1234`), and never paste secrets or tokens into replies, tests or fixtures. Build test data from the project's seed or fixture files.
