```yaml
id: RULE-A7
type: rule
name: A login attempt is used once
status: draft
object: OBJ-A1
statement: "A login attempt found by its id is taken out of the store when it is used, so a second callback with it fails."
proved_by: [AC-38]
satisfies: [FR-1]
```

# A login attempt is used once

## In plain words

When a person starts to sign in, the system keeps one login attempt for them. When they come back, the attempt is taken and removed. A second callback for the same attempt, an unknown attempt, or a request with no attempt cookie is refused with "login expired".

## Why it exists

A callback that could be replayed would let someone use a stolen link a second time. Taking the attempt makes the single use part of the store's promise.

## Allowed and refused

| Case | Answer |
|---|---|
| a known attempt, first time | accepted |
| the same attempt again | refused, "login expired" |
| an unknown attempt, or no cookie | refused, "login expired" |

## How a test would prove it

Use case tests with the in-memory store: `SI-4: an attempt works once`, `an unknown attempt fails`, `a missing attempt cookie fails`. Tagged `Verifies AC-38, RULE-A7` (and AC-42 for the missing cookie).

## Related

- [UC-A1 Sign in](../../usecases/UC-A1-sign-in.md)
