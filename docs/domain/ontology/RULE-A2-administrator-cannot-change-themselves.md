```yaml
id: RULE-A2
type: rule
name: An administrator cannot change themselves
status: draft
object: OBJ-A1
statement: "An administrator who tries to demote or deactivate their own account is refused."
proved_by: []
satisfies: []
```

# An administrator cannot change themselves

## In plain words

An administrator cannot demote or deactivate **their own** account. Another administrator has to do it.

## Why it exists

It prevents a slip that locks a person out, and it means the change is always seen by a second person. It
is the same rule, tested for deactivation in the domain tests.

## Allowed and refused

Allowed: an administrator demoting or deactivating **another** account.

Refused: an administrator demoting or deactivating their own account.

## How a test would prove it

- Given an administrator, when they ask to deactivate their own account, then it is refused.
- Given an administrator, when they ask to demote themselves, then it is refused.

## Related

[RULE-A1](RULE-A1-always-an-administrator.md) guards the last administrator. This rule guards everyone.
