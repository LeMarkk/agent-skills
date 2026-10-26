# guard rule catalog

Starting points for `.claude/guard.json`, by tool. Copy only the entries for tools the project uses and change the paths to its real folders. Patterns are Python regular expressions searched in the whole command; in JSON, every `\` is written `\\`. In `protect_paths` globs, `*` also matches across folders, so `db/migrate/*.rb` covers nested files too.

guard's built-in rules already cover recursive deletes, git history rewrites, SQL `DROP`/`TRUNCATE` and unfiltered `DELETE`/`UPDATE`, Docker, Kubernetes, Terraform and cloud deletes. Don't repeat those here.

## Migrations and schema tools

Each block is ready to paste into `guard.json` (merge the `ask` and `protect_paths` lists if there are several). Change the folder in each glob to the project's real one.

**Prisma**
```json
{"ask": [{"pattern": "\\bprisma\\s+migrate\\s+reset\\b", "reason": "resets the database"},
         {"pattern": "\\bprisma\\s+db\\s+push\\b.*--accept-data-loss", "reason": "pushes a schema change that drops data"},
         {"pattern": "\\bprisma\\s+migrate\\s+resolve\\b", "reason": "rewrites the migration history table"}],
 "protect_paths": [{"glob": "prisma/migrations/*/migration.sql", "reason": "applied migrations never change; add a new one"}]}
```

**Drizzle** (the folder is `out` in `drizzle.config.*`)
```json
{"ask": [{"pattern": "\\bdrizzle-kit\\s+push\\b", "reason": "changes the schema without a migration"},
         {"pattern": "\\bdrizzle-kit\\s+drop\\b", "reason": "deletes a migration"}],
 "protect_paths": [{"glob": "drizzle/*.sql", "reason": "applied migrations never change; add a new one"},
                   {"glob": "drizzle/meta/*.json", "reason": "written by drizzle-kit"}]}
```

**golang-migrate**
```json
{"ask": [{"pattern": "(^|[;&|]\\s*)migrate\\s[^;&|]*\\s(down|drop|force)(\\s|$)", "reason": "rolls back, drops or forces the migration version"}],
 "protect_paths": [{"glob": "migrations/*.sql", "reason": "applied migrations never change; add a new one"}]}
```

**goose**
```json
{"ask": [{"pattern": "(^|[;&|]\\s*)goose\\s[^;&|]*\\s(down|reset|down-to)(\\s|$)", "reason": "rolls back migrations"}],
 "protect_paths": [{"glob": "migrations/*.sql", "reason": "applied migrations never change; add a new one"}]}
```

**Rails**
```json
{"ask": [{"pattern": "\\b(rails|rake)\\s+db:(drop|reset|schema:load|purge|rollback)\\b", "reason": "drops, resets or rolls back the database"}],
 "protect_paths": [{"glob": "db/migrate/*.rb", "reason": "applied migrations never change; add a new one"}]}
```

**Django**
```json
{"ask": [{"pattern": "\\bmanage\\.py\\s+flush\\b", "reason": "deletes all data"},
         {"pattern": "\\bmanage\\.py\\s+migrate\\s+\\S+\\s+zero\\b", "reason": "unapplies every migration of an app"}],
 "protect_paths": [{"glob": "*/migrations/0*.py", "reason": "applied migrations never change; add a new one"}]}
```

**Alembic**
```json
{"ask": [{"pattern": "\\balembic\\s+downgrade\\b", "reason": "rolls back migrations"}],
 "protect_paths": [{"glob": "alembic/versions/*.py", "reason": "applied migrations never change; add a new one"}]}
```

**Laravel**
```json
{"ask": [{"pattern": "\\bartisan\\s+(migrate:(fresh|reset|rollback)|db:wipe)\\b", "reason": "drops or rolls back the database"}],
 "protect_paths": [{"glob": "database/migrations/*.php", "reason": "applied migrations never change; add a new one"}]}
```

**Flyway and Liquibase**
```json
{"ask": [{"pattern": "\\bflyway\\b.*\\b(clean|repair)\\b", "reason": "drops the schema or rewrites migration history"},
         {"pattern": "\\bliquibase\\b.*\\b(drop-all|rollback)", "reason": "drops or rolls back the database"}],
 "protect_paths": [{"glob": "db/migration/V*.sql", "reason": "applied migrations never change; add a new one"}]}
```

**Supabase**
```json
{"ask": [{"pattern": "\\bsupabase\\s+db\\s+reset\\b", "reason": "resets the database"},
         {"pattern": "\\bsupabase\\s+db\\s+push\\b.*--linked", "reason": "pushes migrations to the linked remote project"}],
 "protect_paths": [{"glob": "supabase/migrations/*.sql", "reason": "applied migrations never change; add a new one"}]}
```

**Knex**
```json
{"ask": [{"pattern": "\\bknex\\s+migrate:(rollback|down)\\b", "reason": "rolls back migrations"}],
 "protect_paths": [{"glob": "migrations/*.js", "reason": "applied migrations never change; add a new one"}]}
```

## Data the project says is append-only

For tables the docs call append-only, immutable or audit logs:

```json
{"pattern": "(?i)\\b(UPDATE|DELETE\\s+FROM|TRUNCATE(\\s+TABLE)?)\\s+[\\w.\"]*\\b(audit_log|ledger_entries)\\b",
 "reason": "audit_log and ledger_entries are append-only; correct them with a new row"}
```

## Live and production switches

From `.env.example`, one entry per switch the team keeps off outside production:

```json
{"pattern": "\\bPAYMENTS_LIVE=[\"']?(true|1)\\b", "reason": "live payments only in prod"}
{"pattern": "\\bsk_live_[A-Za-z0-9]{8,}", "reason": "a live secret key in a command; use the test key"}
{"pattern": "\\bNODE_ENV=production\\b.*\\b(migrate|seed|reset)\\b", "reason": "production-mode database command"}
```

## Business rules the docs state

Turn a written rule into a command check where one can express it, for example "order status changes only through the state machine":

```json
{"pattern": "(?i)\\bUPDATE\\s+[\\w.\"]*\\borders\\b[^;]*\\bSET\\b[^;]*\\bstatus\\s*=",
 "reason": "order status changes go through the state machine, never a direct UPDATE"}
```

## Generated and reference files

Files the project regenerates by script, or treats as a signed-off reference:

```json
{"glob": "tests/fixtures/golden/*.json", "reason": "golden files change only by the regenerate script"}
{"glob": "openapi/generated/*", "reason": "generated from the spec; edit the spec and regenerate"}
```

## Deploy and data scripts

Package scripts or Makefile targets that wipe or deploy:

```json
{"pattern": "\\b(npm|pnpm|yarn)\\s+(run\\s+)?db:(reset|drop|wipe)\\b", "reason": "resets the database"}
{"pattern": "\\bmake\\s+(db-reset|deploy-prod|release)\\b", "reason": "resets data or deploys"}
```

`deny` is for the few commands nobody should run from an agent at all, such as a production deploy target:

```json
{"deny": [{"pattern": "\\bmake\\s+deploy-prod\\b", "reason": "production deploys go through CI"}]}
```
