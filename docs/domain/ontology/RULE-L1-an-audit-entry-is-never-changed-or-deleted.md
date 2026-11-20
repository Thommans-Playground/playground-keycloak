```yaml
id: RULE-L1
type: rule
name: An audit entry is never changed or deleted
status: draft
object: OBJ-L1
statement: "An audit entry, once written, is never changed or deleted, by anyone, through the application or the database."
proved_by: []
satisfies: []
```

# An audit entry is never changed or deleted

## In plain words

The trail only grows. Nobody, not even an administrator, can edit or remove an entry. A mistake is put right by a new entry that says so, never by changing the old one.

## Why it exists

A trail that can be rewritten proves nothing. A bug, a stolen API credential or a person with a grudge must not be able to change history.

## Allowed and refused

Allowed: adding an entry, and listing entries newest first.

Refused: changing an entry, deleting it, truncating or altering or dropping the table, by a route or by a database statement.

## How a test would prove it

- Given an entry, when anyone sends PUT, PATCH or DELETE on /audit, then it answers 405 or 404, and the audit port has only add and list_newest_first, proven by an architecture test (AC-79).
- Given the database role the API connects with, when it tries to update, delete, truncate, alter or drop the audit table, then the database refuses each one, while adding and reading still work (AC-80). Runs on PostgreSQL only.

## Related

[OBJ-L1](OBJ-L1-audit-entry.md), decisions 21 and 22, [ADR 0011](../../adr/0011-audit-context-append-only.md), [UC-L1](../../usecases/UC-L1-view-the-audit-trail.md).
