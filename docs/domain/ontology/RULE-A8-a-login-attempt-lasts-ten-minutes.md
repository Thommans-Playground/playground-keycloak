```yaml
id: RULE-A8
type: rule
name: A login attempt lasts ten minutes
status: draft
object: OBJ-A1
statement: "A login attempt is live for less than ten minutes. At ten minutes it is expired."
proved_by: [AC-38]
satisfies: [FR-1]
```

# A login attempt lasts ten minutes

## In plain words

The person has ten minutes to come back from Keycloak. One millisecond before ten minutes the attempt is live, and at ten minutes it is expired and the sign in is refused with "login expired".

## Why it exists

An open sign in that never expires is a standing invitation. A short limit keeps the window small, and the exact edge is testable.

## Allowed and refused

| Case | Answer |
|---|---|
| age under 10 minutes | live |
| age of 10 minutes or more | expired, "login expired" |

## How a test would prove it

`login-attempt.test.ts` tests the edge on the pure function `isExpired` and the constant (ten minutes), and the use case test `an attempt older than ten minutes fails`. Tagged `Verifies AC-38, RULE-A8`.

## Related

- [UC-A1 Sign in](../../usecases/UC-A1-sign-in.md)
