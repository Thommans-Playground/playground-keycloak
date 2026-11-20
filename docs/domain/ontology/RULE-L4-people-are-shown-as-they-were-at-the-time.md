```yaml
id: RULE-L4
type: rule
name: People are shown as they were at the time
status: draft
object: OBJ-L1
statement: "An audit entry holds the name and email of each person and thing as they were when the event happened, and shows them so."
proved_by: []
satisfies: []
```

# People are shown as they were at the time

## In plain words

The entry copies the names and emails in when the event happens. If a person is renamed later, old entries still show the old name.

## Why it exists

A trail that follows the live name would rewrite history, and an entry would stop making sense if an account or project changed. This is a copy of the present name, not a history of names.

## Allowed and refused

Allowed: showing the copied name and email.

Refused: looking the name up again from the live account when the trail is read.

## How a test would prove it

- Given a person who was renamed after a change they made, when an administrator opens the audit trail, then the entry still shows the name they had at the time (AC-70).

## Related

[OBJ-L1](OBJ-L1-audit-entry.md), decision 14, [UC-L1](../../usecases/UC-L1-view-the-audit-trail.md).
