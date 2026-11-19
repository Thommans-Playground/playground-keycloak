```yaml
id: RULE-A10
type: rule
name: A token is refreshed 30 seconds before it expires
status: draft
object: OBJ-A1
statement: "A session whose access token has 30 seconds or less left is refreshed before it is used."
proved_by: [AC-52]
satisfies: [FR-15]
```

# A token is refreshed 30 seconds before it expires

## In plain words

The web server uses an access token as it is while it has more than 30 seconds left. At 30 seconds or less, or when it has expired, it asks Keycloak for a new one first.

## Why it exists

A token that expires on its way to the API would make a request fail for no reason the person can see. The 30 seconds absorb the delay between the check and the use.

## Allowed and refused

| Case | Answer |
|---|---|
| more than 30 seconds left | used as it is |
| 30 seconds or less left, or expired | refreshed first |

## How a test would prove it

`session.test.ts` tests the edge on the pure function `needsRefresh`. Tagged `Verifies AC-52, RULE-A10`. The use case tests of `access-token.ts` carry AC-52, AC-53 and AC-54.

## Related

- [UC-A1 Sign in](../../usecases/UC-A1-sign-in.md)
