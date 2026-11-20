# 0012 Migrations live outside the app, and run as the owner role

- Status: accepted
- Date: 2026-11-20
- Decided by: the agent (technical), after decision 22 and ADR 0011

## Context
ADR 0004 chose Alembic. ADR 0011 needs an owner database role that runs migrations and a separate API role that cannot change structure. ADR 0010 forbids a loose package or file in `app/`, and a context never imports another. Alembic's `env.py` must see the tables of every context to compare the models with the database, so it cannot live inside one context.

## Decision
- Alembic lives in `apps/api/migrations/` (`env.py` and `versions/`), outside `app/`. It is not a context and not a layer.
- An architecture test rule says what `migrations/` may import: `infrastructure/` and the outbound table definitions only, never a `domain/` or an `application/` module. The rule fails with a message that says why.
- Test fixtures run `alembic upgrade head` as the owner role, using a new `TEST_MIGRATION_DATABASE_URL` beside `TEST_DATABASE_URL`. The app under test runs as the API role. The safety rule stays: the database name must end in `_test`.
- SQLite tests also use Alembic. Where a test needs a PostgreSQL feature (roles, grants, identity columns), it is skipped on SQLite.
- A drift test checks that the migrations produce the same schema as the models, so a model change without a migration fails.
- Roles belong to the PostgreSQL server, not to a database. Dev and test share one container, so an idempotent init script creates both roles once, with their attributes. An existing dev volume must be recreated, and `docs/GETTING-STARTED.md` says so.
- Compose gets a one-off `api-migrate` service that runs `alembic upgrade head` with the owner secret, mirroring the one-off task on AWS. The API starts after it.
- The security log ADR on branch `feat/UC-A1-basic-logging` is renumbered 0013 when it merges.

## Consequences
One more top level folder, allowed on purpose by this record. Each migration is code a person reviews. Dev needs a volume recreation once. The test setup is a little slower because it migrates. In return the schema has one source of truth, the API role can stay without any right to change structure, and the move to AWS is the same step in a task instead of a rewrite.

## Links
ADR 0004, 0010, 0011; decision 22; UC-L1 (TSK-L1.2, TSK-L1.3); AC-80.
