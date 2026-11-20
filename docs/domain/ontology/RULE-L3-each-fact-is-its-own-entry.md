```yaml
id: RULE-L3
type: rule
name: Each fact is its own entry
status: draft
object: OBJ-L1
statement: "Each fact that happened is its own audit entry, and a later fact adds an entry and never changes an earlier one."
proved_by: []
satisfies: []
```

# Each fact is its own entry

## In plain words

If a deactivation is saved and then the call to Keycloak fails, that is two facts, so two entries: the deactivation, and that Keycloak was not updated. A retry adds one more entry each time.

## Why it exists

Changing the first entry to add the outcome would break RULE-L1. Separate entries also show the real order of events, including the failures.

## Allowed and refused

Allowed: a second entry with outcome keycloak_not_updated after a deactivation, and one entry for each retry.

Refused: updating the first entry with the outcome, or merging a retry into an earlier entry.

## How a test would prove it

- Given an active account and a Keycloak that cannot be reached, when an administrator deactivates it, then the account is deactivated and the trail has the deactivation entry and a second entry that says Keycloak was not updated (AC-58).
- Given a deactivated account whose Keycloak user is still enabled, when an administrator deactivates it again, then one more entry is added and the first is untouched (AC-77).

## Related

[RULE-L1](RULE-L1-an-audit-entry-is-never-changed-or-deleted.md), [OBJ-L1](OBJ-L1-audit-entry.md), [ADR 0011](../../adr/0011-audit-context-append-only.md), [UC-A4](../../usecases/UC-A4-approve-deactivate-and-reinstate-an-account.md).
