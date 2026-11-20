```yaml
id: RULE-A3
type: rule
name: An account change needs a reason
status: draft
object: OBJ-A1
statement: "Promoting, demoting, deactivating or reinstating an account without a reason that says something is refused. A reason is plain text of at most 500 characters, with no control or bidirectional override character."
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

Every change except an approval needs one, so a reinstatement needs a reason like a deactivation (decision 14).

Allowed: "Left the team", "Needs to help approve requests".

Refused: an empty reason, or one that is only spaces or noise.

A reason is **plain text of at most 500 characters** (AC-81). It is refused if it is longer, or if it has a control character or a bidirectional override character (for example U+202E), where the change is made, so the account stays as it was and no such text reaches the audit trail (decision 22). The limit is Access's, because Access asks for the reason. Audit stores it and never asks for one.

Why no control or override characters: they can hide or reorder text when an administrator reads the trail later, or break a log line.

## How a test would prove it

- Given an active account, when an administrator deactivates it with no reason, then it is refused and it stays active.
- Given a deactivated account, when an administrator reinstates it with no reason, then it is refused and it stays deactivated (AC-57).
- Given an account change with a reason of 501 characters, or one with a control or bidirectional override character, then it is refused and the account stays as it was (AC-81).
- Given the same change with a real reason, then it succeeds and the reason is in the audit trail.

## Related

The audit entry is kept by the Audit context, which also turns away a reason that says nothing.
