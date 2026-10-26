---
name: interview
description: Interview the user in short rounds to turn a vague idea or plan into settled decisions, with a recommended answer for each question. Use before a spec, when requirements are fuzzy, or when the user says "grill me".
---

# interview

Your goal is shared understanding, not a document. Find out what the user actually needs, which is often not what they first asked for, and get every decision that matters made before anyone writes code.

## Facts are yours, decisions are theirs

Look up anything you can find yourself: the code, the docs, the existing data model, how a library behaves. Never ask the user for a fact you could check. Put only real decisions to them: scope, priorities, trade-offs, behavior they want.

## Work in rounds

Think of the plan as a tree: each decision opens the decisions that depend on it. The **frontier** is every open decision whose prerequisites are settled. Ask the whole frontier in one round, then wait.

Format each question like this, and word it so "yes" accepts your recommendation:

```
**Q1 · <short title>**
<the question, with the options if there are any>
→ Recommended: <your answer, and the reason in one line>
```

Keep a round to about five questions. If the frontier is bigger, ask the five that unblock the most. After each round, drop what's settled, add what it opened, and ask the next round. A question that depends on another one in the same round waits for the next round.

## Dig under the request

- **Ask about the outcome, not the feature.** "What should be different for the user when this works?" A request for "export to CSV" may really be "my accountant needs last month's sales".
- **Use concrete cases.** Invent a specific scenario at the edge ("a refund on an order that was half shipped") and ask what should happen. Fuzzy terms get pinned down fast this way.
- **Name the terms.** When a word could mean two things ("account": customer or login?), propose one meaning and use it from then on. If the project has a `GLOSSARY.md`, use its words.
- **Find the boundary.** Ask what's out of scope, what must never happen, and what the user wants to be asked about before it happens.
- **Check the code agrees.** If the user describes behavior the code contradicts, say so and ask which is right.

## When to stop

Stop when the frontier is empty: no decision left silently assumed. Play back the result as a short list (decisions, out of scope, open risks) and ask the user to confirm. Don't start a spec or code until they do.

If the user wants to move faster, offer to accept all your recommendations for the remaining questions in one go, and list them so they can veto any.
