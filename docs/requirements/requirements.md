# Requirements

<!-- Read and written by req_tool.py. A hand edit of a cell is fine: keep the table headers and the
     Notes bullets in the form `- **FR-1:** text`. An empty column is left out and comes back when used. -->

## Functional requirements

### Area A

| ID | Name | Statement | Verified by | Release | Built | Status | Objects | Sources |
|---|---|---|---|---|---|---|---|---|
| FR-1 | Sign in through the identity provider | The system shall let a person sign in through the identity provider. | acceptance test | R1 | yes | draft |  | decision 1; MK3 UC-A1 |
| FR-2 | Sign out | The system shall let a person sign out. | acceptance test | R1 | yes | draft |  | decision 1; MK3 UC-A2 |
| FR-3 | A new person is held as pending | The system shall hold a person it does not know as a pending account, who can see only that it is waiting for approval, until an administrator approves it. | acceptance test | R1 | yes | draft | OBJ-A1 | decision 2; MK3 UC-A5 |
| FR-4 | Decide who can use the product | The system shall let an administrator decide who can use the product: approve a pending account, deactivate an active one with a reason, and reinstate a deactivated one. | acceptance test | R1 | yes | draft |  | ADR 0019; ADR 0010; release plan R1 |
| FR-5 | Show name and account role | The system shall show a signed-in person their name and account role. | acceptance test | R1 | yes | draft | OBJ-A1 | decision 1; MK3 UC-A4 |
| FR-6 | Sign in through single sign-on | The system shall let a person sign in through single sign-on. | acceptance test | R2 | no | draft |  | release plan R2 |

**Notes**

- **FR-1:** Keycloak does it. Our side: send the person there, then check the token (decision 1).
- **FR-2:** Keycloak ends its session. We clear our own (UC-A2).
- **FR-3:** Held until approved (decision 2). The first administrator comes from setup (UC-A3).
- **FR-4:** Approval changes only our database. Deactivating also disables the person in Keycloak (UC-A4).
- **FR-5:** The name comes from the token, the role from our account.
- **FR-6:** Keycloak configuration. It proves who the person is, nothing else.

### Area P

| ID | Name | Statement | Verified by | Release | Built | Status | Sources |
|---|---|---|---|---|---|---|---|
| FR-7 | Create a project | The system shall let an administrator or a project manager create a project, which has a manager from the start. | acceptance test | R1 | no | draft | UC-P1; decision 3 |
| FR-8 | Administrators get no access to contents by role | The system shall not give an administrator access to a project's contents by their role. | acceptance test | R1 | no | draft | UC-P1; decision 3 |
| FR-9 | Manage project members | The system shall let a project manager add, change the role of and remove members of their project, adding only people with an active account. | acceptance test | R1 | no | draft | UC-P2; decision 3 |
| FR-10 | Keep an active manager | The system shall refuse a removal or demotion that would leave a project with no active project manager. | acceptance test | R1 | no | draft | UC-P2; decision 3 |
| FR-11 | Restore a project manager | The system shall let an administrator add a project manager to a project that has no active project manager, with a reason, and only a person with an active account who is not an administrator. | acceptance test | R1 | no | draft | UC-P2; decision 3 |
| FR-12 | Contents only for members | The system shall show a project's contents and member list only to its members, and answer anyone else as for a project that does not exist. | acceptance test | R1 | no | draft | decision 3; no use case yet |
| FR-13 | Audit project changes | The system shall record an audit entry for every project creation, every change to a project's members, and every refused attempt by an administrator to change them. | acceptance test | R1 | no | draft | UC-P1; UC-P2; decision 3 |

**Notes**

- **FR-7:** Name rules and who names the manager: UC-P1. Open: a second manager at creation?
- **FR-8:** The administrator's boundary: RULE-P2 and RULE-P3 (decision 3).
- **FR-9:** Roles are names only for now (UC-P2). Open: does removing a member need a reason?
- **FR-10:** Counts active managers only (RULE-P1).
- **FR-11:** The only administrator power over members (RULE-P3).
- **FR-12:** The same answer as for a missing project (RULE-P4). Contents are empty containers for now.
- **FR-13:** Who, what and whom it affected. Refused administrator attempts included.

## Quality, constraint and process requirements

### Area A

| ID | Kind | Name | Statement | Quality attribute | Stimulus | Environment | Response | Measure | Verified by | Release | Built | Status | Sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NFR-1 | quality | Access is checked on the server | The system shall check access on the server for every command and read. | Security | A person asks for something their role does not allow. | Normal operation, with the browser's role switch off. | The server refuses the request. | An acceptance test for each role shows a refusal on every command and every read. | inspection | R1 | no | draft | release plan R1; risk register R-08; north star |
| NFR-5 | quality | Security events are logged | The system shall write a log line for every refused sign in, every refused request and every session that starts or ends. | Security | A sign in is refused, a request is refused, or a session starts or ends. | Normal operation. | One log line is written with the event, the result, the person's id when it is known and a hash of the session id, and with no token or code in it. | An acceptance test for each event finds its log line, and none holds a token or a code. | acceptance test | R1 | no | draft | decision 12; vbench-security-reviewer on UC-A1 |

**Notes**

- **NFR-1:** The token is checked on every request, then the account and the membership (decision 1).

### Area No area

| ID | Kind | Name | Statement | Quality attribute | Stimulus | Environment | Response | Measure | Verified by | Release | Built | Status | Sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NFR-2 | constraint | Runs on AWS, data in PostgreSQL | The system shall run on AWS in its final form, with its own data in a PostgreSQL database. |  |  |  |  |  | inspection |  | no | draft | decision 4 |
| NFR-3 | quality | Swap an outside system by changing its adapter | The system shall let a developer replace an outside system by changing its adapter only. | Maintainability | A developer replaces the database, the identity provider or the session store. | Development, with the existing tests. | Only the adapter and its configuration change, and the domain code and its tests are unchanged. | No file in the domain imports an adapter, a framework or an outside library, and the domain tests pass unchanged. | inspection |  | yes | draft | decision 4 |
| NFR-4 | process | Failing test first | The team shall write a failing test before the code that makes it pass. |  |  |  |  |  | inspection |  | no | draft | decision 4 |

**Notes**

- **NFR-2:** Each piece has an AWS equivalent (decision 4). Open: RDS or Aurora?
- **NFR-3:** Ports and adapters (decisions 4 and 5), enforced by the two architecture tests.
- **NFR-4:** Test driven development (decision 4). Tests are tagged Verifies AC-n.
