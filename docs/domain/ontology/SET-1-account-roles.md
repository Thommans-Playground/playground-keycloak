```yaml
id: SET-1
type: set
name: Account roles
status: draft
ordered: false
comment: What an account may do in Playground.
values:
  - user
  - administrator
meanings:
  user: Uses the product, and sees the projects they are a member of.
  administrator: Does everything a user does, and also keeps the accounts. In the alpha a superuser (decision 13), who creates projects, manages members and sees inside every project.
used_by:
  - OBJ-A1
questions:
  - Is this person an administrator?
satisfies:
  - id: FR-4
```

# Account roles

## What it is

Two roles. A **user** uses the product and sees the projects they are a member of. An **administrator** is a user who
also keeps the accounts.

## What an administrator does

- approves pending accounts, deactivates and reinstates accounts, always with a reason where one is needed
  ([UC-A4](../../usecases/UC-A4-approve-deactivate-and-reinstate-an-account.md)),
- promotes a user to administrator, or demotes one, with a reason (UC-A4; built in the API and the admin accounts table),
- creates a project by naming its first members, and adds and removes members
  ([UC-P1](../../usecases/UC-P1-create-a-project.md), [UC-P2](../../usecases/UC-P2-manage-project-members.md)),
- sees inside every project (decision 13). The older rule that an administrator does not see inside a project by
  role ([RULE-P2](RULE-P2-an-administrator-never-joins-by-role.md)) is parked.

## How a user becomes an administrator

By being promoted by another administrator. The role is changed in our own data and takes effect at the person's next
request. The first administrator comes from the Keycloak setup, because nobody exists yet to promote them
([RULE-A1](RULE-A1-always-an-administrator.md)).

## Why the role lives here and not in Keycloak

Promotion, its reason and its guardrails are in one place, and nobody can change a role behind the product's back
([RULE-A2](RULE-A2-administrator-cannot-change-themselves.md), [RULE-A3](RULE-A3-account-change-needs-a-reason.md)).

Used by the [account](OBJ-A1-account.md).
