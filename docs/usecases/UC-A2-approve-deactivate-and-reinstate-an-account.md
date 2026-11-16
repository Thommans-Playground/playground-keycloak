```yaml
id: UC-A2
type: use-case
name: Approve, deactivate and reinstate an account
status: draft
actor: administrator
context: BC-ACCESS
satisfies:
  - id: FR-1
    reviewed: 7a2439b
  - id: FR-2
    reviewed: d044c3b
  - id: FR-3
    reviewed: 92a82ff
  - id: FR-4
    reviewed: 1f04af2
criteria:
  - id: AC-1
    reviewed: b4056f3
  - id: AC-2
    reviewed: 98066c3
  - id: AC-3
    reviewed: d262151
  - id: AC-4
    reviewed: 429ab1e
  - id: AC-5
    reviewed: edba5a5
  - id: AC-6
    reviewed: 1097530
  - id: AC-7
    reviewed: eb09f88
  - id: AC-75
  - id: AC-84
  - id: AC-85
  - id: AC-86
parameters:
  - account
  - decision (approve, deactivate or reinstate)
  - reason (for a deactivation)
objects: [OBJ-A1]
rules: []
effects:
  - the person is enabled or disabled in Keycloak
  - the account becomes active or deactivated
  - an audit entry records who, what and why
evolved_from: [MK3 UC-A7]
flow_reviewed: 63dc9f3
```

# Approve, deactivate and reinstate an account

<!-- vbench-uc:begin mirror (generated from the requirements files, do not edit here: change the row, then run sync) -->

## What this serves

**FR-1**: The system shall let an administrator approve a pending account so that the person can sign in.

**FR-2**: The system shall let a person with a pending account see only that their account is waiting for approval, and refuse everything else.

**FR-3**: The system shall let an administrator deactivate an account, with a reason.

**FR-4**: The system shall let an administrator reinstate a deactivated account.

## Acceptance criteria it runs

**AC-1** (acceptance, proves FR-1)

- Given a pending account
- When an administrator approves it
- Then the account is active and the person can sign in

**AC-2** (acceptance, proves FR-1)

- Given a pending account and a person who is not an administrator
- When that person tries to approve it
- Then it is refused and the account stays pending

**AC-3** (acceptance, proves FR-2)

- Given a pending account
- When its owner makes any request other than asking for their own status
- Then it is refused

**AC-4** (acceptance, proves FR-3)

- Given an active account
- When an administrator deactivates it and gives a reason
- Then the account is deactivated and its owner can no longer sign in

**AC-5** (acceptance, proves FR-3)

- Given an active account
- When an administrator deactivates it without a reason
- Then it is refused and the account stays active

**AC-6** (unit, proves FR-3)

- Given an administrator's own account
- When that administrator tries to deactivate it
- Then it is refused

**AC-7** (acceptance, proves FR-4)

- Given a deactivated account
- When an administrator reinstates it
- Then the account is active and its owner can sign in again

**AC-75** (acceptance, proves FR-2)

- Given a pending account
- When its owner asks for their own status
- Then it says the account is waiting for approval

**AC-84** (acceptance, proves FR-3)

- Given an active account whose owner holds a valid token
- When an administrator deactivates it
- Then the owner's next request is refused

**AC-85** (acceptance, proves FR-3)

- Given a deactivated account
- When its records are inspected
- Then all of its data is still there

**AC-86** (future, proves FR-3)

- Given a deactivated person with an evaluation running
- When time passes
- Then the evaluation reaches its end

## How it is verified

- acceptance: AC-1, AC-2, AC-3, AC-4, AC-5, AC-7, AC-75, AC-84, AC-85
- unit: AC-6
- future: AC-86

Each criterion is run by a test tagged `Verifies AC-<n>`.

<!-- vbench-uc:end mirror -->

## Description

An administrator decides who can sign in. A person who registers is pending until an administrator approves them. An administrator can also withdraw access from an active account, with a reason, and give it back later. Keycloak proves who the person is and holds the sign-in. Playground keeps the account record, the reason and the audit entry, and tells Keycloak to enable or disable the person. Nothing is deleted: a deactivated account keeps its data.

## Preconditions

- The administrator has signed in through Keycloak and holds the administrator account role.
- The account exists in Playground and is pending, active or deactivated.

## Main flow

1. The administrator chooses an account. (FR-1, FR-3, FR-4)
2. The administrator chooses what to do: approve a pending account, deactivate an active one, or reinstate a deactivated one. (FR-1, FR-3, FR-4)
3. For a deactivation, the administrator gives a reason. (FR-3)
4. The system checks that the person asking is an administrator. (FR-1)
5. The system enables the person in Keycloak for an approval or a reinstatement, and disables them for a deactivation. (FR-1, FR-3, FR-4)
6. The system sets the account to active (approved, AC-1) or deactivated (AC-4), or active again (reinstated, AC-7). (FR-1, FR-3, FR-4, AC-1, AC-4, AC-7)
7. The system records an audit entry with who, what and why. (FR-3)
8. The person can now sign in, or can no longer sign in. (FR-1, FR-2, FR-3, FR-4)

## Other flows

- A person who is not an administrator tries to approve an account: it is refused and the account stays pending. (AC-2)
- A pending person makes any request other than asking for their own status: it is refused. They can sign in at Keycloak and hold a token, and they can ask for their own status. (AC-3, AC-75)
- An administrator deactivates an account without a reason: it is refused and the account stays active. (AC-5)
- An administrator tries to deactivate their own account: it is refused. (AC-6)
- A deactivated person whose token has not yet expired makes a request: it is refused at once, because the account is read on every request, and Keycloak sessions are ended too. (AC-84)
- All data of a deactivated account is kept. (AC-85)
- An evaluation that a deactivated person had running reaches its end. (AC-86, future)

## Postconditions

- The account is active or deactivated, and the person is enabled or disabled in Keycloak to match.
- An audit entry records who made the change and why.
- No data of the account is removed.

## Slices

- TSK-A2.1: Approve a pending account (AC-1, AC-2)
- TSK-A2.2: A pending person cannot sign in (AC-3)
- TSK-A2.3: Deactivate an account with a reason (AC-4, AC-5, AC-6)
- TSK-A2.4: Reinstate a deactivated account (AC-7)

## Not in this use case

- Signing in, signing out, refreshing the session and resetting a password. Those are Keycloak's (decision 23).
- Giving or taking away the administrator or auditor role. That is done in Keycloak, never from the browser.
- Adding a person to a project (UC-A3).
