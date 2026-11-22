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
| FR-4 | Decide who can use the product | The system shall let an administrator decide who can use the product: approve a pending account, deactivate an active one with a reason, and reinstate a deactivated one with a reason. | acceptance test | R1 | yes | draft |  | ADR 0019; ADR 0010; release plan R1 |
| FR-5 | Show name and account role | The system shall show a signed-in person their name and account role. | acceptance test | R1 | yes | draft | OBJ-A1 | decision 1; MK3 UC-A4 |
| FR-6 | Sign in through single sign-on | The system shall let a person sign in through single sign-on. | acceptance test | R2 | no | draft |  | release plan R2 |
| FR-14 | Promote and demote administrators | The system shall let an administrator promote a user to administrator and demote another administrator, with a reason. | acceptance test | R1 | yes | draft | OBJ-A1 | decision 13 |
| FR-15 | Keep a person signed in | The system shall keep a signed-in person signed in until the session limits. | acceptance test | R1 | yes | draft |  | decision 14; UC-A6 |

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
| FR-7 | Create a project | The system shall let an administrator create a project and name its first members. | acceptance test | R1 | no | draft | UC-P1; decision 3 |
| FR-8 | Administrators get no access to contents by role | The system shall not give an administrator access to a project's contents by their role. | acceptance test | parked | no | draft | decision 3; parked by decision 13 |
| FR-9 | Manage project members | The system shall let an administrator add and remove members of a project, adding only people with an active account. | acceptance test | R1 | no | draft | UC-P2; decision 3 |
| FR-10 | Keep an active manager | The system shall refuse a removal or demotion that would leave a project with no active project manager. | acceptance test | parked | no | draft | decision 3; parked by decision 13 |
| FR-11 | Restore a project manager | The system shall let an administrator add a project manager to a project that has no active project manager, with a reason, and only a person with an active account who is not an administrator. | acceptance test | parked | no | draft | decision 3; parked by decision 13 |
| FR-12 | Contents only for members | The system shall show a project's contents and member list only to its members and to administrators, and answer anyone else as for a project that does not exist. | acceptance test | R1 | no | draft | decision 3; UC-P2; UC-P3 |
| FR-13 | Audit project changes | The system shall record an audit entry for every project creation and every change to a project's members. | acceptance test | R1 | no | draft | UC-P1; UC-P2; decision 3 |
| FR-16 | See and open projects | The system shall let a person list the projects they belong to, let an administrator list all projects, and let either open a project they may see. | acceptance test | R1 | no | draft | decision 14; UC-P3 |

**Notes**

- **FR-7:** Name rules and the first members: UC-P1 (decision 23). A project has no manager in the alpha (decision 13).
- **FR-8:** Parked by decision 13: the administrator is a superuser in the alpha.
- **FR-9:** No project roles in the alpha (decision 13). Removing a person who is not a member is refused (decision 23). Open: does removing a member need a reason?
- **FR-10:** Parked by decision 13: there are no project managers in the alpha.
- **FR-11:** Parked by decision 13: there are no project managers in the alpha.
- **FR-12:** The same answer as for a missing project (RULE-P4). Contents are the empty lists files, endpoints and evaluations, placeholders with no requirement behind them yet (decision 23).
- **FR-13:** Who, what and whom, with the names as they were at the time (BC-AUDIT). Refusals go to the security log, not the trail (decision 22).

### Area L

| ID | Name | Statement | Verified by | Release | Built | Status | Objects | Sources |
|---|---|---|---|---|---|---|---|---|
| FR-17 | Audit trail | The system shall keep an audit trail of every account change and every project change, which an administrator can read. | acceptance test | R1 | no | draft | OBJ-A1 | decision 14; BC-AUDIT |

## Quality, constraint and process requirements

### Area A

| ID | Kind | Name | Statement | Quality attribute | Stimulus | Environment | Response | Measure | Verified by | Release | Built | Status | Sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NFR-1 | quality | Access is checked on the server | The system shall check access on the server for every command and read. | Security | A person asks for something their role does not allow. | Normal operation, with the browser's role switch off. | The server refuses the request. | An acceptance test for each role shows a refusal on every command and every read. | inspection | R1 | no | draft | release plan R1; risk register R-08; north star |
| NFR-5 | quality | Security events are logged | The system shall write a log line for every refused sign in, every refused request and every session that starts or ends. | Security | A sign in is refused, a request is refused, or a session starts or ends. | Normal operation. | One log line is written with the event, the result, the person's id when it is known and a hash of the session id, and with no token or code in it. | An acceptance test for each event finds its log line, and none holds a token or a code. | acceptance test | R1 | no | draft | decision 12; vbench-security-reviewer on UC-A1 |
| NFR-6 | quality | Browsers are told to protect our pages | The system shall tell the browser to protect every page and every answer it serves, with a content security policy, a ban on being framed by another site, no guessing of content types and no stack names. | Security | A page or an API answer is fetched. | Normal operation, on the web app and on the API. | The answer carries the protection headers and none that names the framework. | An acceptance test reads the headers of a page and of an API answer. | acceptance test | R1 | no | draft | security test of UC-A1 |

**Notes**

- **NFR-1:** The token is checked on every request, then the account and the membership (decision 1).
- **NFR-5:** Brought into the alpha by decision 17 (it was deferred to R2 by decision 13).

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
