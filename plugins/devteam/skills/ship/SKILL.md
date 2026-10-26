---
name: ship
description: Get a change safely to production: CI quality gates, a pre-release checklist, rollback plan, logs, metrics and alerts for the new behavior, and a PR that shows evidence and merge risk. Use when setting up CI, preparing a release, or opening a PR.
---

# ship

A change is shipped when it's in production, you can see it working, and you can undo it.

## CI gates

Every pull request and push to the main branch runs, in this order, and any failure blocks the merge:

1. Install from the lockfile (`npm ci`, `pip install -r` with hashes, `composer install`)
2. Lint and format check
3. Type check, if the stack has one
4. Tests, with a real database or service container where the tests need one
5. Build
6. Dependency audit, failing on critical or high

Keep the pipeline under about ten minutes: cache dependencies, run independent jobs in parallel. Secrets live in the CI's secret store, never in the workflow file. When CI fails, read the log, reproduce locally, and fix the cause; don't re-run hoping it passes.

## Before release

- [ ] CI green on the exact commit being released
- [ ] Review done; security review done if the change handles input, auth, money, files or personal data
- [ ] Database migrations are backward compatible: the old code still runs against the new schema
- [ ] New environment variables and secrets exist in every target environment
- [ ] Feature flag in place for anything user-visible and risky, defaulting off
- [ ] Health check endpoint responds
- [ ] README, API docs and changelog updated

## Rollback

Write the rollback before deploying, in one or two commands: redeploy the previous image or tag, turn the flag off, or run the down migration. If the change can't be rolled back (a destructive migration, a sent email, a published API), say so explicitly and get the user's go-ahead.

Deploy where you can watch: staging first, then production, gradually if the platform supports it (canary, percentage rollout). Watch error rate and latency for the first minutes before going wider.

## See it working

For each new endpoint, job or external call:

- **Logs:** structured (JSON), stable event names, a request or correlation ID, no secrets or personal data.
- **Metrics:** request rate, error rate and latency (as a histogram, so p95 and p99 are visible).
- **Alerts:** on symptoms users feel (error rate, latency, queue age), each with a short runbook line. Test-fire a new alert once.

Before calling it done, ask: if this broke at 2 a.m., could someone find out what happened from the telemetry alone?

## The PR

```markdown
## Summary
<the smallest picture of the change: a call tree, a file tree, a diff of the shape, or a short sequence diagram>

## Evidence
Before: <failing test, error, screenshot>
After: <passing test run, output, screenshot>

## Risk
Door: one-way | two-way (can we undo it cheaply?)
Blast radius: <who or what is affected if it's wrong>
Rollback: <the command or step>
```

Keep it short and use the project's terms. Link the spec and tasks instead of repeating them.
