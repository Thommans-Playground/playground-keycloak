# 0011 The Audit context, append only, enforced by the database

- Status: accepted
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
- Migrations come first: Alembic with a baseline of today's schema is the first slice.

## Consequences
One more context and more files. The permissions need a second database role in dev, in the test stack and on RDS, and the AC-80 test runs on PostgreSQL only. The API loses the right to fix an entry, so every correction is a new entry. A hash chain and an immutable copy (S3 Object Lock, CloudWatch) are not part of the alpha.

## Links
decision 21, decision 14, decision 18; ADR 0003, 0004, 0009, 0010; BC-AUDIT; UC-L1; AC-79, AC-80.
