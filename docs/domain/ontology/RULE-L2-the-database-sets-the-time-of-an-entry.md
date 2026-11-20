```yaml
id: RULE-L2
type: rule
name: The database sets the time of an entry
status: draft
object: OBJ-L1
statement: "The time of an audit entry is set by the database when the entry is added, and the API cannot set or change it."
proved_by: []
satisfies: []
```

# The database sets the time of an entry

## In plain words

The time on an entry is the time the database wrote it (`now()`). The application does not pass a time in.

## Why it exists

If the API could set the time, a bug or a stolen credential could back date or forward date an entry. One clock, the database's, also keeps entries in a true order.

## Allowed and refused

Allowed: an entry with a time the database gave it.

Refused: an add that carries a time chosen by the API.

## How a test would prove it

- Given the audit port, when an entry is added, then its time is the database's and the port takes no time (AC-80 note, run on PostgreSQL).
- Given the database role the API uses, when it tries to update an entry's time, then the database refuses (AC-80).

## Related

[RULE-L1](RULE-L1-an-audit-entry-is-never-changed-or-deleted.md), [OBJ-L1](OBJ-L1-audit-entry.md), [ADR 0011](../../adr/0011-audit-context-append-only.md).
