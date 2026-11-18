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
  - for a deactivation our account changes first and then the person is disabled in Keycloak and their sessions end, for a reinstatement the person is enabled in Keycloak first and then our account changes, and for an approval Keycloak is not called
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
5. For a deactivation the system first sets the account to deactivated (AC-6), so the API refuses the person at once, then disables the person in Keycloak and ends their sessions. For a reinstatement it first enables the person in Keycloak, then sets the account to active again (AC-7). For an approval it sets the account to active (AC-5) and does not call Keycloak. (FR-4, AC-5, AC-6, AC-7, decision 10)
6. If a Keycloak call fails, the system keeps the order's safe side and tells the administrator (see other flows). (FR-4, decision 10)
7. The system records an audit entry with who, what and why. (FR-4)
8. The person can now use the product, or can no longer sign in and is refused if they still hold a token. (FR-3, FR-4)

## Other flows

- A person who is not an administrator tries to approve an account: it is refused and the account stays pending.
- A pending person makes any request other than asking for their own status: it is refused. They can sign in at Keycloak and hold a token, and they can ask for their own status. (AC-4)
- An administrator deactivates an account without a reason: it is refused and the account stays active.
- An administrator tries to deactivate their own account: it is refused.
- A deactivated person whose token has not yet expired makes a request: it is refused at once, because the account is read on every request, and Keycloak sessions are ended too. (AC-6)
- All data of a deactivated account is kept. (AC-7)
- The Keycloak call fails during a deactivation: the deactivation stands, because our database already changed and the API refuses the person. The administrator is told that Keycloak was not updated, an audit entry records the half-done change, and the call can be retried. (decision 10)
- The Keycloak call fails during a reinstatement: our account stays deactivated, the administrator is told, and an audit entry records the half-done change. The person stays locked out rather than let in. The call can be retried. (decision 10)
- Retrying: disabling a person who is already disabled in Keycloak, and enabling one who is already enabled, succeed and change nothing, so both Keycloak calls are safe to repeat. (decision 10)

## Postconditions

- The account is active or deactivated. A deactivated person is disabled in Keycloak, and an active one who was deactivated before is enabled again. An approved person's Keycloak account is unchanged.
- If a Keycloak call failed, the account change of a deactivation stands and the account of a reinstatement stays deactivated, until the call is retried.
- An audit entry records who made the change and why. A half-done change leaves an audit entry too.
- No data of the account is removed.

## Open questions

For the product owner to decide.

1. Decided (decision 10): a deactivation changes our database first, then Keycloak, and if Keycloak fails the deactivation stands, the administrator is told and the call can be retried. A reinstatement is the reverse: Keycloak first, then our database, so a failure locks the person out. Both Keycloak calls are safe to repeat.
2. No use case describes an administrator promoting or demoting an account. Which use case should it be?
3. An evaluation that a deactivated person had running should reach its end. No criterion yet, because evaluations do not exist.

## Slices

- TSK-A4.1: Approve a pending account (AC-5)
- TSK-A4.2: A pending person can sign in but can only ask for their own status (AC-4)
- TSK-A4.3: Deactivate an account with a reason (AC-6)
- TSK-A4.4: Reinstate a deactivated account (AC-7)

## Not in this use case

- Signing in, signing out, refreshing the session and resetting a password. Those are Keycloak's (decision 1).
- Giving or taking away the administrator role. Roles live in our database and are changed in Playground by an administrator, with a reason and an audit entry (decision 1 amendment, OBJ-A1). No use case describes it yet (see the open question).
- Adding a person to a project (UC-P2).
