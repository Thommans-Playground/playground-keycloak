```yaml
id: UC-A4
type: use-case
name: Approve, deactivate and reinstate an account
status: draft
actor: administrator
context: BC-ACCESS
satisfies:
  - id: FR-3
  - id: FR-4
criteria:
  - id: AC-4
  - id: AC-5
  - id: AC-6
  - id: AC-7
parameters:
  - account
  - decision (approve, deactivate or reinstate)
  - reason (for a deactivation)
objects: [OBJ-A1]
rules: []
effects:
  - for a deactivation the person is disabled in Keycloak and their sessions end, for a reinstatement they are enabled again, and for an approval Keycloak is not called
  - the account becomes active or deactivated
  - an audit entry records who, what and why
evolved_from: [MK3 UC-A7]
flow_reviewed: 63dc9f3
```

# Approve, deactivate and reinstate an account

<!-- vbench-uc:begin mirror (generated from the requirements files, do not edit here: change the row, then run sync) -->

<details>
<summary>The requirements and criteria it runs, copied from docs/requirements (2 requirements, 4 criteria). Do not edit.</summary>

## What this serves

**FR-3**: The system shall hold a person it does not know as a pending account, who can see only that it is waiting for approval, until an administrator approves it.

**FR-4**: The system shall let an administrator decide who can use the product: approve a pending account, deactivate an active one with a reason, and reinstate a deactivated one.

## Acceptance criteria it runs

**AC-4** (acceptance, proves FR-3)

- Given a pending account
- When its owner asks for their status, then for anything else
- Then the status says it is waiting, and everything else is refused

**AC-5** (acceptance, proves FR-4)

- Given a pending account
- When an administrator approves it
- Then the person can use the product, with no change made in Keycloak

**AC-6** (acceptance, proves FR-4)

- Given an active account
- When an administrator deactivates it, with a reason
- Then the person cannot sign in at Keycloak, and their next request is refused even with a valid token

**AC-7** (acceptance, proves FR-4)

- Given a deactivated account
- When an administrator reinstates it
- Then the person can use the product again, with their data and memberships, and is enabled in Keycloak

## How it is verified

- acceptance: AC-4, AC-5, AC-6, AC-7

Each criterion is run by a test tagged `Verifies AC-<n>`.

</details>

<!-- vbench-uc:end mirror -->

## Description

An administrator decides who can sign in. A person who registers is pending until an administrator approves them. An administrator can also withdraw access from an active account, with a reason, and give it back later. Keycloak proves who the person is and holds the sign-in. Playground keeps the account record, the reason and the audit entry, and tells Keycloak to disable a person who is deactivated and to enable them again when reinstated. Approving a pending person is a change in Playground only (decision 2, confirmed in decision 8): the API decides who may use the product, and Keycloak only proves who the person is. Nothing is deleted: a deactivated account keeps its data.

## Preconditions

- The administrator has signed in through Keycloak and holds the administrator account role.
- The account exists in Playground and is pending, active or deactivated.

## Main flow

1. The administrator chooses an account. (FR-4)
2. The administrator chooses what to do: approve a pending account, deactivate an active one, or reinstate a deactivated one. (FR-4)
3. For a deactivation, the administrator gives a reason. (FR-4)
4. The system checks that the person asking is an administrator. (FR-4)
5. For a deactivation the system disables the person in Keycloak and ends their sessions. For a reinstatement it enables them again. For an approval it does not call Keycloak. (FR-4, AC-6, AC-7)
6. The system sets the account to active (approved, AC-5) or deactivated (AC-6), or active again (reinstated, AC-7). (FR-4, AC-5, AC-6, AC-7)
7. The system records an audit entry with who, what and why. (FR-4)
8. The person can now use the product, or can no longer sign in and is refused if they still hold a token. (FR-3, FR-4)

## Other flows

- A person who is not an administrator tries to approve an account: it is refused and the account stays pending.
- A pending person makes any request other than asking for their own status: it is refused. They can sign in at Keycloak and hold a token, and they can ask for their own status. (AC-4)
- An administrator deactivates an account without a reason: it is refused and the account stays active.
- An administrator tries to deactivate their own account: it is refused.
- A deactivated person whose token has not yet expired makes a request: it is refused at once, because the account is read on every request, and Keycloak sessions are ended too. (AC-6)
- All data of a deactivated account is kept. (AC-7)

## Postconditions

- The account is active or deactivated. A deactivated person is disabled in Keycloak, and an active one who was deactivated before is enabled again. An approved person's Keycloak account is unchanged.
- An audit entry records who made the change and why.
- No data of the account is removed.

## Open questions

For the product owner to decide.

1. If the Keycloak call fails during a deactivation or a reinstatement, which wins: the account change or the Keycloak change, and is it retried? The API refuses a deactivated person either way, so the safe order for a deactivation looks like our database first, but the owner has not decided it.
2. An evaluation that a deactivated person had running should reach its end. No criterion yet, because evaluations do not exist.

## Slices

- TSK-A4.1: Approve a pending account (AC-5)
- TSK-A4.2: A pending person can sign in but can only ask for their own status (AC-4)
- TSK-A4.3: Deactivate an account with a reason (AC-6)
- TSK-A4.4: Reinstate a deactivated account (AC-7)

## Not in this use case

- Signing in, signing out, refreshing the session and resetting a password. Those are Keycloak's (decision 1).
- Giving or taking away the administrator or auditor role. That is done in Keycloak, never from the browser.
- Adding a person to a project (UC-P2).
