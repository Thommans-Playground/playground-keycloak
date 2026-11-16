```yaml
id: RULE-A3
type: rule
name: An account change needs a reason
status: draft
object: OBJ-A1
statement: "Promoting, demoting, deactivating or reinstating an account without a reason that says something is refused."
proved_by: []
satisfies: []
```

# An account change needs a reason

## In plain words

When an administrator promotes, demotes, deactivates or reinstates an account, they must say **why**. An empty
reason, or one that says nothing, is refused.

## Why it exists

These changes are hard to undo and they go into the audit trail. Promoting someone to administrator is the most
sensitive of them. A committee or an auditor reads the trail later, and a change with no reason teaches nobody
anything.

Creating an account does not need one: the person's own request already says why they asked.

## Allowed and refused

Allowed: "Left the team", "Needs to help approve requests".

Refused: an empty reason, or one that is only spaces or noise.

## How a test would prove it

- Given an active account, when an administrator deactivates it with no reason, then it is refused and it stays active.
- Given the same change with a real reason, then it succeeds and the reason is in the audit trail.

## Related

The audit entry is kept by the Audit context, which also turns away a reason that says nothing.
