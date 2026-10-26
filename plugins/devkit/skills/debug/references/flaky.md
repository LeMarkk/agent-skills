# Flaky, CI-only and order-dependent failures

Read this before rerunning, retrying, raising a timeout or skipping anything. A green rerun proves nothing about the cause.

## 1. Measure it

- Run the single test many times locally: `go test ./pkg -run TestX -count=50 -race`, or `for i in $(seq 30); do npx vitest run path -t "name" || break; done`.
- Note the failure rate and whether the error is always the same. Same error every time points at one cause; different errors point at shared state.
- In CI, compare the failing job's environment with local: runtime version, database image, timezone, CPU count, parallelism, and env vars.

## 2. Order-dependent (passes alone, fails in the suite)

- Run the failing test alone, then with the file it shares, then the whole package or project, to find the smallest set that fails.
- Bisect the set: split the tests that run before it in half until one "polluter" test is left.
- Look for what the polluter leaves behind: rows in a shared database, a global or module-level variable, an env var, a mocked clock or fetch that isn't restored, a file in a fixed temp path, a server port.
- Fix the leak at its source (clean up in the polluter, or isolate state per test), not by reordering tests.

## 3. Timing and races

- Go: run with `-race`; a reported race is a real bug even when the test passes.
- Look for: unawaited promises, goroutines outliving the test, `sleep`-based waits, assumptions that two requests or webhooks arrive in order, retries that run twice, clocks read in two places.
- Prove the race by forcing the bad order (a channel, a barrier, a delayed mock) so the test fails every time, then fix and keep that test.
- Replace sleeps with waiting on the actual condition (an event, a row appearing, a health check).

## 4. CI-only

- Reproduce CI locally as closely as possible: the same container image, `TZ=UTC`, a clean database built from migrations, `CI=true`.
- Check for things CI lacks: a local `.env`, a seeded database, a cached build, network access to an outside API.
- If it can't be reproduced, add focused logging around the failure and report `BLOCKED` with what you saw, rather than retrying until it passes.

## 5. Done means

The test fails reliably before the fix (forced order, `-count`, or the polluter in place) and passes reliably after it, with the same run count.
