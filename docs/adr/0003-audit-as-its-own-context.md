# 0003 The audit trail is its own bounded context

- Status: accepted
- Date: 2026-11-19
- Decided by: the owner

## Context
Account changes and project changes both need an audit entry. Access owned the table, and Projects could not reuse its port without importing it.

## Decision
Audit is a context (BC-AUDIT) that owns the audit table and the administrator's read of it. Access and Projects each keep an AuditLog port, and the composition root wires an adapter that calls Audit. An entry holds the actor, the action, what kind of thing and which one, the people involved, the reason, the time, and names and emails as they were at the time.

## Consequences
No context imports another. The existing Access audit has to move, with a migration. A change and its audit entry should be one transaction, which needs care across the bridge. NOT BUILT YET.

## Links
decision 14; BC-AUDIT; docs/domain/diagrams/audit-design.puml; UC-L1.
