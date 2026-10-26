---
name: design
description: Design modules and interfaces before building: deep modules behind small interfaces, seams placed where behavior varies, contract-first APIs with consistent errors and additive changes. Use when shaping a new module, API or schema, or restructuring existing code.
---

# design

Good design here means: a lot of behavior behind a small interface, at a clean seam, testable through that interface. Callers get leverage, maintainers get one place to change.

## Words we use

- **Module:** anything with an interface and an implementation: a function, a class, a package, a service.
- **Interface:** everything a caller must know to use it correctly: the signature, plus invariants, ordering, error modes, config and performance limits.
- **Deep module:** a small interface hiding a lot of behavior. **Shallow:** the interface is almost as complex as what's behind it. Avoid shallow modules.
- **Seam:** the place where a module's interface lives, where you can swap behavior without editing the callers. Tests live at seams.
- **Adapter:** a concrete thing that fills a seam (a Postgres repository, an in-memory fake).

## Shaping a module

1. **Start from the callers.** Write the two or three calls a caller will make, before the implementation. If the calls are awkward, the interface is wrong.
2. **Shrink the interface.** Fewer methods, fewer parameters, sensible defaults. Hide ordering rules inside ("call `init` before `save`" is a leak).
3. **Deletion test.** Imagine deleting the module. If complexity disappears, it was a pass-through; inline it. If complexity reappears in every caller, it earns its place.
4. **Seams only where something varies.** One adapter is a hypothetical seam; two (real and fake, or two providers) is a real one. Don't add an interface for a single implementation.
5. **Dependencies in, results out.** Accept collaborators as parameters instead of constructing them; return values instead of mutating inputs. Both make the module testable at its seam.

For a big or contested interface, sketch two or three very different designs side by side and compare them on interface size, what changes together, and where tests would sit. Then pick one.

## APIs and contracts

- **Contract first.** Define request and response types, and error cases, before handlers. Commit the types or schema with the code.
- **One error shape** across every endpoint: a stable machine-readable code, a human message, and field details for validation errors. Never leak stack traces or SQL.
- **Validate at the boundary.** Parse and check external input once, where it enters. Inside, trust the types.
- **Add, don't change.** New fields are optional; never repurpose or remove one in place. Assume every observable behavior has a user who depends on it.
- **Lists paginate** from day one, with a stable sort.
- **Retries are safe.** State-changing endpoints either accept an idempotency key (claimed atomically, and a reused key with a different payload fails loudly) or are documented as not safe to retry.
- **Predictable names:** one convention for paths, fields and casing, used everywhere.

## Output

Write the decisions into the spec's **Decisions** section: modules, their interfaces in prose or types, seams, and the data shape. If a choice is hard to reverse and a real trade-off, also record it with the `decisions` skill. Keep code sketches to what encodes the decision (a type, a schema, a state machine), not a working implementation.
