```yaml
id: RULE-A1
type: rule
name: There is always an administrator
status: draft
object: OBJ-A1
statement: "A change that would leave no active administrator is refused."
proved_by: []
satisfies: []
```

# There is always an administrator

## In plain words

Playground must always have at least one active administrator. If there is only one, they cannot be demoted or
deactivated.

## Why it exists

Without an administrator, nobody can work the queue, create an account or promote anyone. The only way out
would be to repair it by hand in Keycloak. This is the same guardrail that stops a cloud account from being
locked out of itself.

## Allowed and refused

Allowed: demoting or deactivating an administrator when another active administrator exists.

Refused: demoting or deactivating the **only** active administrator.

## How a test would prove it

- Given two administrators, when one is demoted, then it succeeds.
- Given one administrator, when they are demoted or deactivated, then it is refused and nothing changes.

## Related

The protected object is the [account](OBJ-A1-account.md). A related rule stops anyone changing themselves:
[RULE-A2](RULE-A2-administrator-cannot-change-themselves.md).
