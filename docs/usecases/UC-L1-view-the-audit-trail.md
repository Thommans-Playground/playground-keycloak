```yaml
id: UC-L1
type: use-case
name: View the audit trail
status: draft
actor: administrator
context: BC-AUDIT
satisfies:
  - id: FR-17
    reviewed: 456b074
  - id: FR-13
    reviewed: 1667b7c
criteria:
  - id: AC-56
    reviewed: 9a5a098
  - id: AC-29
    reviewed: cb5e5d6
  - id: AC-30
    reviewed: 269d8a5
  - id: AC-68
  - id: AC-69
  - id: AC-70
parameters: []
objects: []
rules: []
effects:
  - nothing changes, reading the trail writes no entry and changes no account or project
evolved_from: []
flow_reviewed: fdfbe64
```

# View the audit trail

<!-- vbench-uc:begin mirror (generated from the requirements files, do not edit here: change the row, then run sync) -->

<details>
<summary>The requirements and criteria it runs, copied from docs/requirements (2 requirements, 6 criteria). Do not edit.</summary>

## What this serves

**FR-17**: The system shall keep an audit trail of every account change and every project change, which an administrator can read.

**FR-13**: The system shall record an audit entry for every project creation and every change to a project's members.

## Acceptance criteria it runs

**AC-56** (acceptance, proves FR-17)

- Given an account change and a project change
- When an administrator opens the audit trail
- Then both entries are there, with who, what, whom and the reason where one was asked

**AC-29** (acceptance, proves FR-13)

- Given a project
- When it is created
- Then an audit entry says who created it and who its first members are

**AC-30** (acceptance, proves FR-13)

- Given a project
- When a member is added or removed
- Then each has an entry saying who, what and whom

**AC-68** (acceptance, proves FR-17)

- Given a user who is not an administrator
- When they ask for the audit trail
- Then it is refused

**AC-69** (acceptance, proves FR-17)

- Given no account or project change yet
- When an administrator opens the audit trail
- Then it is empty and is not an error

**AC-70** (acceptance, proves FR-17)

- Given a person who was renamed after a change they made
- When an administrator opens the audit trail
- Then the entry still shows the name they had at the time

## How it is verified

- acceptance: AC-56, AC-29, AC-30, AC-68, AC-69, AC-70

Each criterion is run by a test tagged `Verifies AC-<n>`.

</details>

<!-- vbench-uc:end mirror -->

## Description

An administrator opens one list of what people changed: account changes (approve, deactivate, reinstate, promote, demote) and project changes (a project created, a member added or removed). Each entry says who did it, what, to which account or project, which people were involved, and why where a reason was asked, as they were at the time. The trail is its own context, Audit (decision 14). Access and Projects write to it when they change something (UC-A4, UC-P1, UC-P2). This use case is only the read. Partly built: the administrator can already read the account entries, in the API (GET /audit) and as the audit table on the admin accounts page, from the Access context. Project entries, the people involved and the names at the time are not built.

## Preconditions

- The person is a signed-in administrator with an active account.
- Entries exist because other use cases wrote them. An empty trail is a valid answer.

## Main flow

1. The administrator asks to see the audit trail. (FR-17)
2. The system checks that the person is an active administrator, as for every request. (FR-17)
3. The system lists every entry, the newest first, account changes and project changes together. (FR-17, AC-56)
4. Each entry shows when it happened, who did it, what was done, which account or project it was done to, and the reason where one was asked. The people shown are named as they were at the time. (FR-17, AC-56)
5. An entry for a project creation also shows its first members, and an entry for a member change shows the member. (FR-13, AC-29, AC-30)

## Other flows

- The person is not an administrator, or is not signed in: the system refuses and shows no entry. Open: no criterion proves this refusal yet.
- There are no entries yet: the system shows an empty trail, not an error. Open: no criterion proves this yet.
- A person was renamed after an event: the entry still shows the name they had at the time. Open: no criterion proves this yet (the security review, decision 14).
- A project entry is made when a project is created: it names the actor and the first members. (AC-29)
- A project entry is made when a member is added or removed: it names the actor, what was done and the member. (AC-30)

## Postconditions

- The administrator has seen the trail. Nothing has changed.

## Analysis

### Revision 1

What the administrator and Playground say to each other, with no route, store, port or token. The diagram is
[UC-L1-view-the-audit-trail-analysis-sequence.puml](diagrams/UC-L1-view-the-audit-trail-analysis-sequence.puml). Not frozen yet: read it, then freeze it.

- A1 (step): The administrator asks to see the audit trail
- A2 (refusal): A person who is not an administrator is refused and sees no entry
- A3 (step): Playground gathers every entry, newest first, account changes and project changes together
- A4 (step): Each entry shows when, who, what, to which account or project, and the reason where one was asked
- A5 (step): A project creation shows its first members, and a member change shows the member
- A6 (object): Audit entry
- A7 (rule): People are shown as they were at the time of the event
- A8 (rule): Reading the trail changes nothing
- A9 (rule): Only an administrator reads the trail

## Design

The parts that do the work. The class diagram is [audit-design.puml](../domain/diagrams/audit-design.puml) and the design sequence is
[UC-L1-view-the-audit-trail-design-sequence.puml](diagrams/UC-L1-view-the-audit-trail-design-sequence.puml). Both use the step numbers of the main flow.

**Built today, inside Access (D1, D5's read, D6, D11):** `GET /audit` with the administrator guard, the `audit_entries` table (time,
actor id, action, target id, reason) and `SqlAudit.entries()`, and the Audit trail table on the admin accounts page. They show account entries
only, and ids are turned into names in the web page. **Planned (decision 14): the rest**, that is the Audit context as its own folder
(D2, D3, D4, D5 as a port of Audit, D7, D8, D10), the `kind` and `details` columns, the names and emails at the time, and project entries.

- D1 (route): `GET /audit`, for an administrator only. Built in the Access routes, to move to the Audit context's routes
- D2 (use case): AuditService with `record(entry)` and `read(caller)`. Planned. Today `AccessService.audit.entries()` does the read
- D3 (entity): AuditEntry with time, actor (id, name, email), action, kind (account or project), target (id, name, email), details (the people involved) and reason. Planned. Today the entry is a dict with the id, time, actor id, action, target id and reason
- D4 (value object): Caller, the account id and whether it is an administrator, resolved by the API once (decision 14). Planned. Today the route takes the account and checks its role
- D5 (port): AuditRepository, with `add(entry)` and `list_newest_first()`. Built as the Access `AuditLog` port (`record` and `entries`), to become Audit's own port
- D6 (adapter): SqlAudit over the `audit_entries` table in PostgreSQL, which is Amazon RDS PostgreSQL on AWS. Built, to move with the table and gain the new columns
- D7 (adapter): AccessAuditBridge in the composition root, which turns Access's `AuditLog` call into `AuditService.record`. Planned
- D8 (adapter): ProjectsAuditBridge in the composition root, the same for Projects' `AuditLog`. Planned
- D9 (port): The `AuditLog` port of Access (built) and of Projects (planned), each in the words of its own context
- D10 (migration): Alembic migration that moves the table and adds `kind`, `details` and the names and emails. Planned (decision 14)
- D11 (page): The Audit trail table on the admin accounts page, kept thin, with no port of its own. Built for account entries, to show kind, people and names stored at the time

## Changes from analysis to design

```
A1 became -> D1
A2 became -> D1, D4
A3 became -> D2, D5, D6
A4 became -> D2, D3, D11
A5 became -> D3, D7, D8, D9
A6 became -> D3
A7 became -> D3, D7, D8
A8 became -> D2
A9 became -> D2, D4
+ D10 added: the table moves out of Access, and the new columns need a migration (decision 14)
```

## Slices

- TSK-L1.1: Move the audit table and the administrator's read into the Audit context, with the migration, and nothing changes for the administrator
- TSK-L1.2: An entry carries its kind, the people involved, and the names and emails at the time
- TSK-L1.3: A project creation writes an entry with the first members, through the Projects bridge (AC-29)
- TSK-L1.4: A member added or removed writes an entry with the member (AC-30)
- TSK-L1.5: The administrator reads account and project entries in one list (AC-56)

## Not in this use case

- Writing an entry. It is the last step of UC-A4, UC-P1 and UC-P2.
- Filtering, paging, exporting or deleting entries. The trail is append only, and the alpha returns it whole.
- Moving the audit table. It is slice 1, and the Alembic migration is part of decision 14.
