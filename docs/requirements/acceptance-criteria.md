# Acceptance criteria

<!-- Read and written by req_tool.py. Each row is one scenario: Given, When, Then. -->

| ID | Proves | Given | When | Then | Level | Status | Notes |
|---|---|---|---|---|---|---|---|
| AC-1 | FR-1 | an approved person | they sign in through the identity provider | they can use the product | acceptance | draft |  |
| AC-2 | FR-2 | a signed-in person | they sign out | their session stops working and they must sign in again | acceptance | draft |  |
| AC-3 | FR-3 | a person the system does not know | they make a request, then another | one pending account exists for them | acceptance | draft |  |
| AC-4 | FR-3 | a pending account | its owner asks for their status, then for anything else | the status says it is waiting, and everything else is refused | acceptance | draft |  |
| AC-5 | FR-4 | a pending account | an administrator approves it | the person can use the product, with no change made in Keycloak | acceptance | draft |  |
| AC-6 | FR-4 | an active account | an administrator deactivates it, with a reason | the person cannot sign in at Keycloak, and their next request is refused even with a valid token | acceptance | draft |  |
| AC-7 | FR-4 | a deactivated account | an administrator reinstates it | the person can use the product again, with their data and memberships, and is enabled in Keycloak | acceptance | draft |  |
| AC-8 | FR-5 | a signed-in person | they open their profile | it shows their name and role | acceptance | draft |  |
| AC-9 | FR-7 | an administrator and an active account | they create a project naming that account as manager | the project exists and that person is its manager | acceptance | draft |  |
| AC-10 | FR-7 | a person who manages a project | they create a project | it exists and they are its manager | acceptance | draft |  |
| AC-11 | FR-7 | a person who manages no project and is not an administrator | they try to create a project | it is refused | acceptance | draft |  |
| AC-12 | FR-7 | a project name that is empty, only spaces, or over 100 characters | a project is created with it | it is refused | acceptance | draft |  |
| AC-13 | FR-7 | an administrator | they create a project naming no manager, or one who is not active or does not exist | it is refused, with one answer for an account that cannot be a manager | acceptance | draft |  |
| AC-14 | FR-8 | a project an administrator created for someone else | that administrator asks for its contents | it is refused | acceptance | draft |  |
| AC-15 | FR-8 | an administrator | they add themselves to a project, or name themselves its manager | it is refused and they are not a member | acceptance | draft |  |
| AC-16 | FR-8 | an administrator who is not a member of a project | they list the projects | they see its name and members, never its contents | acceptance | draft |  |
| AC-17 | FR-9 | a manager and an active account | the manager adds that person as an engineer | they are a member with that role | acceptance | draft |  |
| AC-18 | FR-9 | a manager and an account that is pending, deactivated or unknown | the manager adds it | it is refused, with one answer for all three | acceptance | draft |  |
| AC-19 | FR-9 | an engineer in a project | their manager makes them a manager | they are a manager of the project | acceptance | draft |  |
| AC-20 | FR-9 | a member of a project | their manager removes them | they are out, and their next request gets the same answer as for a missing project | acceptance | draft |  |
| AC-21 | FR-10 | a project with one active manager | anyone removes or demotes that manager | it is refused | unit | draft |  |
| AC-22 | FR-9; FR-10 | a project with two active managers | one of them removes themselves | it is allowed and the other remains | unit | draft |  |
| AC-23 | FR-11 | a project with no active manager, and an active person who is not an administrator | an administrator adds that person as manager, with a reason | they are a manager | acceptance | draft |  |
| AC-24 | FR-11 | a project with no active manager | an administrator adds a manager without a reason | it is refused | acceptance | draft |  |
| AC-25 | FR-11 | a project | an administrator adds a manager although one is active, or adds an administrator or an inactive person | it is refused | acceptance | draft |  |
| AC-26 | FR-12 | a project, a member and a non-member | each asks for its contents | the member sees them and the other is refused | acceptance | draft |  |
| AC-27 | FR-12 | a project and an id that does not exist | a non-member asks about, or changes the members of, either | the answer is the same for both | acceptance | draft |  |
| AC-28 | FR-12 | an engineer who is a member | they open the member list | they see its members | acceptance | draft |  |
| AC-29 | FR-13 | a project | it is created | an audit entry says who created it and who its manager is | acceptance | draft |  |
| AC-30 | FR-13; FR-11 | a project | a member is added, changed or removed, or a manager is restored with a reason | each has an entry saying who, what and whom, and the reason for a restore | acceptance | draft |  |
| AC-31 | FR-13 | an administrator | their attempt to change a project's members is refused | an audit entry records the attempt | acceptance | draft |  |
| AC-32 | NFR-1 | any role, and a person who is not a member | each makes a command or read it may not, even if the screen hides it | the server refuses it | acceptance | draft |  |
| AC-33 | NFR-1 | a request with no token, an expired one, or one not from our identity provider | it reaches a protected route | it is refused | acceptance | draft |  |
| AC-34 | NFR-2 | the final deployment design | its data stores and hosting are listed | each is an AWS service | inspection | draft |  |
| AC-35 | NFR-2 | the API | it runs, and its tests are run on PostgreSQL | it uses PostgreSQL and they pass | integration | draft |  |
| AC-36 | NFR-3 | the domain code | its imports are checked, and its tests run with fake adapters | it imports nothing outside itself and the tests pass unchanged | unit | draft | Tests: test_architecture.py, architecture.test.ts, test_service.py. |
| AC-37 | NFR-4 | a rule or a use case, and its code | the history is read | its test came before, or with, the code | inspection | draft |  |
