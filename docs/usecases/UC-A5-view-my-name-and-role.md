```yaml
id: UC-A5
type: use-case
name: View my name and role
status: draft
actor: signed-in person
context: BC-ACCESS
satisfies:
  - id: FR-5
criteria:
  - id: AC-8
parameters: []
objects: [OBJ-A1]
rules: []
effects:
  - nothing is changed, except that the copied name and email are refreshed from the token
evolved_from: [MK3 UC-A4]
```

# View my name and role

<!-- vbench-uc:begin mirror (generated from the requirements files, do not edit here: change the row, then run sync) -->

<details>
<summary>The requirements and criteria it runs, copied from docs/requirements (1 requirement, 1 criterion). Do not edit.</summary>

## What this serves

**FR-5**: The system shall show a signed-in person their name and account role.

## Acceptance criteria it runs

**AC-8** (acceptance, proves FR-5)

- Given a signed-in person
- When they open the dashboard
- Then it shows their name and role

## How it is verified

- acceptance: AC-8

Each criterion is run by a test tagged `Verifies AC-<n>`.

</details>

<!-- vbench-uc:end mirror -->

> Study copy. Rewritten from MK3's UC-A4 (view profile) for Keycloak.


## Description

The person sees who the product thinks they are. The name comes from the Keycloak token, and the role and status come from the Playground account. Changing the name, the email or the password is not done here: Keycloak has its own account page for that.

## What changed from MK3

| MK3 UC-A4 | Playground UC-A5 |
|---|---|
| `GET /auth/me` returns the id and email from our user table | `GET /me` returns the account: name, email, role, status |
| Our code could change the profile later | Not ours: Keycloak's account page |
| The user comes from our table | The name and email are copied from the token each time, the role and status come from our table |

This use case is a good one to learn from because it shows the **split in one response**: some fields are Keycloak's, copied in, and some are Playground's. The `/me` answer is allowed for a pending person, so it is the one read that skips the "active account" check (FR-3).

## Preconditions

- The person is signed in.

## Main flow

1. The person opens the dashboard. (FR-5)
2. The web server asks the API for `/me` with the access token. (FR-5)
3. The API checks the token. (NFR-1)
4. The API finds the account by the Keycloak id, and refreshes the name and email if they changed. (FR-5)
5. The API refuses a deactivated account. (FR-5)
6. The API answers with name, email, role and status. (FR-5)
7. The page shows the name and the role. (FR-5, AC-8)

## Other flows

- No valid token: 401, and the person is asked to sign in. (NFR-1)
- The account is pending: the answer is the same, with status pending, and the page shows "Waiting for approval". (AC-4)
- The account is deactivated: 403 "Your account is deactivated." and the dashboard shows that notice. (FR-5)
- The access token has expired: the web server refreshes it first (UC-A6). If Keycloak refuses, the session ends and the person signs in again.
- The person wants to change their password or email: the page links to Keycloak's account page. Nothing here changes them.

## Postconditions

- Nothing is changed, apart from the copied name and email if they differed.

## Overview

The high level picture. The analysis sequence is in [UC-A5-view-my-name-and-role-analysis-sequence.puml](diagrams/UC-A5-view-my-name-and-role-analysis-sequence.puml) and the design sequence, with the routes, use cases, ports and adapters, in [UC-A5-view-my-name-and-role-design-sequence.puml](diagrams/UC-A5-view-my-name-and-role-design-sequence.puml). Both use the step numbers of the main flow.

```mermaid
sequenceDiagram
    actor P as Person
    participant A as API
    P->>A: open dashboard (token)
    A->>A: name from the token
    A->>A: role and status from the account
    A-->>P: name and role
```

## Analysis

### Revision 1

What the person and Playground say to each other, with no route, store, port or token. The diagram is
[UC-A5-view-my-name-and-role-analysis-sequence.puml](diagrams/UC-A5-view-my-name-and-role-analysis-sequence.puml). Not frozen yet.

- A1 (step): The person opens their profile
- A2 (step): Playground checks who the person is
- A3 (step): Playground finds the person's account and refreshes the name and email
- A4 (step): Playground refuses a deactivated account
- A5 (step): Playground shows the name and the role, and the status
- A6 (rule): The name and email are Keycloak's, copied in. The role and status are Playground's
- A7 (rule): A person waiting for approval may see their own profile
- A8 (refusal): A request with no valid proof is refused
- A9 (refusal): A deactivated account is refused
- A10 (object): Account

## Design

The parts that do the work, drawn in [UC-A5-view-my-name-and-role-design-sequence.puml](diagrams/UC-A5-view-my-name-and-role-design-sequence.puml). The class diagram of the API side is [access-design.puml](../domain/diagrams/access-design.puml). The class diagram of the web server side is [bff-design.puml](../domain/diagrams/bff-design.puml).

- D1 (route): The web dashboard, which asks the API for /me (there is no separate profile page)
- D2 (route): The API /me route
- D3 (service): The API TokenVerifier
- D4 (use case): AccessService.account_for
- D5 (port): AccountRepository
- D6 (adapter): SQLAlchemy over PostgreSQL, behind AccountRepository
- D7 (port): BackendApi, on the web server
- D8 (route guard): The API route guard that refuses a deactivated account with 403 `account_deactivated`. It is not a domain rule, and RULE-A4 (deactivation removes nothing) is not it
- D9 (aggregate): Account

## Changes from analysis to design

```
A1 became -> D1, D7
A2 became -> D2, D3
A3 became -> D4, D5, D6
A4 became -> D4, D8
A5 became -> D1, D2
A6 became -> D4, D9
A7 became -> D2
A8 became -> D3
A9 became -> D8
A10 became -> D9
```

## Slices

1. TSK-A5.1: Return the account for /me (AC-8)
2. TSK-A5.2: Show it on the page (AC-8)
