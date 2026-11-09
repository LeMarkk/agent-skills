---
name: review
description: Review a change before merge on two separate axes, standards (repo rules, correctness, readability, design, performance) and spec (does it do what was asked), with labeled severities. Use to review a branch, PR or diff, or when asked to "review since X".
---

# review

Review the diff, not the whole codebase. Report findings; don't fix them. Keep the two axes apart so a change that's well written but wrong (or right but messy) can't hide behind the other axis.

## 1. Pin the change

Get the base: a branch, commit or `main`. Check it resolves (`git rev-parse <base>`) and the diff isn't empty, then read `git log <base>..HEAD --oneline` and `git diff <base>...HEAD`.

Read the tests first: they tell you what the author thinks the change does.

## 2. Find the spec and the standards

- **Spec:** the task file and `docs/work/<feature>/spec.md`, an issue linked in the commits, or ask. If there's no spec, say so and skip that axis.
- **Standards:** `CLAUDE.md`, `CONTRIBUTING.md`, `CODING_STANDARDS.md`, lint config, ADRs for the touched area, the glossary.

## 3. Standards axis

Check, in this order:

1. **Correctness:** logic errors, off-by-one, null and empty cases, error paths, race conditions, transactions that can half-apply.
2. **Repo rules:** anything the standards files say. A documented rule beats the defaults below.
3. **Readability:** names that say what things are, straightforward flow, no dead or commented-out code.
4. **Design:** right module for the change, no new shallow wrappers, no abstraction the spec doesn't need, no duplicated logic.
5. **Performance:** N+1 queries, unbounded loops or result sets, work in hot paths that could be done once.
6. **Tests:** they test behavior at the seam, would fail if the code broke, and cover the error cases.

Useful smells to name (always as judgment calls): unclear name, duplicated code, a function more interested in another module's data, the same few parameters always travelling together, a string standing in for a domain type, the same switch repeated, one change scattered across many files, speculative options, a wrapper that only passes calls through.

Skip what lint or formatters already enforce.

## 4. Spec axis

- Requirements that are **missing or partial**, quoting the spec line
- Behavior **nobody asked for** (scope creep)
- Requirements that look done but are **done wrong**

## 5. Verify the verification

Run the tests yourself. Check that the commands the author reported actually pass, and that a test for the main behavior exists and can fail.

## Report

```markdown
## Standards
- **Critical** `path:line`: <issue> → <suggested fix>
- **Should fix** ...
- **Nit** ...

## Spec
- **Missing** (story 4: "<quote>"): ...
- **Not asked for**: ...

Summary: <n> standards findings (worst: ...), <n> spec findings (worst: ...). Tests: <command> → <result>.

VERDICT: APPROVE | CHANGES REQUESTED @ <full commit sha>
```

Severities: **Critical** blocks merge (wrong behavior, data loss, security hole). **Should fix** before merge unless the author has a reason. **Nit** is optional. Don't rank across the two axes. Under 400 words; if there are more findings than that, list the most serious and say how many you left out.

If you spot a security issue, flag it as Critical and recommend a `security` review.

## When the project delegates merging

Some projects let agents merge without a person reading the diff. Only do this when the project's `CLAUDE.md` says so and names who merges. The gate is all of:

1. Every reviewer the project names gives `APPROVE` or `PASS` **at the same commit sha**. A new commit, even a one-line fix, voids every verdict; review again.
2. No Critical finding is open, and no Should fix finding is waved through without a written reason.
3. CI is green on that sha.
4. A review record exists (the project names the path, e.g. `docs/reviews/<ticket>.md`) with each verdict, its sha and the CI run, committed with the merge.

Then merge without force, never with `--admin` or any switch that skips branch protection. A person still owns production deploys and anything else the project lists as human-only. Stop and hand to a person instead of merging when the change rewrites a recorded decision (ADR), deletes or rewrites data, or the same change has failed the gate three times.
