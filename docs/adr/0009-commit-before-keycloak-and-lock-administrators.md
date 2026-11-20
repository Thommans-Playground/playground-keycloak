# 0009 Commit a deactivation before calling Keycloak, and lock the administrators

- Status: accepted; the audit outcome part of ADR 0009 is superseded by 0011 (a second entry, not `set_outcome`)
- Date: 2026-11-20
- Decided by: the agent (technical), after the three UC-A4 reviews

## Context
The route owns the transaction: it commits after the service returns and rolls back on any exception. A deactivation that saves, calls Keycloak and raises on failure would lose the deactivation and its audit entry (AC-58). The last-administrator check and the change are two statements, so two administrators can both count two (AC-62). SQLite has no row locks.

## Decision
- The service commits the deactivation and its audit entry through a UnitOfWork port, then calls Keycloak, and returns an outcome ("done" or "Keycloak not updated") instead of raising. The outcome is recorded on the audit entry.
- The repository gets a port method that locks the active administrator rows (`SELECT ... FOR UPDATE`, in id order) and returns them. `decide` stays the only place the rule lives. The lock is released at the commit, which comes before any Keycloak call.
- AC-62 is proven on PostgreSQL only (`TEST_DATABASE_URL`). The fast SQLite suite does not run it.
- The port declares the failure it raises when Keycloak cannot be reached, and the adapter translates into it. Each step (disable, end sessions) is reported.

## Consequences
One more port, and the routes stop owning the commit for this use case. Administrator changes are serialised, which is fine at this volume. Works the same on RDS and Aurora.

## Links
decision 18; UC-A4 D11, D13; AC-58, AC-62, AC-77.
