# Requirements

<!-- Read and written by req_tool.py. A hand edit of a cell is fine: keep the table headers and the
     Notes bullets in the form `- **FR-1:** text`. An empty column is left out and comes back when used. -->

## Functional requirements

### Area A

| ID | Name | Statement | Verified by | Release | Built | Status | Objects | Sources |
|---|---|---|---|---|---|---|---|---|
| FR-1 | Approve an account | The system shall let an administrator approve a pending account so that the person can sign in. | acceptance test | R1 | no | draft |  | ADR 0019; ADR 0010; release plan R1 |
| FR-2 | A pending account sees only its status | The system shall let a person with a pending account see only that their account is waiting for approval, and refuse everything else. | acceptance test | R1 | no | draft |  | ADR 0019; release plan R1 |
| FR-3 | Deactivate an account | The system shall let an administrator deactivate an account, with a reason. | acceptance test | R1 | no | draft |  | ADR 0019; ADR 0010 |
| FR-4 | Reinstate an account | The system shall let an administrator reinstate a deactivated account. | acceptance test | R1 | no | draft |  | ADR 0019; ADR 0010 |
| FR-5 | One account role | The system shall give each account exactly one role: member, administrator or auditor. | unit test |  | yes | draft |  | ADR 0019 |
| FR-24 | Sign in through single sign-on | The system shall let a person sign in through single sign-on. | acceptance test | R2 | no | draft |  | release plan R2 |
| FR-123 | A new person arrives pending | The system shall create a pending account the first time a person it does not know reaches it through the identity provider. | acceptance test | R1 | no | draft | OBJ-A1 | decision 24; MK3 UC-A5 |
| FR-124 | Sign in through the identity provider | The system shall let a person sign in through the identity provider. | acceptance test | R1 | no | draft |  | decision 23; MK3 UC-A1 |
| FR-125 | Sign out | The system shall let a person sign out. | acceptance test | R1 | no | draft |  | decision 23; MK3 UC-A2 |
| FR-126 | Show name and account role | The system shall show a signed-in person their name and account role. | acceptance test | R1 | no | draft | OBJ-A1 | decision 23; MK3 UC-A4 |
| FR-127 | Refuse a request with no valid token | The system shall refuse a request that has no valid token from the identity provider. | acceptance test | R1 | no | draft |  | decision 23; NFR-1 |
| FR-128 | No role change from our screens | The system shall not let anyone give or take away an account role from its own screens. | acceptance test | R1 | no | draft |  | decision 23; MK3 UC-A7 decision D13 |

**Notes**

- **FR-1:** Needs an Account object in the ontology. A new account starts pending. Approval is a status change in Playground only: Keycloak is not called (decision 24).
- **FR-2:** The person can sign in at Keycloak and gets a token, but our API refuses every request except asking for their own status (decision 24). It replaced 'prevent from signing in'.
- **FR-3:** An administrator cannot deactivate themselves: a rule to write in the ontology. The reason and the audit entry are kept by Playground. The backend disables the person in Keycloak and ends their sessions (decision 23).
- **FR-4:** The backend enables the person in Keycloak again and sets the account active (decisions 23 and 24).
- **FR-5:** The account role is kept in Playground's database, not in Keycloak (decision 23, amended). Project roles stay in our database too.
- **FR-24:** Keycloak configuration. Single sign-on proves who the person is and nothing else: roles stay in Playground, and a person with no account is refused and offered the account request page. The release is the owner's call.
- **FR-123:** Our API holds the person until an administrator approves. Needs the Account object in the ontology.
- **FR-124:** Keycloak does it. Our side: send the person there, then check the token that comes back.
- **FR-125:** Keycloak ends its session. We clear our own session.
- **FR-126:** The name comes from the token and the role from our account. Passwords and email are changed on Keycloak's own account page.
- **FR-127:** A valid token has the right signature, has not expired, and was issued by the identity provider for this product.
- **FR-128:** A role is changed in Keycloak only, so a hacked administrator session cannot make a second administrator.

### Area P

| ID | Name | Statement | Verified by | Release | Built | Status | Sources |
|---|---|---|---|---|---|---|---|
| FR-129 | Create a project | The system shall let an administrator or a project manager create a project. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-130 | Administrator names the manager | The system shall require an administrator who creates a project to name its manager, who must have an active account. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-131 | Administrator is not a member | The system shall not make an administrator who creates a project a member of it. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-132 | Creator becomes the manager | The system shall make a project manager who creates a project its manager. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-133 | Add a project member | The system shall let a project manager add a person with an active account to their project, as a project manager or an engineer. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-134 | Change or remove a member | The system shall let a project manager change a member's project role or remove a member from their project. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-135 | Keep a manager | The system shall never remove or demote the last project manager of a project. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-136 | Administrator cannot join | The system shall not let an administrator add themselves to a project. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-137 | Administrator can restore a manager | The system shall let an administrator add a project manager to a project that has no active project manager. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-138 | Administrator changes nothing else | The system shall not let an administrator change the members of a project in any other way. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-139 | Same abilities for every member | The system shall let every member of a project do the same things in it, except manage its members. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-140 | Contents only for members | The system shall show the contents of a project (its files, endpoints and evaluations) only to its members. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-141 | Administrator sees every project | The system shall let an administrator see the name and the members of every project. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-142 | Hide that a project exists | The system shall refuse a person who is not a member of a project, with an answer that does not reveal whether the project exists. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |
| FR-143 | Audit project changes | The system shall record an audit entry for every project creation and every change to a project's members. | acceptance test | R1 | no | draft | UC-P1; UC-P4; decision 24 |

**Notes**

- **FR-129:** A project manager here means someone who manages at least one project. An administrator creates the first project and names its manager. Project and Membership are not ontology objects yet: hand to vbench-ontology. Open: must a project name be unique, and within what?
- **FR-130:** A project must have a manager from the start.
- **FR-131:** An administrator manages access and does not see inside projects. Contents need membership.
- **FR-132:** Open: can the creator name a second manager at creation?
- **FR-133:** Roles are names only for now: a project manager and an engineer do the same things, except for managing members.
- **FR-134:** Open: does removing a member need a reason? For now only an audit entry.
- **FR-135:** A deactivated account is not removed from a project, so it still counts as a member for this rule.
- **FR-136:** Administrators are not given a way into a project's contents.
- **FR-137:** The only way an administrator changes a project's members. Needed so a project is never stuck when its manager is deactivated.
- **FR-138:** Excludes adding themselves (FR-136), adding an engineer, changing a role and removing a member.
- **FR-139:** First cut: manager and engineer differ in name only, apart from managing members. The release may push this apart later.
- **FR-140:** Files, endpoints and evaluations are empty containers in the first cut.
- **FR-141:** High level access only: names and members, never contents.
- **FR-142:** Supports the access check on the server (NFR-1).
- **FR-143:** Who, what and who it affected.

## Quality, constraint and process requirements

### Area A

| ID | Kind | Name | Statement | Quality attribute | Stimulus | Environment | Response | Measure | Verified by | Release | Built | Status | Sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NFR-1 | quality | Access is checked on the server | The system shall check access on the server for every command and read. | Security | A person asks for something their role does not allow. | Normal operation, with the browser's role switch off. | The server refuses the request. | An acceptance test for each role shows a refusal on every command and every read. | inspection | R1 | no | draft | release plan R1; risk register R-08; north star |

**Notes**

- **NFR-1:** The server checks the Keycloak token (signature, expiry, issuer) on every request, then checks project membership (decision 23).
