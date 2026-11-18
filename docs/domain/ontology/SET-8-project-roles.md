```yaml
id: SET-8
type: set
name: Project roles
status: draft
ordered: false
comment: What a person is in one project. Names only in the first cut.
values:
  - project manager
  - engineer
meanings:
  project manager: Does everything an engineer does in the project, and also keeps its members.
  engineer: Works with the project's files, endpoints and evaluations.
used_by:
  - OBJ-P2
questions:
  - Who keeps the members of this project?
  - Is this person a manager of any project?
satisfies:
  - id: FR-9
  - id: FR-12
```

# Project roles

## What it is

Two roles that a person holds **inside one project**. They are not account roles: a person can be a manager of
one project and an engineer in another. The account role (user or administrator, [SET-5](SET-5-account-roles.md))
belongs to Access and says nothing about projects.

## Why it is fixed

The first cut keeps the roles as names only. A project manager and an engineer can do the same things in a
project, except that only a manager changes its members. Fixing the list now lets the roles be pushed apart
later, with new rules, without changing who holds them.

## How it is used

- A project manager adds a person as a project manager or as an engineer
  ([OBJ-P2](OBJ-P2-membership.md)).
- A person who manages at least one project may create a new one ([UC-P1](../../usecases/UC-P1-create-a-project.md)).
- An administrator is not a project role. An administrator may only restore a manager
  ([RULE-P3](RULE-P3-administrator-only-restores-a-manager.md)).

Used by the [membership](OBJ-P2-membership.md).
