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
criteria:
  - id: AC-56
    reviewed: 9a5a098
  - id: AC-68
  - id: AC-69
  - id: AC-70
  - id: AC-79
  - id: AC-80
  - id: AC-82
  - id: AC-85
parameters: []
objects: [OBJ-L1]
rules: [RULE-L1, RULE-L2, RULE-L3, RULE-L4]
effects:
  - nothing changes, reading the trail writes no audit entry and changes no account or project, and the read and every refusal write a line to the security log (decision 17)
  - a first request by a brand new person can write a register entry, which is UC-A3's effect and not the read's
evolved_from: []
flow_reviewed: fdfbe64
```

# View the audit trail

<!-- vbench-uc:begin mirror (generated from the requirements files, do not edit here: change the row, then run sync) -->

<details>
<summary>The requirements and criteria it runs, copied from docs/requirements (1 requirement, 8 criteria). Do not edit.</summary>

## What this serves

**FR-17**: The system shall keep an audit trail of every account change and every project change, which an administrator can read.

## Acceptance criteria it runs

**AC-56** (acceptance, proves FR-17)

- Given an account change, such as an approval, a deactivation or a promotion
- When an administrator opens the audit trail
- Then the entry is there, with who, what, whom and the reason where one was asked

**AC-68** (acceptance, proves FR-17)

- Given a person who is not an active administrator: an ordinary user, a pending account, a deactivated account, or a request with no token
- When they ask for the audit trail
- Then each is refused (401 with no token or a bad one, 403 for the others) and no entry is shown

**AC-69** (acceptance, proves FR-17)

- Given no account or project change yet
- When an administrator opens the audit trail
- Then it is empty and is not an error

**AC-70** (acceptance, proves FR-17)

- Given a person who was renamed after a change they made
- When an administrator opens the audit trail
- Then the entry still shows the name they had at the time

**AC-79** (acceptance, proves FR-17)

- Given an audit entry that exists
- When anyone, including an administrator, tries to change or delete it through the application
- Then there is no way to do it: PUT, PATCH and DELETE on /audit answer 405 or 404, and the audit port has only add and list_newest_first (proven by an architecture test), so the trail only ever grows

**AC-80** (integration, proves FR-17)

- Given the database role the API connects with (not the owner role that runs the migrations)
- When it tries to update, delete, truncate, alter or drop the audit table
- Then the database refuses each one, while adding and reading still work, and an insert that names its own time is refused or its time is ignored (RULE-L2). The role holds only the privileges on the allow list: INSERT on chosen columns and SELECT on the table, with no other privilege

**AC-82** (acceptance, proves FR-17)

- Given an administrator who reads the audit trail, and a refused request for it from a caller who already has an account
- When each happens
- Then each writes a line to the security log (decision 17) and neither writes an audit entry

**AC-85** (acceptance, proves FR-17)

- Given an administrator who created a project, added a member and removed a member
- When an administrator opens the audit trail
- Then the trail shows the project creation and each member change, newest first, with the project's name and the people's names as they were at the time

## How it is verified

- acceptance: AC-56, AC-68, AC-69, AC-70, AC-79, AC-82, AC-85
- integration: AC-80

Each criterion is run by a test tagged `Verifies AC-<n>`.

</details>

<!-- vbench-uc:end mirror -->

## Description

An administrator opens one list of what people changed: account changes (approve, deactivate, reinstate, promote, demote) and project changes (a project created, a member added or removed). Each entry says who did it, what, to which account or project, which people were involved, and why where a reason was asked, as they were at the time. The trail is its own context, Audit (decision 14). Access and Projects write to it when they change something (UC-A4, UC-P1, UC-P2). This use case is only the read. Writing an entry is the last step of UC-A4, UC-P1 and UC-P2. Partly built: the administrator can already read the account entries, in the API (GET /audit) and as the audit table on the admin accounts page, from the Access context. Project entries, the people involved and the names at the time are not built.

## Preconditions

- The person is a signed-in administrator with an active account.
- Entries exist because other use cases wrote them. An empty trail is a valid answer.

## Main flow

1. The administrator asks to see the audit trail. (FR-17)
2. The system checks that the person is an active administrator, as for every request. (FR-17)
3. The system lists every entry, the newest first, account changes and project changes together. (FR-17, AC-56)
4. Each entry shows when it happened, who did it, what was done, which account or project it was done to, and the reason where one was asked. The people shown are named as they were at the time. (FR-17, AC-56)
5. An entry for a project creation also shows the project (its name) and its first members, and an entry for a member change shows the project and the member. Writing those entries is UC-P1 (AC-29) and UC-P2 (AC-30). Showing them in the trail is this use case's (AC-85). (FR-17)
6. The system writes a line to the security log for the read, and for every refusal, and writes no audit entry for either. (AC-82, decisions 17 and 22)

## Other flows

- The person is not an administrator, or is not signed in: the system refuses and shows no entry. An ordinary user, a pending account and a deactivated account get 403, and no token or a bad one gets 401. (AC-68)
- There are no entries yet: the system shows an empty trail, not an error. (AC-69)
- A person was renamed after an event: the entry still shows the name they had at the time. (AC-70, decision 14)
- A project entry is made when a project is created: it names the actor and the first members. That is UC-P1's, proven by AC-29.
- A project entry is made when a member is added or removed: it names the actor, what was done and the member. That is UC-P2's, proven by AC-30.
- An entry is changed or deleted by a route or a database statement: there is none, and the database refuses it. (AC-79, AC-80)
- A reason with more than 500 characters, or with a control or bidirectional override character, is refused where the change is made, so it never reaches the trail. That is UC-A4's, proven by AC-81.
- A brand new person's first request to /audit: the guard creates their pending account and writes a `register` entry (UC-A3's effect, decision 22), then refuses the read. The read itself writes nothing. (AC-82 covers a refused request from a caller who already has an account.)

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
- A10 (rule): An entry is never changed or deleted, by anyone, and the database refuses it too
- A11 (rule): Reading the trail and every refusal go to the security log, never to the audit trail
- A12 (rule): A reason is plain text of at most 500 characters (checked where the change is made, UC-A4, AC-81)

## Design

The parts that do the work. The class diagram is [audit-design.puml](../domain/diagrams/audit-design.puml) and the design sequence is
[UC-L1-view-the-audit-trail-design-sequence.puml](diagrams/UC-L1-view-the-audit-trail-design-sequence.puml). Both use the step numbers of the main flow.

**Built today, inside Access (D1, D5's read, D6, D11):** `GET /audit` with the administrator guard, the `audit_entries` table (time,
actor id, action, target id, reason) and `SqlAudit.entries()`, and the Audit trail table on the admin accounts page. They show account entries
only, and ids are turned into names in the web page. **Planned (decisions 14, 21 and 22, ADR 0011 and 0012): the rest**, that is the Audit context as its own folder
(D2, D3, D4, D5 as a port of Audit, D7, D8, D10), the `kind` and `details` columns, the names and emails at the time, and project entries.

- D1 (route): `GET /audit`, for an administrator only. Built in the Access routes, to move to the Audit context's routes. PUT, PATCH and DELETE on `/audit` answer 405 or 404 (AC-79). The refusal is 401 with no token or a bad one, and 403 for an ordinary user, a pending account or a deactivated account (AC-68)
- D2 (use case): AuditService with `record(entry)` and `read(caller)`. Planned. Today `AccessService.audit.entries()` does the read. `read` and every refusal write a line to the security log of decision 17, and never an audit entry (AC-82)
- D3 (entity): AuditEntry with time, actor (id, name, email), action, kind (account or project), target (id, name, email), details (the people involved) and reason. Planned. Today the entry is a dict with the id, time, actor id, action, target id and reason. The database sets the time (`now()`), the API cannot set it, and the id is an identity column, so the API role needs no sequence grant (ADR 0011, amendments). What each action records is the table in [BC-AUDIT](../domain/contexts/BC-AUDIT.md)
- D4 (value object): Audit's own Caller in its domain: the account id and whether it is an administrator. Composition translates the guard's result into it (decision 14, ADR 0011). Planned. Today the route takes the account and checks its role
- D5 (port): AuditRepository, with `add(entry)` and `list_newest_first()` only: no update, no delete, no `set_outcome`, proven by an architecture test (AC-79). Built as the Access `AuditLog` port (`record`, `entries` and `set_outcome`), to become Audit's own port
- D6 (adapter): SqlAuditEntries over the `audit_entries` table in PostgreSQL, which is Amazon RDS PostgreSQL on AWS. Built as SqlAudit, to move with the table and gain the new columns. It is built in composition on the same session as the request, so the change and its entry commit together
- D7 (adapter): AccessAuditBridge in composition/, which turns Access's `AuditLog` call into `AuditService.record`. Access passes the names and emails in its own AuditLog port. Planned
- D8 (adapter): ProjectsAuditBridge in composition/, the same for Projects' `AuditLog`. Projects gets the names and emails from a small `People` port that Access answers in composition/. Planned
- D9 (port): The `AuditLog` port of Access (built) and of Projects (planned), each in the words of its own context
- D10 (migration): Alembic migrations in `apps/api/migrations/`, outside `app/` (ADR 0012), run by the owner role in their own step (a one-off task on AWS, the `api-migrate` service in compose), never by the API. The baseline is slice 2. The move of the table (slice 4) adds `kind`, `details`, the names and emails at the time, the identity column and the database set time, and fills old rows with kind `account` and no names. `create_all` goes. Planned (decisions 14 and 22, ADR 0011 and 0012)
- D11 (page): The Audit trail table on the admin accounts page, kept thin, with no port of its own. Built for account entries, to show kind, people and names stored at the time
- D12 (database permission): the table is owned by the owner role (the migration role, a second secret). The API's role is a new role with no superuser power, no CREATEROLE, no membership in the owner role, and it owns nothing. Grants are per table, with no default privileges, from an allow list for tables, sequences and schemas: SELECT, and INSERT on chosen columns only (so the API cannot set the time), and no UPDATE, DELETE, TRUNCATE or TRIGGER and no sequence write. CREATE on the schema is revoked from PUBLIC and from the role. An update, a delete, a truncate, an alter or a drop is refused by PostgreSQL (AC-80). At start the API checks its own role and refuses to run if it is a superuser, owns a table or can UPDATE the audit table. There is one API role and one session for each request. The owner role can still edit rows, which is accepted for the alpha (decision 22). Planned, slice 3 (ADR 0011 amendments)
- D13 (setting): `MIGRATION_DATABASE_URL`, the owner role's URL, present only in the migration container's environment: the API refuses to start if it is present. Test fixtures run `alembic upgrade head` as the owner role (`TEST_MIGRATION_DATABASE_URL` beside `TEST_DATABASE_URL`, ADR 0012), and AC-80 runs as the API role, on PostgreSQL only. Planned
- D14 (rule): a reason is at most 500 characters and has no control or bidirectional override characters, checked in the domain of the context that asks for it, which is Access (AC-81, UC-A4, TSK-A4.9). Planned

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
A10 became -> D5, D6, D12
A11 became -> D1, D2
A12 became -> D14
+ D12 added: the database role of the API may add and read audit rows only (decision 21)
+ D10 added: the table moves out of Access, and the new columns need a migration (decision 14)
+ D13 added: the owner role's URL for the migration step only (decision 22, ADR 0011 and 0012)
+ D14 added: a reason has a maximum length and plain text only, checked by Access (AC-81 moved to UC-A4, decision 22)
```

## Changes in decision 22

- AC-29 and AC-30 (writing an entry) moved to UC-P1 and UC-P2, so this use case no longer lists them or FR-13 (decision 22)
- AC-68 covers an ordinary user, a pending account, a deactivated account and no token (401 or 403). AC-79 lists what is proven. AC-80 covers update, delete, truncate, alter and drop, and the privilege allow list. AC-81 is new and was moved to UC-A4 (TSK-A4.9), and AC-82 is new
- the slices were reordered (decision 22, ADR 0012): the second entry first, then Alembic, then the API role, then the move of the table, names at the time, the security log and the append only proof
- first request guard: the read goes through the same guard as every request, so a first request to /audit by a brand new person can write a register entry. That entry is UC-A3's effect, not the read's, and the read writes nothing

## Slices

- TSK-L1.1: A repeated deactivation adds its own entry with the outcome and the retry's reason, a failed Keycloak call adds a second entry, and `set_outcome` is removed. This is TSK-A4.8 in UC-A4 (the criteria are UC-A4's). No database role yet
- TSK-L1.2: Alembic baseline with the `migrations/` folder, the tests set up as the owner role, and `create_all` removed (ADR 0004 and 0012)
- TSK-L1.3: The API role, the grants for each table, the start-up self check, and AC-80 with the allow list test: each command in its own transaction on a table holding a row, expecting permission denied (42501), with the owner role running the same command as the control, rules RULE-L1, RULE-L2 (AC-80)
- TSK-L1.4: Move the table and the read into the Audit context, with kind, details, the names at the time, an identity column and the database set time (the migration also fills old rows with kind `account` and no names), one session for each request and the Caller translated in composition/ (AC-56, AC-68, AC-69)
- TSK-L1.5: The names and emails at the time (AC-70)
- TSK-L1.6: Reading the trail and every refusal write a line to the security log and no audit entry after the logging branch is merged (its ADR is renumbered 0013) (AC-82)
- TSK-L1.7: Append only is proven: the routes answer 405 or 404 and the port has two methods, rules RULE-L3, RULE-L4 (AC-79)
- TSK-L1.8: A project creation and a member change show in the trail, with the project's name and the people's names at the time, once Projects writes them (AC-85)

## Not in this use case

- Writing an entry. It is the last step of UC-A4, UC-P1 (TSK-P1.5, AC-29) and UC-P2 (TSK-P2.4, AC-30). The slices above were reordered by decision 22.
- Filtering, paging, exporting or deleting entries. The trail is append only (decision 21), and the alpha returns it whole.
- The reason limits (AC-81). They are UC-A4's (TSK-A4.9), where the reason is asked for.
- Keeping or erasing personal data in the trail. It is kept for the alpha and retention is open (decision 22).
