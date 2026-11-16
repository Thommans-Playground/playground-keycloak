```yaml
id: RULE-A6
type: rule
name: Deactivation removes nothing
status: draft
object: OBJ-A1
statement: "Deactivating an account changes only its status. No endpoint, evaluation or share is removed or changed, and evaluations in progress finish."
proved_by: []
satisfies: []
```

# Deactivation removes nothing

## In plain words

Deactivating an account stops the person signing in. That is all it does. Their endpoints, their evaluations and
what they shared are all kept, and an evaluation that is already in progress finishes.

## Why it exists

Results are evidence, and other people may rely on what was shared with them. A person leaving must not delete
that. Keeping everything also means a reinstated person finds their work exactly as it was.

## Allowed and refused

Allowed: deactivating an account while its evaluations are running or shared.

Refused: any part of deactivation that deletes or changes work or shares.

## How a test would prove it

- Given an account with evaluations and shares, when it is deactivated, then every one of them is still there.
- Given a person with an evaluation in progress, when the account is deactivated, then the evaluation reaches its end.
- Given a deactivated account that is reinstated, then its work is as it was.

## Related

The status is in [SET-6](SET-6-account-statuses.md). The person's next request after deactivation is refused: their
token may still be valid, so the account is checked on every request.
