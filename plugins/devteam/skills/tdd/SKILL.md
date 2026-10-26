---
name: tdd
description: Test-driven development through public seams: one failing test, the least code to pass it, repeat. Covers what makes a test worth keeping and the anti-patterns to avoid. Use when building features or fixing bugs test-first.
---

# tdd

Red, then green, one slice at a time. The tests you end up with should describe what the system does, and keep passing when its insides change.

## Test at the seam

A test exercises behavior through a public interface: an endpoint, an exported function, a rendered screen. It never reaches inside.

- Agree the seams before writing tests. They're in the spec's **Test seams** section; if they aren't, propose them (what each catches, what it misses) and confirm.
- Prefer one high seam that covers a whole flow over many low ones.
- Name tests as behavior: `refund over the order total is rejected`, not `test_validate_2`.

## The loop

1. **Red.** Write one test for the next small behavior. Run it. It must fail, and fail for the reason you expect (an assertion, not a typo or import error).
2. **Green.** Write the least code that makes it pass. Don't build ahead for the next test.
3. **Repeat** with the next behavior. Each test should respond to what the last one taught you.

Refactoring is a separate step after a slice is green, not part of the red-green cycle. Keep tests passing while you do it.

For a bug: first write a test that reproduces it and fails. Then fix. The test stays as the regression guard.

## What makes a good test

- **Expected values come from outside the code:** a literal, a worked example, the spec. Never recompute the answer the way the code does (`expect(add(a, b)).toBe(a + b)` can't fail).
- **One behavior per test**, with a clear arrange, act, assert.
- **Deterministic.** Control time, randomness and network. A test that sometimes fails is a bug in the test or the code; find out which.
- **Fast enough to run on every change.** Keep slow end-to-end tests few and focused on the main paths.
- **Real collaborators when cheap.** Use an in-memory database or a local service over a mock where you can. Mock only at system edges you don't own (payment provider, email, clock).

## Anti-patterns

- **Testing the implementation:** mocking internal collaborators, testing private functions, checking the database directly instead of reading back through the interface. The sign: the test breaks on a refactor that didn't change behavior.
- **All tests first, then all code.** You end up testing the shape you imagined, not the behavior you needed. Go one test at a time.
- **Tests that pass by construction:** snapshots nobody checked, assertions that mirror the code, catch-all mocks.
- **Weakening a test to make it pass.** If a test is wrong, fix it on purpose and say why in the commit.
