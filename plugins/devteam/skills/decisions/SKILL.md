---
name: decisions
description: Record architecture decisions as short ADRs in docs/adr/ and keep the project's terms in GLOSSARY.md. Use when a hard-to-reverse choice is made, when terms are ambiguous, or before changing code an ADR covers.
---

# decisions

Two small files keep a project understandable to the next person or agent: ADRs say *why* it's built this way, and the glossary says what the words mean.

## When an ADR is worth writing

Write one only when all three are true:

1. **Hard to reverse:** changing your mind later costs real time or data.
2. **Surprising without context:** a future reader would ask "why did they do it this way?"
3. **A real trade-off:** there were genuine alternatives and this one won for stated reasons.

Picking a database, an auth provider, sync vs async processing, a multi-tenant data model: yes. Naming a folder or choosing a lint rule: no.

## ADR format

Create `docs/adr/` when the first ADR is needed. Number files in order: `docs/adr/0003-queue-emails-instead-of-sending-inline.md`.

```markdown
# 0003: Queue emails instead of sending them inline

Status: accepted (2026-10-27)

## Context
What forced the decision: the constraint, the problem, the numbers.

## Decision
What we chose, in one or two sentences.

## Alternatives
- <option>: why not
- <option>: why not

## Consequences
What gets easier, what gets harder, what we now have to look after.
```

Keep it under a page. ADRs are never edited after they're accepted, except the status line. To change course, write a new ADR and mark the old one `superseded by 0007`.

Before changing code in an area, check `docs/adr/` for decisions that cover it. If your change goes against one, say so and ask before proceeding.

## Glossary

`GLOSSARY.md` at the repo root holds the project's domain terms, created when the first term is settled:

```markdown
**Order:** a customer's confirmed purchase of one or more items. Not a cart (unconfirmed).
**Refund:** money returned against an Order, full or partial. See also: Credit note.
```

- One line per term: what it is, and what it's easily confused with.
- Update it the moment a term is settled, not at the end.
- No implementation detail. It's a glossary, not a spec.
- When someone uses a term in a way that conflicts with the glossary, point it out and ask which meaning is right.
- Use the glossary's words in specs, tasks, tests, code names and PRs.
