```yaml
id: RULE-A1
type: rule
name: There is always an administrator
status: draft
object: OBJ-A1
statement: "A change that would leave no active administrator is refused, and the check and the change are one step."
proved_by: []
satisfies: []
```

# There is always an administrator

## In plain words

Playground must always have at least one active administrator. If there is only one, they cannot be demoted or
deactivated.

## Why it exists

Without an administrator, nobody can work the queue, approve an account or promote anyone. Roles live in our database, not in Keycloak, so
there is no repair by hand in Keycloak: the way out would be to edit the database directly. This is the same
guardrail that stops a cloud account from being locked out of itself.

The check and the change are **one step** (decision 14). If the count of active administrators were read first and the
change made after, two administrators demoting each other at the same moment would both pass the check and leave
none. A lock, or one conditional update, closes that gap.

## Allowed and refused

Allowed: demoting or deactivating an administrator when another active administrator exists.

Refused: demoting or deactivating the **only** active administrator.

## How a test would prove it

- Given two administrators, when one is demoted, then it succeeds.
- Given one administrator, when they are demoted or deactivated, then it is refused and nothing changes.
- Given two administrators, when each demotes the other at the same moment, then one is refused and an administrator remains (AC-62).

## Related

The protected object is the [account](OBJ-A1-account.md). A related rule stops anyone changing themselves:
[RULE-A2](RULE-A2-administrator-cannot-change-themselves.md).
