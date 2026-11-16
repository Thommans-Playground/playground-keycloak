```yaml
id: UC-A12
type: use-case
name: Register and wait for approval
status: draft
actor: new person
context: BC-ACCESS
satisfies:
  - id: FR-123
  - id: FR-2
criteria:
  - id: AC-3
  - id: AC-75
  - id: AC-76
  - id: AC-77
parameters:
  - name, email and password (given to Keycloak, not to us)
objects: [OBJ-A1]
rules: [RULE-A1]
effects:
  - a user exists in Keycloak
  - a pending account exists in the API database, made on the person's first request
  - an audit entry records the registration
evolved_from: [MK3 UC-A5]
```

# Register and wait for approval

<!-- vbench-uc:begin mirror (generated from the requirements files, do not edit here: change the row, then run sync) -->

## What this serves

**FR-123**: The system shall create a pending account the first time a person it does not know reaches it through the identity provider.

**FR-2**: The system shall let a person with a pending account see only that their account is waiting for approval, and refuse everything else.

## Acceptance criteria it runs

**AC-3** (acceptance, proves FR-2)

- Given a pending account
- When its owner makes any request other than asking for their own status
- Then it is refused

**AC-75** (acceptance, proves FR-2)

- Given a pending account
- When its owner asks for their own status
- Then it says the account is waiting for approval

**AC-76** (acceptance, proves FR-123)

- Given a person the system does not know, signed in through the identity provider
- When they make their first request
- Then a pending account exists for them

**AC-77** (acceptance, proves FR-123)

- Given a person who already has an account
- When they make another request
- Then no second account is created

## How it is verified

- acceptance: AC-3, AC-75, AC-76, AC-77

Each criterion is run by a test tagged `Verifies AC-<n>`.

<!-- vbench-uc:end mirror -->

> Study copy. Rewritten from MK3's UC-A5 (sign up) for Keycloak.


## Description

This is MK3's sign-up, split in two. **Registering** (a name, an email, a password) is Keycloak's. **Becoming known to Playground** is ours, and it is not a sign-up form at all: the account is made quietly the first time the API sees a new person's token. The person lands as **pending** and can do one thing, ask for their own status. An administrator approves them in UC-A2.

## What changed from MK3

| MK3 UC-A5 | Playground UC-A12 |
|---|---|
| Our signup form, password rules, bcrypt, duplicate email check | Keycloak's registration page, its password policy and its duplicate check |
| Signup creates the user and signs the person in at once | Registration creates a Keycloak user. Signing in is separate |
| The user row holds the password hash | Our account holds no password: only the Keycloak id (`identity`), name, email, role, status |
| An email that is already used gives an error | Keycloak handles it. We link by the Keycloak id, never by email |
| Status starts as pending, and an administrator approves | The same. The account is made on first sight, not at signup |
| First administrator: a command on the server | Email in `BOOTSTRAP_ADMIN_EMAILS` and verified at Keycloak |

New in the design language: **lazy provisioning**. The person exists in two places, and the second record is made when first needed, not when the person registers. So there is no moment that has to create both, which is exactly the "what if only one succeeds" worry in the Access notes. The cost: a person who registers and never comes back has a Keycloak user and no account, which is harmless.

## Preconditions

- The person has no Keycloak user (registration), or has one and no account (first request).

## Main flow

1. The person asks to create an account. The system sends them to Keycloak's registration page. (FR-123)
2. The person gives a name, an email and a password to Keycloak. Keycloak creates the user and signs them in. (FR-123)
3. The person comes back and the system makes a session, as in UC-A10. (FR-123)
4. The person's first request reaches the API with a valid token. (FR-123)
5. The API looks for an account with the token's Keycloak id and finds none. (AC-76)
6. The API creates an account with role user and status pending, with the name and email from the token. (FR-123, AC-76)
7. The API records an audit entry "register" with no administrator. (FR-123)
8. The API refuses everything except "show me my own status". (FR-2)
9. The person sees "Waiting for approval". (FR-2, AC-75)

## Other flows

- The person already has an account: nothing is created, and the name and email are refreshed from the token. (AC-77)
- The person's email is in `BOOTSTRAP_ADMIN_EMAILS` and Keycloak says it is verified: the account is created active, with role administrator, and the audit entry says it came from setup. (RULE-A1)
- The email is in `BOOTSTRAP_ADMIN_EMAILS` but not verified: the account is created pending, as for anyone else, so someone cannot claim the first administrator by registering with an unverified address.
- A pending person asks for anything other than their own status: the API answers 403 "waiting for approval". (AC-3)
- The person's name or email changed in Keycloak: the account is updated on the next request. The link stays the Keycloak id.
- Two first requests arrive at the same moment: only one account may exist. Open: the account table needs a unique identity, and the second insert must be treated as "found". (AC-77)
- Open: Keycloak's registration page does not check the email by default. Whether to require it, and whether to limit how fast registrations can come from one place, is still undecided.

## Postconditions

- A Keycloak user exists, and one account exists for its id, pending (or active for the first administrator).
- No password is held by Playground.

## Overview

The high level picture. The detailed sequence, with step numbers that match the main flow, is in [UC-A12-register-and-wait-for-approval-sequence.puml](diagrams/UC-A12-register-and-wait-for-approval-sequence.puml).

```mermaid
sequenceDiagram
    actor P as Person
    participant K as Keycloak
    participant A as API
    P->>K: register
    P->>A: first request (token)
    A->>A: no account yet: make a pending one
    A-->>P: waiting for approval
```

## Slices

1. TSK-A12.1: Create the account on first sight, rules RULE-A1 (AC-76, AC-77)
2. TSK-A12.2: Refuse everything but the person's own status while pending (AC-3, AC-75)
