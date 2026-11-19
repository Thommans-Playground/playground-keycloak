```yaml
id: BC-PROJECTS
type: context
name: Projects
status: draft
kind: supporting
owns:
  - OBJ-P1
  - OBJ-P2
  # SET-3 is parked by decision 13: it is not used in the alpha, and returns with role based access
refers_to:
  - context: BC-ACCESS
    how: by account id, for who a member is
  - context: BC-AUDIT
    how: Projects writes its audit entries through the AuditLog port, and the composition root wires the port to Audit (decision 14)
  - context: BC-FILES
    how: files carry a project id and are shown to a project's members and administrators only
  - context: BC-ENDPOINTS
    how: endpoints carry a project id and are shown to a project's members and administrators only
  - context: BC-EVALUATIONS
    how: evaluations carry a project id and are shown to a project's members and administrators only
ports_needed:
  - name: ProjectRepository
    answers: Find a project, list the projects of a member or all of them, and save a project with its memberships. Answered by the SQL adapter (SqlProjects) over the API database, Amazon RDS on AWS.
    status: planned
  - name: AccountStatus
    answers: Of this set of account ids, which are active? An id that is unknown or not active is left out. Answered by Access, through an adapter wired in the composition root.
    status: planned
  - name: AuditLog
    answers: Record who created a project or changed its members. Answered by Audit (BC-AUDIT), through an adapter wired in the composition root.
    status: planned
must_not:
  - Hold an account, a role of an account, a password or a token. That is Access (decision 1).
  - Show a project's contents or members to anyone but its members and the administrators (RULE-P4).
  - Look a role up. It receives the Caller, which says who is asking and whether they are an administrator, and never asks Access for either.
  - Import another context. It asks through a port, and the others ask it who is a member.
questions:
  - Who is in this project?
  - May this person see inside this project?
  - Which projects does this person belong to?
satisfies:
  - id: FR-7
  - id: FR-9
  - id: FR-12
  - id: FR-13
  - id: FR-16
```

# Projects context

## What it is

It decides **who is in a project, and so who may see inside it**. Access says who a person is and whether their
account is active. Projects says which projects they belong to. Files, endpoints and evaluations live
in other contexts. They carry a project id, and they are shown only to the project's members.

Decision 2 moved membership here from Access: it is an invariant of the project, so it belongs with the project.
Decision 13 sets the alpha scope: no project roles, and the administrator is a superuser.

## Its boundary

It owns the [project](../ontology/OBJ-P1-project.md) and the [membership](../ontology/OBJ-P2-membership.md). A
membership has no role in the alpha.

It refers to an account **by id**. It asks Access one question through the `AccountStatus` port: *of these account
ids, which are active?* It asks for a set at once, so a project created with several first members costs one
question. It never reads an account role, and it never looks at what Keycloak holds.

Its class diagram is [projects-design.puml](../diagrams/projects-design.puml) (planned, not built): the aggregate
`Project` with its `Membership`s, the value objects `ProjectName` and `Caller`, the rules in `ProjectRules`,
`ProjectsService`, the three ports and their adapters.

## What an administrator and a member can do

- An **administrator** is an account role and a superuser. Only an administrator creates a project, naming its first
  members (active accounts only), and only an administrator adds or removes members. They see inside every project.
- A **member** is a user who is in the project. Every member has the same rights: they run evaluations. A member
  does not change the members.
- Anyone else gets the same answer as for a project that does not exist.
- A project may be empty.

## The Caller

Projects never looks a role up. The composition root (`main.py`) runs the same full check as for the account
routes (the token, the account found, not deactivated, not pending), and only then builds a `Caller`: a value
object holding the **account id** and **is administrator**. Every use case of `ProjectsService` takes it as its
first argument. So a project route never sees a token, and a rule never reads a role from anywhere but the Caller.

## The rules it holds

- [RULE-P4](../ontology/RULE-P4-only-members-see-inside-a-project.md) Members and administrators see inside a
  project. Anyone else gets the same answer as for a project that does not exist. In code: `may_see(caller, project)`.
- Only an administrator changes members (decision 13). In code: `may_change_members(caller)`.
- A project name is trimmed and has 1 to 100 characters (`ProjectName`).
- A first member named at creation gets `added by` the creator. An administrator may name themselves, and a project may
  have none.

## Parked by decision 13

Not in the alpha, kept with their text, and brought back with role based access in a later release: the project
roles [SET-3](../ontology/SET-3-project-roles.md) (manager and engineer), [RULE-P1](../ontology/RULE-P1-a-project-always-has-a-manager.md)
(a project always has a manager), [RULE-P2](../ontology/RULE-P2-an-administrator-never-joins-by-role.md) (an
administrator never joins by role) and [RULE-P3](../ontology/RULE-P3-administrator-only-restores-a-manager.md) (an
administrator only restores a manager), and the role of a membership.

## How a request for a project is checked

```mermaid
sequenceDiagram
    participant P as Person
    participant M as Composition root
    participant S as ProjectsService
    participant R as ProjectRepository
    P->>M: a request about a project, with a token
    M->>M: token, account found, not deactivated, not pending
    M->>M: build the Caller (account id, is administrator)
    M->>S: the use case, with the Caller
    S->>R: get the project
    S->>S: may_see(caller, project)?
    S-->>M: the result, or ProjectNotFound for a missing project and for a person who may not see it
    M-->>P: the result, or the same 404 for both
```

The account is read on every request (by the check) and the membership is read on every request (by the use case).
Removing a member, or deactivating an account, takes effect at their very next request.

## The bridge to Access and Audit

Projects imports neither. `AccountStatus` and `AuditLog` are ports of Projects, and the composition root wires an
adapter to each: one that asks Access which accounts are active, and one that writes to Audit
([BC-AUDIT](BC-AUDIT.md), decision 14). The architecture test forbids a context importing another. The audit write
and the change to the project share one database session, so they are one transaction.

## What each refusal answers (decision 14)

Authorisation is checked before the input is validated. Every project route first passes the full check, with the
answers of the account routes (401 for a bad token, 403 for an account that is deactivated or pending).

| Case | Error | Answer |
|---|---|---|
| A project that does not exist, or a person who is neither a member nor an administrator, on any project route | `ProjectNotFound` | 404, the same for both |
| A member who is not an administrator adds or removes a member | `NotAnAdministrator` | 403 |
| A user who is not an administrator creates a project | `NotAnAdministrator` | 403 |
| A first member or an added person who is inactive or unknown | `MemberNotEligible` | 422, one answer for every reason |
| A name that is empty, only spaces, or over 100 characters | `InvalidProjectName` | 422 |
| A person to remove who is not a member (an administrator asks) | `MemberNotEligible` | 422 |

The last row is not decided by decision 14: see the open questions.

## The use cases

[UC-P1](../../usecases/UC-P1-create-a-project.md) creates a project.
[UC-P2](../../usecases/UC-P2-manage-project-members.md) manages its members.
[UC-P3](../../usecases/UC-P3-list-and-open-a-project.md) lists and opens projects.

## Questions this context leaves open

1. Must a project name be unique, and within what?
2. Does removing a member need a reason?
3. What does a removed member's earlier work show as: their name, or "removed member"?
4. Can a project be archived or deleted?
5. Which error answers an administrator who removes a person who is not a member? The table above says
   `MemberNotEligible`, 422, until it is decided.
6. Does a refused creation or a refused change leave an audit entry? Not in the alpha plan.

## Not yet built

All of it. The API has no project code (`apps/api/app/projects/` does not exist), and the class diagram is planned. Files, endpoints and evaluations are not yet ontology objects here, so they
are empty containers in the first cut.
