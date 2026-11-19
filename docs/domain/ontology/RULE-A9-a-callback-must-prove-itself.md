```yaml
id: RULE-A9
type: rule
name: A callback must prove itself
status: draft
object: OBJ-A1
statement: "A sign in callback that carries the wrong state, a used code or an error from Keycloak makes no session."
proved_by: [AC-39]
satisfies: [FR-1]
```

# A callback must prove itself

## In plain words

The system makes a session only when the callback has the state of the attempt, a code that has not been used, and no error. A wrong state or a used code is "login failed", and a cancel or refusal at Keycloak is "login refused". Nothing is made in either case.

## Why it exists

The state ties the callback to the sign in that started it, and a code works once. Without them an attacker could finish someone else's sign in or replay a code.

## Allowed and refused

| Case | Answer |
|---|---|
| wrong state | refused, "login failed", no session |
| a code used before | refused, "login failed", no session |
| `error=` from Keycloak | refused, "login refused", no session |

## How a test would prove it

Use case tests: `a callback with the wrong state fails and makes no session`, `a code that was used before fails`, `a callback Keycloak marked as an error fails as refused`. Tagged `Verifies AC-39, RULE-A9`.

## Related

- [UC-A1 Sign in](../../usecases/UC-A1-sign-in.md)
