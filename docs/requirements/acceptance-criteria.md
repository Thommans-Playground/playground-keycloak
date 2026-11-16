# Acceptance criteria

<!-- Read and written by req_tool.py. Each row is one scenario: Given, When, Then. -->

| ID | Proves | Given | When | Then | Level | Status | Notes |
|---|---|---|---|---|---|---|---|
| AC-1 | FR-1 | a pending account | an administrator approves it | the account is active and the person can sign in | acceptance | draft |  |
| AC-2 | FR-1 | a pending account and a person who is not an administrator | that person tries to approve it | it is refused and the account stays pending | acceptance | draft | Only an administrator approves (permissions matrix). |
| AC-3 | FR-2 | a pending account | its owner makes any request other than asking for their own status | it is refused | acceptance | draft | Was 'sign-in is refused' before decision 24: the person can now sign in at Keycloak, and our API holds them. |
| AC-4 | FR-3 | an active account | an administrator deactivates it and gives a reason | the account is deactivated and its owner can no longer sign in | acceptance | draft |  |
| AC-5 | FR-3 | an active account | an administrator deactivates it without a reason | it is refused and the account stays active | acceptance | draft |  |
| AC-6 | FR-3 | an administrator's own account | that administrator tries to deactivate it | it is refused | unit | draft | An administrator cannot deactivate themselves. The rule is not written in the ontology yet. |
| AC-7 | FR-4 | a deactivated account | an administrator reinstates it | the account is active and its owner can sign in again | acceptance | draft |  |
| AC-8 | NFR-1 | each role (administrator, auditor, project manager, engineer) and a person who is not a member of the project | each makes every command and read the role is not allowed | the server refuses every one | acceptance | draft | This is the requirement's own measure: a refusal on every command and every read, for each role. |
| AC-9 | NFR-1 | a screen that hides a button the role may not use | the request is sent directly to the server | the server still refuses it | integration | draft |  |
| AC-75 | FR-2 | a pending account | its owner asks for their own status | it says the account is waiting for approval | acceptance | draft |  |
| AC-76 | FR-123 | a person the system does not know, signed in through the identity provider | they make their first request | a pending account exists for them | acceptance | draft |  |
| AC-77 | FR-123 | a person who already has an account | they make another request | no second account is created | acceptance | draft |  |
| AC-78 | FR-124 | an approved person with an identity provider account | they sign in through the identity provider | they can use the product | acceptance | draft |  |
| AC-79 | FR-125 | a signed-in person | they sign out | the product no longer accepts their session and asks them to sign in again | acceptance | draft |  |
| AC-80 | FR-126 | a signed-in person | they open their profile | it shows their name and account role | acceptance | draft |  |
| AC-81 | FR-127 | a request with no token, an expired token, or a token not issued by the identity provider | it is made to any protected route | it is refused | acceptance | draft | Each of the three is its own case in the test. |
| AC-82 | FR-128 | a signed-in administrator | they try to change an account's role through Playground | there is no way to do it | acceptance | draft |  |
| AC-83 | FR-128 | the identity provider account that the backend uses | its rights are listed | it cannot assign roles | inspection | draft | Needs checking against what Keycloak's admin roles allow. |
| AC-84 | FR-3 | an active account whose owner holds a valid token | an administrator deactivates it | the owner's next request is refused | acceptance | draft | Needs our API to check the account on every request, and the person's Keycloak sessions to end. |
| AC-85 | FR-3 | a deactivated account | its records are inspected | all of its data is still there | acceptance | draft |  |
| AC-86 | FR-3 | a deactivated person with an evaluation running | time passes | the evaluation reaches its end | future | draft | Cannot be tested until Evaluations exists. |
| AC-87 | FR-129; FR-130 | an administrator and an account that is active | they create a project with a name and name that account as manager | the project exists and that person is its manager | acceptance | draft |  |
| AC-88 | FR-129; FR-132 | a person who manages one project | they create a project | the new project exists and they are its manager | acceptance | draft |  |
| AC-89 | FR-129 | an engineer who manages no project | they try to create a project | it is refused and no project exists | acceptance | draft |  |
| AC-90 | FR-129 | an administrator | they create a project with an empty name | it is refused and no project exists | acceptance | draft |  |
| AC-91 | FR-130 | an administrator | they create a project and name no manager | it is refused and no project exists | acceptance | draft |  |
| AC-92 | FR-130 | an administrator and an account that is pending or deactivated | they name that account as the manager | it is refused and no project exists | acceptance | draft |  |
| AC-93 | FR-131 | a project created by an administrator | that administrator asks for its contents | it is refused, because they are not a member | acceptance | draft |  |
| AC-94 | FR-133 | a project manager and an account that is active | the manager adds that person as an engineer | the person is a member of the project with the role engineer | acceptance | draft |  |
| AC-95 | FR-133 | a project manager and an account that is pending or deactivated | the manager tries to add that person | it is refused and the person is not a member | acceptance | draft |  |
| AC-96 | FR-133 | an engineer of a project | they try to add a person to it | it is refused | acceptance | draft |  |
| AC-97 | FR-134 | a project with an engineer and a manager | the manager changes the engineer's role to project manager | the person is a project manager of that project | acceptance | draft |  |
| AC-98 | FR-134 | a member of a project | its manager removes the member | the person is no longer a member and their next request for the project is refused | acceptance | draft |  |
| AC-99 | FR-135 | a project with one manager | anyone tries to remove that manager | it is refused and the person is still its manager | unit | draft |  |
| AC-100 | FR-135 | a project with one manager | anyone tries to change that manager to an engineer | it is refused and the person is still its manager | unit | draft |  |
| AC-101 | FR-136 | an administrator and a project that has no active manager | the administrator tries to add themselves to the project | it is refused and they are not a member | acceptance | draft |  |
| AC-102 | FR-137 | a project whose only manager has a deactivated account | an administrator adds another person with an active account as a project manager | that person is a manager of the project | acceptance | draft |  |
| AC-103 | FR-137 | a project that has an active manager | an administrator tries to add a project manager | it is refused | acceptance | draft |  |
| AC-104 | FR-138 | an administrator and a project | they try to add an engineer, change a member's role or remove a member | it is refused and the members are unchanged | acceptance | draft |  |
| AC-105 | FR-139 | a manager and an engineer of the same project | each does the same thing with the project's contents | both are allowed | future | draft | Needs project contents (files, endpoints, evaluations) to exist. |
| AC-106 | FR-140 | a project, one of its members and a person who is not a member | each asks for the project's contents | the member sees them and the other person is refused | acceptance | draft |  |
| AC-107 | FR-141 | an administrator who is not a member of a project | they list the projects | they see its name and members and not its contents | acceptance | draft |  |
| AC-108 | FR-142 | a project that exists, an id that does not, and a person who is not a member of either | they ask for each | the answer is the same for both | acceptance | draft |  |
| AC-109 | FR-143 | a project | it is created and later a member is added | an audit entry exists for each, saying who did it and what it was | acceptance | draft |  |
| AC-110 | FR-143 | a project with a member | its manager removes the member | an audit entry exists saying who removed whom | acceptance | draft |  |
| AC-111 | NFR-2 | the final deployment design | each data store and the hosting are listed | each runs on an AWS service | inspection | draft |  |
| AC-112 | NFR-3 | the running API | its database setting is inspected | it is a PostgreSQL database | inspection | draft |  |
| AC-113 | NFR-3 | the API tests and a PostgreSQL database | the tests are run against it | they all pass | integration | draft |  |
| AC-114 | NFR-4 | the domain code | its imports are inspected | none comes from an adapter, a framework or an outside service | unit | draft |  |
| AC-115 | NFR-4 | a test double in place of the database adapter | the domain tests are run | they pass unchanged | unit | draft |  |
| AC-116 | NFR-5 | a rule or a use case and its code | the history is read | its test was committed before, or with, its code | inspection | draft |  |
| AC-117 | NFR-6 | the domain code | its names are compared with the ontology and the vocabulary | the same words are used | inspection | draft |  |
