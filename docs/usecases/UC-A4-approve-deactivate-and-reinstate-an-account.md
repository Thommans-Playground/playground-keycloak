```yaml
id: UC-A4
type: use-case
name: Approve, deactivate, reinstate, promote and demote an account
status: draft
actor: administrator
context: BC-ACCESS
satisfies:
  - id: FR-3
  - id: FR-4
  - id: FR-14
criteria:
  - id: AC-4
  - id: AC-5
  - id: AC-6
  - id: AC-7
  - id: AC-49
  - id: AC-50
  - id: AC-51
parameters:
  - account
  - decision (approve, deactivate, reinstate, promote or demote)
  - reason (for every decision except an approval)
objects: [OBJ-A1]
rules: [RULE-A1, RULE-A2, RULE-A3]
effects:
  - for a deactivation our account changes first and then the person is disabled in Keycloak and their sessions end, for a reinstatement the person is enabled in Keycloak first and then our account changes, and for an approval Keycloak is not called
  - for a promotion or a demotion only our account changes, and Keycloak is not called
  - the account becomes active or deactivated, or its role becomes administrator or user
  - an audit entry records who, what and why
evolved_from: [MK3 UC-A7]
flow_reviewed: 63dc9f3
```

# Approve, deactivate, reinstate, promote and demote an account

<!-- vbench-uc:begin mirror (generated from the requirements files, do not edit here: change the row, then run sync) -->

<details>
<summary>The requirements and criteria it runs, copied from docs/requirements (3 requirements, 7 criteria). Do not edit.</summary>

## What this serves

**FR-3**: The system shall hold a person it does not know as a pending account, who can see only that it is waiting for approval, until an administrator approves it.

**FR-4**: The system shall let an administrator decide who can use the product: approve a pending account, deactivate an active one with a reason, and reinstate a deactivated one.

**FR-14**: The system shall let an administrator promote a user to administrator and demote another administrator, with a reason.

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

**AC-49** (acceptance, proves FR-14)

- Given an administrator and a user
- When the administrator promotes the user, with a reason
- Then they are an administrator, and an audit entry says who, whom and why

**AC-50** (acceptance, proves FR-14)

- Given two administrators
- When one demotes the other, with a reason
- Then the other is a user, and an audit entry says who, whom and why

**AC-51** (acceptance, proves FR-14)

- Given the only administrator
- When they try to demote themselves
- Then it is refused and an administrator remains

## How it is verified

- acceptance: AC-4, AC-5, AC-6, AC-7, AC-49, AC-50, AC-51

Each criterion is run by a test tagged `Verifies AC-<n>`.

</details>

<!-- vbench-uc:end mirror -->

## Description

An administrator decides who can sign in and who administers the product. A person who registers is pending until an administrator approves them. An administrator can also withdraw access from an active account, with a reason, and give it back later. Keycloak proves who the person is and holds the sign-in. Playground keeps the account record, the reason and the audit entry, and tells Keycloak to disable a person who is deactivated and to enable them again when reinstated. Approving a pending person is a change in Playground only (decision 2, confirmed in decision 8): the API decides who may use the product, and Keycloak only proves who the person is. Nothing is deleted: a deactivated account keeps its data.

In the alpha there are two account roles, user and administrator (decision 13). An administrator can promote a user to administrator and demote another administrator, always with a reason. The role lives in Playground, so a promotion or a demotion changes our account only, takes effect at the person's next request, and never calls Keycloak. There is always at least one administrator, and an administrator never changes their own role.

## Preconditions

- The administrator has signed in through Keycloak and holds the administrator account role.
- The account exists in Playground and is pending, active or deactivated. To be promoted it is an active user, to be demoted it is an administrator.

## Main flow

1. The administrator chooses an account. (FR-4, FR-14)
2. The administrator chooses what to do: approve a pending account, deactivate an active one, reinstate a deactivated one, promote a user to administrator, or demote an administrator. (FR-4, FR-14)
3. For every choice except an approval, the administrator gives a reason. (FR-4, FR-14)
4. The system checks that the person asking is an administrator. (FR-4, FR-14)
5. For a deactivation the system first sets the account to deactivated (AC-6), so the API refuses the person at once, then disables the person in Keycloak and ends their sessions. For a reinstatement it first enables the person in Keycloak, then sets the account to active again (AC-7). For an approval it sets the account to active (AC-5) and does not call Keycloak. For a promotion it sets the role to administrator (AC-49), and for a demotion it sets the role to user (AC-50), and neither calls Keycloak. (FR-4, FR-14, AC-5, AC-6, AC-7, AC-49, AC-50, decision 10, decision 13)
6. If a Keycloak call fails, the system keeps the order's safe side and tells the administrator (see other flows). (FR-4, decision 10)
7. The system records an audit entry with who, what, whom and why. (FR-4, FR-14, AC-49, AC-50)
8. The person can now use the product, or can no longer sign in and is refused if they still hold a token, or holds the new role from their next request. (FR-3, FR-4, FR-14)

## Other flows

- A person who is not an administrator tries to approve an account: it is refused and the account stays pending.
- A person who is not an administrator tries to promote or demote an account: it is refused and the role stays as it was.
- A pending person makes any request other than asking for their own status: it is refused. They can sign in at Keycloak and hold a token, and they can ask for their own status. (AC-4)
- An administrator deactivates an account without a reason: it is refused and the account stays active.
- An administrator promotes or demotes an account without a reason that says something: it is refused and the role stays as it was.
- An administrator tries to deactivate their own account: it is refused.
- An administrator tries to demote themselves: it is refused, even when another administrator exists. (AC-51)
- An administrator tries to demote the only administrator, or the only active administrator: it is refused, and an administrator remains. When the only administrator tries it on themselves this is the same refusal as the one above. (AC-51)
- An administrator promotes an account that is already an administrator, or demotes one that is not: it is refused and nothing changes.
- An administrator promotes an account that is not active: it is refused and nothing changes. Open: decision 13 does not say whether a pending or deactivated user may be promoted. The built rules allow only an active account.
- A deactivated person whose token has not yet expired makes a request: it is refused at once, because the account is read on every request, and Keycloak sessions are ended too. (AC-6)
- A demoted person whose session is still open makes a request: the account is read on every request, so they are a user from that request and the administrator actions are refused. (AC-50)
- All data of a deactivated account is kept. (AC-7)
- The Keycloak call fails during a deactivation: the deactivation stands, because our database already changed and the API refuses the person. The administrator is told that Keycloak was not updated, an audit entry records the half-done change, and the call can be retried. (decision 10)
- The Keycloak call fails during a reinstatement: our account stays deactivated, the administrator is told, and an audit entry records the half-done change. The person stays locked out rather than let in. The call can be retried. (decision 10)
- Retrying: disabling a person who is already disabled in Keycloak, and enabling one who is already enabled, succeed and change nothing, so both Keycloak calls are safe to repeat. (decision 10)

## Postconditions

- The account is active or deactivated, and its role is user or administrator. A deactivated person is disabled in Keycloak, and an active one who was deactivated before is enabled again. An approved, promoted or demoted person's Keycloak account is unchanged.
- At least one active administrator exists. (AC-51)
- If a Keycloak call failed, the account change of a deactivation stands and the account of a reinstatement stays deactivated, until the call is retried.
- An audit entry records who made the change, to whom, and why. A half-done change leaves an audit entry too.
- No data of the account is removed.

## Open questions

For the product owner to decide.

1. Decided (decision 10): a deactivation changes our database first, then Keycloak, and if Keycloak fails the deactivation stands, the administrator is told and the call can be retried. A reinstatement is the reverse: Keycloak first, then our database, so a failure locks the person out. Both Keycloak calls are safe to repeat.
2. Decided (decision 13): promoting and demoting administrators belongs to this use case, with a reason and an audit entry.
3. An evaluation that a deactivated person had running should reach its end. No criterion yet, because evaluations do not exist.
4. May a pending or deactivated account be promoted? The built rule says only an active account. Decision 13 is silent.
5. A reinstatement needs a reason in RULE-A3 and in the built code, but AC-7 does not mention one.

## Slices

- TSK-A4.1: Approve a pending account (AC-5)
- TSK-A4.2: A pending person can sign in but can only ask for their own status (AC-4)
- TSK-A4.3: Deactivate an account with a reason (AC-6)
- TSK-A4.4: Reinstate a deactivated account (AC-7)
- TSK-A4.5: Promote a user to administrator, with a reason, rules RULE-A3 (AC-49)
- TSK-A4.6: Demote an administrator, with a reason, never oneself and never the last one, rules RULE-A1, RULE-A2 (AC-50, AC-51)

## Overview

The analysis sequence is in [UC-A4-approve-deactivate-and-reinstate-an-account-analysis-sequence.puml](diagrams/UC-A4-approve-deactivate-and-reinstate-an-account-analysis-sequence.puml) and the design sequence, with the routes, ports and adapters, in [UC-A4-approve-deactivate-and-reinstate-an-account-design-sequence.puml](diagrams/UC-A4-approve-deactivate-and-reinstate-an-account-design-sequence.puml). Both use the step numbers of the main flow.

## Analysis

### Revision 1

What the administrator and Playground say to each other, with no route, store, port or token. The diagram is
[UC-A4-approve-deactivate-and-reinstate-an-account-analysis-sequence.puml](diagrams/UC-A4-approve-deactivate-and-reinstate-an-account-analysis-sequence.puml).
Written for decision 13 (promote and demote). Not frozen yet: read it, then freeze it.

- A1 (step): The administrator chooses an account and what to do: approve, deactivate, reinstate, promote or demote
- A2 (step): The administrator gives a reason, except for an approval
- A3 (step): Playground checks that the person asking is an administrator
- A4 (step): Playground changes the account: its status for an approval, a deactivation or a reinstatement, its role for a promotion or a demotion
- A5 (step): Playground has Keycloak disable the person and end their sessions, or enable them again, for a deactivation or a reinstatement
- A6 (step): Playground records who made the change, to whom, and why
- A7 (step): The person's next request is answered by what the account now allows
- A8 (rule): A change other than an approval needs a reason that says something (RULE-A3)
- A9 (rule): An administrator cannot deactivate or demote themselves (RULE-A2)
- A10 (rule): There is always an active administrator (RULE-A1)
- A11 (rule): A change must fit the account: only a pending account is approved, an active one deactivated, a deactivated one reinstated, a user promoted, an administrator demoted
- A12 (rule): A promotion or a demotion changes Playground only, and Keycloak is not called
- A13 (rule): A pending person can only ask for their own status
- A14 (refusal): The person asking is not an administrator
- A15 (refusal): Keycloak cannot be reached during a deactivation or a reinstatement
- A16 (outside system): Keycloak
- A17 (object): Account

## Design

The parts that do the work. The class diagram is [access-design.puml](../domain/diagrams/access-design.puml). The design sequence is [UC-A4-approve-deactivate-and-reinstate-an-account-design-sequence.puml](diagrams/UC-A4-approve-deactivate-and-reinstate-an-account-design-sequence.puml).

**Built:** the API for all five decisions, with the rules, the audit entry and the Keycloak calls, and the administrator accounts page of the web server, which offers promote and demote with a reason. The API's `AccessService.change` already handles promote and demote (the domain rules, the reason and the audit entry), and its tests cover them.

**Planned, not built:** D11, the order of a deactivation that decision 10 asks for. The code today calls Keycloak first and changes nothing if Keycloak fails, which is the reinstatement order. Promote and demote need no change.

- D1 (route): The five routes `POST /accounts/{id}/approve`, `deactivate`, `reinstate`, `promote` and `demote`, with `GET /accounts` and `GET /audit`, each behind the administrator guard
- D2 (guard): The chain of checks on every request: token, account, deactivated refused, pending refused, administrator only
- D3 (use case): AccessService.change
- D4 (domain rule): decide() and clean_reason(): the transitions, no self change, the last administrator, the reason
- D5 (aggregate): Account, with its role and status
- D6 (port): AccountRepository, with the count of active administrators
- D7 (port): AuditLog
- D8 (port): IdentityProvider of the API (disable, enable, end sessions), not called for approve, promote or demote
- D9 (adapter): SqlAdapters on PostgreSQL (RDS on AWS) and KeycloakAdmin
- D10 (mapping): Domain errors answered as HTTP statuses in main.py (422 reason, 409 last administrator and wrong state, a self change refused, 404 no account)
- D11 (use case): Planned: a deactivation changes our account first, then Keycloak (decision 10)
- D12 (web): The administrator accounts page and its table, with the reason dialog, calling the API through the BackendApi port

## Changes from analysis to design

```
A1 became -> D1, D12
A2 became -> D1, D4, D12
A3 became -> D2
A4 became -> D3, D4, D5, D6
A5 became -> D3, D8, D9, D11
A6 became -> D3, D7, D9
A7 became -> D2, D5
A8 became -> D4
A9 became -> D4
A10 became -> D4, D6
A11 became -> D4
A12 became -> D3
A13 became -> D2
A14 became -> D2, D10
A15 became -> D3, D10
A16 became -> D8, D9
A17 became -> D5
```

## Not in this use case

- Signing in, signing out, refreshing the session and resetting a password. Those are Keycloak's (decision 1).
- Roles other than user and administrator, and project roles. They are parked for release R2 (decision 13).
- Adding a person to a project (UC-P2).
