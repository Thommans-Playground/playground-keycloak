# Acceptance criteria

<!-- Read and written by req_tool.py. Each row is one scenario: Given, When, Then. -->

| ID | Proves | Given | When | Then | Level | Status | Notes |
|---|---|---|---|---|---|---|---|
| AC-1 | FR-1 | an active account | its person signs in through the identity provider, then asks for their own account | they have a session, and the answer shows their account | acceptance | draft |  |
| AC-2 | FR-2 | a signed-in person | they sign out | their session stops working, and starting a sign in shows the identity provider's login page | acceptance | draft |  |
| AC-3 | FR-3 | a person the system does not know | they make a request, then another | one pending account exists for them | acceptance | draft |  |
| AC-4 | FR-3 | a pending account | its owner asks for their status, then makes any other request | the status says it is waiting, and every other route is refused | acceptance | draft |  |
| AC-5 | FR-4 | a pending account | an administrator approves it | their next request shows an active account and their own page, not the waiting page, and nothing was changed in Keycloak | acceptance | draft |  |
| AC-6 | FR-4 | an active account | an administrator deactivates it, with a reason | the person cannot sign in at Keycloak, and their next request is refused even with a valid token | acceptance | draft |  |
| AC-7 | FR-4 | a deactivated account | an administrator reinstates it, with a reason | the person can use the product again, with their data and memberships, and is enabled in Keycloak | acceptance | draft |  |
| AC-8 | FR-5 | a signed-in person | they open the dashboard | it shows their name and role | acceptance | draft |  |
| AC-9 | FR-7 | an administrator and an active account | they create a project naming that account as a first member | the project exists and that person is a member | acceptance | draft |  |
| AC-10 | FR-7 | an administrator | they create a project naming themselves as a first member | it exists and they are a member | acceptance | draft |  |
| AC-11 | FR-7 | a user who is not an administrator | they try to create a project | it is refused | acceptance | draft |  |
| AC-12 | FR-7 | a project name that is empty, only spaces, or over 100 characters | a project is created with it | it is refused | acceptance | draft |  |
| AC-13 | FR-7 | an administrator | they create a project naming a first member who is not active or does not exist | it is refused, with one answer for an account that cannot be a member | acceptance | draft |  |
| AC-14 | FR-8 | a project an administrator created for someone else | that administrator asks for its contents | it is refused | acceptance | draft | Parked with FR-8 by decision 13. |
| AC-15 | FR-8 | an administrator | they add themselves to a project, or name themselves its manager | it is refused and they are not a member | acceptance | draft | Parked with FR-8 by decision 13. |
| AC-16 | FR-8 | an administrator who is not a member of a project | they list the projects | they see its name and members, never its contents | acceptance | draft | Parked with FR-8 by decision 13. |
| AC-17 | FR-9 | an administrator and an active account | the administrator adds that person to a project | they are a member | acceptance | draft |  |
| AC-18 | FR-9 | an administrator and an account that is pending, deactivated or unknown | the administrator adds it | it is refused, with one answer for all three | acceptance | draft |  |
| AC-19 | FR-9 | an engineer in a project | their manager makes them a manager | they are a manager of the project | acceptance | retired | Retired by decision 13: no project roles, and an administrator is always allowed. |
| AC-20 | FR-9 | a member of a project | an administrator removes them | they are out, and their next request gets the same answer as for a missing project | acceptance | draft |  |
| AC-21 | FR-10 | a project with one active manager | anyone removes or demotes that manager | it is refused | unit | draft | Parked with FR-10 by decision 13. |
| AC-22 | FR-9; FR-10 | a project with two active managers | one of them removes themselves | it is allowed and the other remains | unit | draft | Parked with FR-10 by decision 13. |
| AC-23 | FR-11 | a project with no active manager, and an active person who is not an administrator | an administrator adds that person as manager, with a reason | they are a manager | acceptance | draft | Parked with FR-11 by decision 13. |
| AC-24 | FR-11 | a project with no active manager | an administrator adds a manager without a reason | it is refused | acceptance | draft | Parked with FR-11 by decision 13. |
| AC-25 | FR-11 | a project | an administrator adds a manager although one is active, or adds an administrator or an inactive person | it is refused | acceptance | draft | Parked with FR-11 by decision 13. |
| AC-26 | FR-12 | a project, a member, an administrator and a user who is neither | each asks for its contents | the member and the administrator see them and the other is refused | acceptance | draft |  |
| AC-27 | FR-12 | a project and an id that does not exist | a person who is neither a member nor an administrator asks about, or changes the members of, either | the answer is the same for both | acceptance | draft |  |
| AC-28 | FR-12 | a member of a project | they open the member list | they see its members | acceptance | draft |  |
| AC-29 | FR-13 | a project | it is created | an audit entry says who created it and who its first members are | acceptance | draft |  |
| AC-30 | FR-13 | a project | a member is added or removed | each has an entry saying who, what and whom | acceptance | draft |  |
| AC-31 | FR-13 | an administrator | their attempt to change a project's members is refused | an audit entry records the attempt | acceptance | retired | Retired by decision 13: no project roles, and an administrator is always allowed. |
| AC-32 | NFR-1 | any role, and a person who is not a member | each makes a command or read it may not, even if the screen hides it | the server refuses it | acceptance | draft |  |
| AC-33 | NFR-1 | a request with no token, an expired one, one from another issuer, one made for another audience, or one signed with an algorithm we do not allow | it reaches a protected route | it is answered 401, and no account or audit entry is made | acceptance | draft |  |
| AC-34 | NFR-2 | the final deployment design | its data stores and hosting are listed | each is an AWS service | inspection | draft |  |
| AC-35 | NFR-2 | the API | it runs, and its tests are run on PostgreSQL | it uses PostgreSQL and they pass | integration | draft |  |
| AC-36 | NFR-3 | the domain code | its imports are checked, and its tests run with fake adapters | it imports nothing outside itself and the tests pass unchanged | unit | draft | Tests: test_architecture.py, architecture.test.ts, test_service.py. |
| AC-37 | NFR-4 | a rule or a use case, and its code | the history is read | its test came before, or with, the code | inspection | draft |  |
| AC-38 | FR-1 | a sign in that was never started, was already used, or has expired | the identity provider sends the person back for it | no session is made, and the person is asked to sign in again | acceptance | draft |  |
| AC-39 | FR-1 | a person who cancels at the identity provider, or a sign in whose proof does not check out | they are sent back | no session is made, and they are told the sign in did not work | acceptance | draft |  |
| AC-40 | FR-1 | a sign in whose return address points to another site | the person signs in | they land on a page of ours, never on the other site | acceptance | draft |  |
| AC-41 | FR-1 | a signed-in person | the browser's cookies and storage are inspected | they hold the session id and no token | acceptance | draft |  |
| AC-42 | FR-1 | a sign in finished in a browser that did not start it | it reaches the system | it is refused and no session is made | acceptance | draft |  |
| AC-43 | FR-1 | a browser that already holds a session | they sign in again | the earlier session of this browser no longer works | acceptance | draft | R2 hardening: deferred by decision 13. |
| AC-44 | FR-1 | an identity provider that cannot be reached | a person asks to sign in | they are told sign in is not available, and no session is made | acceptance | draft |  |
| AC-45 | FR-4 | a deactivated account whose person still signs in, for example re-enabled in Keycloak by hand | they sign in | they see that the account is deactivated, and both their session and Keycloak's end | acceptance | draft | R2 hardening: deferred by decision 13. |
| AC-46 | FR-1 | a sign in started in two tabs of one browser | the older one finishes | it is refused, and the newer one can still finish | acceptance | draft | R2 hardening: deferred by decision 13. |
| AC-47 | FR-3 | a pending account | its person signs in | they land on the waiting page | acceptance | draft |  |
| AC-48 | NFR-5 | a refused sign in, a refused request, and a session that starts and ends | each happens | each writes one log line, and none holds a token or a code | acceptance | draft | Alpha, by decision 17 (deferred by decision 13, now brought back with NFR-5). |
| AC-49 | FR-14 | an administrator and a user | the administrator promotes the user, with a reason | they are an administrator, and an audit entry says who, whom and why | acceptance | draft |  |
| AC-50 | FR-14 | two administrators | one demotes the other, with a reason | the other is a user, and an audit entry says who, whom and why | acceptance | draft |  |
| AC-51 | FR-14 | the only administrator | they try to demote themselves | it is refused and an administrator remains | acceptance | draft |  |
| AC-52 | FR-15 | a signed-in person whose access token is about to expire | they make a request | the token is refreshed and the request succeeds | acceptance | draft |  |
| AC-53 | FR-15 | a signed-in person whose access token is about to expire | two requests arrive at the same moment | only one refresh is sent to the identity provider | acceptance | draft |  |
| AC-54 | FR-15 | a signed-in person whose refresh is refused by the identity provider | they make a request | their session ends and they must sign in again | acceptance | draft |  |
| AC-55 | FR-16 | an administrator, a user who is a member of one project, and several projects | each lists projects | the user sees only their own project and the administrator sees all | acceptance | draft |  |
| AC-56 | FR-17 | an account change and a project change | an administrator opens the audit trail | both entries are there, with who, what, whom and the reason where one was asked | acceptance | draft |  |
| AC-57 | FR-4 | a deactivated account | an administrator reinstates it without a reason | it is refused and the account stays deactivated | acceptance | draft |  |
| AC-58 | FR-4 | an active account and an identity provider that cannot be reached | an administrator deactivates it, with a reason | the account is deactivated, the person's next request is refused, and the administrator is told Keycloak was not updated | acceptance | draft |  |
| AC-59 | FR-4 | a deactivated account and an identity provider that cannot be reached | an administrator reinstates it, with a reason | the account stays deactivated and the administrator is told | acceptance | draft |  |
| AC-60 | FR-9 | a member of a project who is not an administrator | they try to add or remove a member | it is refused | acceptance | draft |  |
| AC-61 | FR-3 | an active administrator exists, and a new person whose email is the setup email, verified | they make their first request | they get a pending account, not an administrator account | acceptance | draft |  |
| AC-62 | FR-14 | two administrators | each demotes the other at the same moment | one is refused and an administrator remains | acceptance | draft |  |
| AC-63 | FR-4 | a person who is not an active administrator: an ordinary user, a pending account or a deactivated account | they try to approve, deactivate, reinstate, promote or demote an account | each is refused and the account stays as it was | acceptance | draft |  |
| AC-64 | FR-4 | an administrator | they deactivate, promote or demote an account without a reason | it is refused and the account stays as it was | acceptance | draft |  |
| AC-65 | FR-4 | an administrator | they try to deactivate their own account, or the last active administrator | it is refused | acceptance | draft |  |
| AC-66 | FR-4 | an account in the wrong state | an administrator approves a non-pending one, promotes a non-user, demotes a non-administrator or reinstates a non-deactivated one | it is refused | unit | draft |  |
| AC-67 | FR-4 | a deactivated account whose person holds a valid token | they open the dashboard | the request is refused and the page says the account is deactivated | acceptance | draft |  |
| AC-68 | FR-17 | a user who is not an administrator | they ask for the audit trail | it is refused | acceptance | draft |  |
| AC-69 | FR-17 | no account or project change yet | an administrator opens the audit trail | it is empty and is not an error | acceptance | draft |  |
| AC-70 | FR-17 | a person who was renamed after a change they made | an administrator opens the audit trail | the entry still shows the name they had at the time | acceptance | draft |  |
| AC-71 | FR-2 | a signed-in person | a page on another site sends a GET to the sign out address | nothing happens, and their session still works | acceptance | draft |  |
| AC-72 | FR-2 | a signed-in person | they sign out | they end on our home page, not on an error page of the identity provider | acceptance | draft |  |
| AC-73 | FR-3 | a pending account whose email another account already has | an administrator lists the accounts | it is marked with a warning that shows the other account, and approving it is still the administrator's decision | acceptance | draft |  |
| AC-74 | FR-3 | no active administrator exists, and a new person whose email is the setup email, verified | they make their first request | they get an active administrator account | acceptance | draft |  |
| AC-75 | FR-3 | a new person whose email is the setup email, not verified | they make their first request | they get a pending account, like anyone else | acceptance | draft |  |
| AC-76 | FR-4 | an administrator | they approve an account that does not exist, or one that is not pending | it is refused with a clear answer and nothing changes | acceptance | draft |  |
