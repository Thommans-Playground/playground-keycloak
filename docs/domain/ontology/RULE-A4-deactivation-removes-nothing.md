```yaml
id: RULE-A4
type: rule
name: Deactivation removes nothing
status: draft
object: OBJ-A1
statement: "Deactivating an account changes only its status. Nothing the person made or belongs to is removed or changed, including their project memberships."
proved_by: []
satisfies:
  - id: FR-4
```

# Deactivation removes nothing

## In plain words

Deactivating an account stops the person using the product. That is all it does. Their data and their memberships of
projects are kept, so a reinstated person finds everything as it was.

## Why it exists

Work is evidence, and other people may rely on it. A person leaving must not delete it. A project manager's
deactivation also must not quietly empty a project: the membership stays, and the last-manager rule counts only active
managers ([RULE-P1](RULE-P1-a-project-always-has-a-manager.md)).

## Allowed and refused

Allowed: deactivating an account that belongs to projects.

Refused: any part of deactivation that deletes or changes the person's data or memberships.

## How a test would prove it

- Given an account that is a member of a project, when it is deactivated, then the membership is still there.
- Given a deactivated account that is reinstated, then the person is a member again, with their data as it was.

## Related

The status is in [SET-2](SET-2-account-statuses.md). The person's next request after deactivation is refused: their
token may still be valid, so the account is checked on every request.
