# 0011 The Audit context, append only, enforced by the database

- Status: accepted; the audit outcome part of ADR 0009 is superseded by 0011
- Date: 2026-11-20
- Decided by: the agent (technical), after decision 21 (owner)
- Supersedes: the audit outcome part of ADR 0009 (one entry edited by `set_outcome`)

## Context
Decision 21 makes the audit trail append only and read only. ADR 0003 made Audit its own context and said it was not built. ADR 0010 gives every context the same folders. Today the audit table belongs to Access, `/audit` reads `svc.audit`, and `set_outcome` edits an entry.

## Decision
- `app/audit/` has `domain/` (AuditEntry, with the actor and target names and emails as they were at the time), `application/` (`AuditService` with `record` and `read`, and its ports) and `adapters/` (inbound `GET /audit`; outbound `SqlAuditEntries`).
- The port has two methods only: `add(entry)` and `list_newest_first()`. No update, no delete, no `set_outcome`. The application level proof is that the port and the routes have no way to change an entry (AC-79).
- The audit table is owned by a different database role from the one the API uses. A migration (Alembic, ADR 0004) creates the table with the owner role and grants the API's role INSERT and SELECT only (AC-80). On RDS this is two roles in one PostgreSQL database.
- Access and Projects each keep an `AuditLog` port in their own words. The composition root wires each to `AuditService.record` through a bridge, in the same database session so the change and its entry commit together.
- A failed Keycloak call after a deactivation adds a second entry (`keycloak_not_updated`); the first is not touched.
- No shared kernel: Audit has its own error base and clock, like every context (an owner question in ADR 0010 left to this record; revisit when a third context repeats the same code).
- One API database role and one session for each request. `composition/` builds the Audit adapter on that same session, so a change and its entry commit together.
- Migrations (Alembic) run as a separate owner role, in their own step (a one-off task on AWS). `create_all` goes. The API role owns nothing and cannot alter structure. Two secrets (owner, API) and a `MIGRATION_DATABASE_URL` setting.
- AC-80 widens: UPDATE, DELETE, TRUNCATE, ALTER and DROP are refused to the API role. The database sets the entry time (`now()`), the API cannot set it.
- Names and emails at the time: Access passes them in its own AuditLog port. Projects gets a small `People` port, answered by Access in `composition/`.
- Audit owns its own `Caller` in its domain, translated from the guard's result in `composition/`.
- The test database setup runs as the owner role, and AC-80 runs as the API role, on PostgreSQL only.
- A reason has a maximum length (500 characters) and rejects control and bidirectional override characters (AC-81).
- Reading the trail and every refusal write a line to the security log of decision 17, and never an audit entry (AC-82). The SecurityLog port is not merged yet, so this record does not name it.
- Every repeated deactivation (AC-77) adds an entry with its outcome and the retry's reason (decision 22).
- Migrations come first: Alembic with a baseline of today's schema is the first slice.

## Consequences
One more context and more files. The permissions need a second database role in dev, in the test stack and on RDS, and the AC-80 test runs on PostgreSQL only. The API loses the right to fix an entry, so every correction is a new entry. A hash chain and an immutable copy (S3 Object Lock, CloudWatch) are not part of the alpha, so the database owner (the RDS master user) can still edit rows. That risk is accepted for the alpha (decision 22, the security overlay). Personal data in the trail is kept for the alpha. Migrations need their own deploy step and a second secret in Secrets Manager.

## Links
decisions 21 and 22, decision 14, decision 18; ADR 0003, 0004, 0009, 0010; BC-AUDIT; UC-L1; AC-79, AC-80, AC-81, AC-82.

## Amendments (20 Nov 2026)
Added after review. They add detail and do not change the meaning above. Where the migration side is concerned, see ADR 0012.

- The API role is a **new role** with no superuser power, no CREATEROLE, no membership in the owner role, and it owns nothing.
- Grants are made **per table, with no default privileges**. They are an allow list for tables, sequences and schemas: no UPDATE, DELETE, TRUNCATE or TRIGGER, and no write on a sequence. The `id` becomes an identity column, so no sequence grant is needed. CREATE on the schema is revoked from PUBLIC and from the role.
- INSERT is granted on **chosen columns only**, so the API cannot set the time (the database does, RULE-L2).
- At start the API **checks its own role** and refuses to run if it is a superuser, owns a table, or can UPDATE the audit table.
- `MIGRATION_DATABASE_URL` exists **only in the migration container's environment**. The API refuses to start if it is present.
- The RDS PostgreSQL version must be **15 or later**. Before 15 the PUBLIC role has CREATE on the public schema, so the migration revokes it and the check depends on that.
