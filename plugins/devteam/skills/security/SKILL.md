---
name: security
description: Threat-model and review a change for exploitable security issues: input handling, auth and access control, secrets, data exposure, dependencies, SSRF, uploads and LLM features, with fixes ranked by real risk. Use before shipping anything that handles input, auth, money, files or personal data.
---

# security

Find the issues an attacker could actually use, explain how, and say what to change. Practical over theoretical: a reachable injection beats a missing header.

## 1. Threat model the change

List what the change exposes: endpoints, forms, file inputs, webhooks, background jobs, new data stored. For each, ask:

| Threat | Question |
|---|---|
| Spoofing | Can someone act as another user or service? |
| Tampering | Can input or stored data be altered to change behavior? |
| Repudiation | Could an important action happen with no record? |
| Information disclosure | Can data leak through responses, logs, errors or URLs? |
| Denial of service | Can one client exhaust it (no size limit, no rate limit, no timeout)? |
| Elevation of privilege | Can a user reach data or actions outside their role? |

## 2. Check the controls

**Input and output**
- Queries are parameterized; no string-built SQL, shell commands or file paths from user input.
- Output is encoded for its context (HTML, attributes, URLs, JSON); no raw HTML from users.
- Input is validated at the boundary: type, length, format, allowlists for enums.
- Uploads: size limit, type checked from content not the name, stored outside the web root with generated names.
- Server-side fetches of user-supplied URLs go through an allowlist; block internal and metadata addresses.

**Auth and access**
- Every protected route checks authentication **and** that this user may touch this record (no IDs trusted from the client).
- Passwords hashed with bcrypt, scrypt or argon2; sessions expire and rotate on login; cookies are `HttpOnly`, `Secure`, `SameSite`.
- Rate limiting on login, signup, password reset and anything that sends email or SMS, using a shared store when there's more than one instance.

**Secrets and data**
- No secrets in code, config committed to git, logs, error messages or client bundles. Check `git log -p` for the touched files too.
- Errors shown to users are generic; details go to logs, and logs carry no tokens, passwords or full card or ID numbers.
- Personal data is limited to what the feature needs, with a retention period.
- CORS lists specific origins; security headers (CSP, HSTS, `X-Content-Type-Options`) are set.

**Dependencies**
- Run the ecosystem's audit (`npm audit`, `pip-audit`, `composer audit`, `govulncheck`). New dependencies are maintained, pinned in a lockfile and actually needed.

**LLM features**
- Model output is treated as untrusted input: validated and encoded before use, never executed or used to build queries.
- User content can't change system instructions or reach tools beyond the user's own permissions.

## 3. Destructive operations

Deletes or overwrites on paths or records derived from input resolve the real target first, then check it's inside the allowed root and owned by the user.

## Report

```markdown
## Findings
- **High** `path:line` · <threat>: how it's exploited, in one sentence → the fix
- **Medium** ...
- **Low** ...

## Checked, no issue
<one line listing the areas reviewed>

Audit: <command> → <result>
```

High: exploitable now with real impact. Medium: exploitable with conditions, or a missing control on a sensitive path. Low: defense in depth. Report findings only; don't change code unless asked. Anything needing a decision (a new auth provider, data retention) goes to the user as a question.
