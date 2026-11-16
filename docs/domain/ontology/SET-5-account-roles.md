```yaml
id: SET-5
type: set
name: Account roles
status: draft
ordered: false
comment: What an account may do in Playground.
values:
  - user
  - administrator
meanings:
  user: Starts evaluations, and sees their own work and what has been shared with them.
  administrator: Does everything a user does, and also keeps the accounts. Reads none of anyone else's work.
used_by:
  - OBJ-A1
questions:
  - Is this person an administrator?
satisfies: []
```

# Account roles

## What it is

Two roles. A **user** starts evaluations and sees their own work and what is shared with them. An
**administrator** is a user who also keeps the accounts.

## What an administrator does

- works the queue of account requests and creates accounts,
- deactivates and reinstates accounts,
- promotes a user to administrator, or demotes one, always with a reason.

An administrator does **not** read other people's evaluations. They see them only if they are shared, like
anyone else ([RULE-A4](RULE-A4-see-own-work-and-what-is-shared.md)).

## How a user becomes an administrator

By being promoted by another administrator, from our screen. The role is changed in our own data and takes effect at
the person's next request. The first administrator comes from the Keycloak setup, because nobody exists yet to
promote them. There must always be at least one
([RULE-A1](RULE-A1-always-an-administrator.md)), and nobody changes their own role
([RULE-A2](RULE-A2-administrator-cannot-change-themselves.md)).

Used by the [account](OBJ-A1-account.md).
