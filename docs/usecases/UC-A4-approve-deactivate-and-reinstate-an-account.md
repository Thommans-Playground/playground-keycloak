```yaml
id: UC-A4
type: use-case
name: Approve, deactivate, reinstate, promote and demote an account
status: draft
actor: administrator
context: BC-ACCESS
satisfies:
  - id: FR-4
  - id: FR-14
criteria:
  - id: AC-5
  - id: AC-6
  - id: AC-7
  - id: AC-49
  - id: AC-50
  - id: AC-51
  - id: AC-57
  - id: AC-58
  - id: AC-59
  - id: AC-62
  - id: AC-63
  - id: AC-64
  - id: AC-65
  - id: AC-66
  - id: AC-67
  - id: AC-76
  - id: AC-77
parameters:
  - account
  - decision (approve, deactivate, reinstate, promote or demote)
  - reason (for every decision except an approval)
objects: [OBJ-A1]
rules: [RULE-A1, RULE-A2, RULE-A3]
effects:
  - for a deactivation our database changes first and then the person is disabled in Keycloak and their sessions end, for a reinstatement the person is enabled in Keycloak first and then our database changes, and for an approval Keycloak is not called
  - for a promotion or a demotion only our account changes, and Keycloak is not called
  - the account becomes active or deactivated, or its role becomes administrator or user
  - an audit entry records who, what and why, and goes to the Audit context (BC-AUDIT) through the AuditLog port
evolved_from: [MK3 UC-A7]
flow_reviewed: 63dc9f3
```

# Approve, deactivate, reinstate, promote and demote an account

<!-- vbench-uc:begin mirror (generated from the requirements files, do not edit here: change the row, then run sync) -->

<details>
<summary>The requirements and criteria it runs, copied from docs/requirements (2 requirements, 17 criteria). Do not edit.</summary>

## What this serves

**FR-4**: The system shall let an administrator decide who can use the product: approve a pending account, deactivate an active one with a reason, and reinstate a deactivated one with a reason.

**FR-14**: The system shall let an administrator promote a user to administrator and demote another administrator, with a reason.

## Acceptance criteria it runs

**AC-5** (acceptance, proves FR-4)

- Given a pending account
- When an administrator approves it
- Then their next request shows an active account and their own page, not the waiting page, and nothing was changed in Keycloak

**AC-6** (acceptance, proves FR-4)

- Given an active account
- When an administrator deactivates it, with a reason
- Then the person cannot sign in at Keycloak, and their next request is refused even with a valid token

**AC-7** (acceptance, proves FR-4)

- Given a deactivated account
- When an administrator reinstates it, with a reason
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

**AC-57** (acceptance, proves FR-4)

- Given a deactivated account
- When an administrator reinstates it without a reason
- Then it is refused and the account stays deactivated

**AC-58** (acceptance, proves FR-4)

- Given an active account and an identity provider that cannot be reached
- When an administrator deactivates it, with a reason
- Then the account is deactivated, the person's next request is refused, and the administrator gets a success that says Keycloak was not updated and the call can be repeated

**AC-59** (acceptance, proves FR-4)

- Given a deactivated account and an identity provider that cannot be reached
- When an administrator reinstates it, with a reason
- Then the account stays deactivated and the administrator is told

**AC-62** (acceptance, proves FR-14)

- Given two administrators
- When each demotes the other at the same moment
- Then one is refused and an administrator remains (proven on PostgreSQL)

**AC-63** (acceptance, proves FR-4)

- Given a person who is not an active administrator: an ordinary user, a pending account or a deactivated account
- When they try to approve, deactivate, reinstate, promote or demote an account
- Then each is refused and the account stays as it was

**AC-64** (acceptance, proves FR-4)

- Given an administrator
- When they deactivate, promote or demote an account without a reason
- Then it is refused and the account stays as it was

**AC-65** (acceptance, proves FR-4)

- Given an administrator
- When they try to deactivate their own account, or the last active administrator
- Then it is refused

**AC-66** (unit, proves FR-4)

- Given an account in the wrong state
- When an administrator approves a non-pending one, promotes a non-user, demotes a non-administrator or reinstates a non-deactivated one
- Then it is refused

**AC-67** (acceptance, proves FR-4)

- Given a deactivated account whose person holds a valid token
- When they open the dashboard
- Then the request is refused and the page says the account is deactivated

**AC-76** (acceptance, proves FR-4)

- Given an administrator
- When they approve an account that does not exist, or one that is not pending
- Then it is refused with a clear answer and nothing changes

**AC-77** (acceptance, proves FR-4)

- Given a deactivated account whose Keycloak user is still enabled
- When an administrator deactivates it again, with a reason
- Then only the Keycloak calls are sent again, our account does not change, and the administrator is told whether Keycloak was updated

## How it is verified

- acceptance: AC-5, AC-6, AC-7, AC-49, AC-50, AC-51, AC-57, AC-58, AC-59, AC-62, AC-63, AC-64, AC-65, AC-67, AC-76, AC-77
- unit: AC-66

Each criterion is run by a test tagged `Verifies AC-<n>`.

</details>

<!-- vbench-uc:end mirror -->

## Description

An administrator decides who can sign in and who administers the product. A person who registers is pending until an administrator approves them. An administrator can also withdraw access from an active account, with a reason, and give it back later. Keycloak proves who the person is and holds the sign-in. Playground keeps the account record and the reason, sends the audit entry to the Audit context (BC-AUDIT), and tells Keycloak to disable a person who is deactivated and to enable them again when reinstated. Approving a pending person is a change in Playground only (decision 2, confirmed in decision 8): the API decides who may use the product, and Keycloak only proves who the person is. Nothing is deleted: a deactivated account keeps its data. A pending person's own status request is UC-A3's, not this use case's.

Every change except an approval needs a reason, a reinstatement included (decision 14). A deactivation changes our database first, so the API refuses the person at once, and then Keycloak (decision 10, decision 14). A reinstatement is the reverse, Keycloak first and then our database, so a failure leaves the person deactivated.

In the alpha there are two account roles, user and administrator (decision 13). An administrator can promote a user to administrator and demote another administrator, always with a reason. The role lives in Playground, so a promotion or a demotion changes our account only, takes effect at the person's next request, and never calls Keycloak. There is always at least one administrator, and an administrator never changes their own role. The check that an administrator remains and the change itself are one step, so two administrators acting at the same moment cannot leave none (decision 14).

## Preconditions

- The administrator has signed in through Keycloak and holds the administrator account role.
- The account exists in Playground and is pending, active or deactivated. To be promoted it is an active user, to be demoted it is an administrator. The Audit context (BC-AUDIT) is there to take the entry.

## Main flow

1. The administrator chooses an account. (FR-4, FR-14)
2. The administrator chooses what to do: approve a pending account, deactivate an active one, reinstate a deactivated one, promote a user to administrator, or demote an administrator. (FR-4, FR-14)
3. For every choice except an approval, the administrator gives a reason: a deactivation, a reinstatement, a promotion and a demotion all need one. (FR-4, FR-14, AC-57)
4. The system checks that the person asking is an administrator. (FR-4, FR-14)
5. The system checks the rules and makes the change as one step, so that the check that an administrator remains and the change cannot be split by a second administrator acting at the same moment (a lock on the active administrators, ADR 0009). (FR-14, AC-51, AC-62, decision 14)
6. For a deactivation the system first sets the account to deactivated in our database (AC-6), and commits it with its audit entry, so the API refuses the person at once, then disables the person in Keycloak and ends their sessions. For a reinstatement it first enables the person in Keycloak, then sets the account to active again in our database (AC-7). For an approval it sets the account to active (AC-5) and does not call Keycloak. For a promotion it sets the role to administrator (AC-49), and for a demotion it sets the role to user (AC-50), and neither calls Keycloak. (FR-4, FR-14, AC-5, AC-6, AC-7, AC-49, AC-50, decision 10, decision 13, decision 14)
7. If a Keycloak call fails, the system keeps the safe side of the order, answers with a success that says "Keycloak was not updated" and records that outcome on the one audit entry (see other flows). (FR-4, AC-58, AC-59, decisions 14 and 18)
8. The system sends the audit entry, with who, what, whom and why, to the Audit context (BC-AUDIT) through the AuditLog port. (FR-4, FR-14, AC-49, AC-50)
9. The person can now use the product, or can no longer sign in and is refused if they still hold a token, or holds the new role from their next request. (FR-3, FR-4, FR-14)

## Other flows

- A person who is not an administrator tries to approve an account: it is refused and the account stays pending.
- A person who is not an administrator tries to promote or demote an account: it is refused and the role stays as it was.
- A person who is not an administrator (a user, a pending person, a deactivated person) tries any account command: it is refused and nothing changes. A pending person's own status request is UC-A3's, not this use case's.
- An administrator deactivates an account without a reason: it is refused and the account stays active.
- An administrator reinstates an account without a reason that says something: it is refused and the account stays deactivated. (AC-57)
- An administrator promotes or demotes an account without a reason that says something: it is refused and the role stays as it was.
- An administrator tries to deactivate their own account: it is refused.
- An administrator tries to demote themselves: it is refused, even when another administrator exists. (AC-51)
- An administrator tries to demote the only administrator, or the only active administrator: it is refused, and an administrator remains. When the only administrator tries it on themselves this is the same refusal as the one above. (AC-51)
- An administrator promotes an account that is already an administrator, or demotes one that is not: it is refused and nothing changes.
- An administrator promotes an account that is not active (pending or deactivated): it is refused and nothing changes, because promoting needs an active user.
- Two administrators demote each other at the same moment: one change is refused and an administrator remains, because the check and the change are one step. (AC-62)
- A deactivated person whose token has not yet expired makes a request: it is refused at once, because the account is read on every request, and Keycloak sessions are ended too. (AC-6)
- A demoted person whose session is still open makes a request: the account is read on every request, so they are a user from that request and the administrator actions are refused. (AC-50)
- All data of a deactivated account is kept. (AC-7)
- The Keycloak call fails during a deactivation: the deactivation stands, because our database already changed and the API refuses the person. The administrator gets a success that says "Deactivated here. Keycloak was not updated. Press again to retry.", and the audit entry records the outcome. (AC-58, decisions 14 and 18)
- Deactivating an account that is already deactivated, with a reason, only sends the Keycloak calls again and changes nothing in our database, the one exception to the wrong state refusal. (AC-77, decision 18)
- The Keycloak call fails during a reinstatement: our account stays deactivated and nothing changes, so no audit entry is written (the failure goes to the log, decision 17). The administrator is told that Keycloak could not be reached. The person stays locked out rather than let in. The call can be repeated. (AC-59, decision 14)
- Retrying: disabling a person who is already disabled in Keycloak, and enabling one who is already enabled, succeed and change nothing, so both Keycloak calls are safe to repeat. (decision 10, decision 14)

## Postconditions

- The account is active or deactivated, and its role is user or administrator. A deactivated person is disabled in Keycloak, and an active one who was deactivated before is enabled again. An approved, promoted or demoted person's Keycloak account is unchanged.
- At least one active administrator exists, even when two changes ran at once. (AC-51, AC-62)
- If a Keycloak call failed, the account change of a deactivation stands and the account of a reinstatement stays deactivated, until the call is repeated. (AC-58, AC-59)
- An audit entry records who made the change, to whom, and why, and is held by the Audit context (BC-AUDIT). A deactivation whose Keycloak call failed has that entry with the outcome Keycloak not updated. A reinstatement that failed changes nothing and writes no entry.
- No data of the account is removed.

## Open questions

For the product owner to decide.

1. Decided (decision 10, decision 14): a deactivation changes our database first, then Keycloak, and if Keycloak fails the deactivation stands, the administrator is told "Keycloak was not updated" and the call can be repeated by deactivating again (decision 18, AC-77). A reinstatement is the reverse: Keycloak first, then our database, so a failure locks the person out. Both Keycloak calls are safe to repeat.
2. Decided (decision 13): promoting and demoting administrators belongs to this use case, with a reason and an audit entry.
3. An evaluation that a deactivated person had running should reach its end. No criterion yet, because evaluations do not exist.
4. Decided: promoting needs an active user. A pending or deactivated account is refused.
5. Decided (decision 14): a reinstatement needs a reason, like every change except an approval (AC-7, AC-57).
6. Decided (decision 18): one entry for each change, with an outcome (done, or Keycloak not updated). Refused changes go to the log.

## Slices

- TSK-A4.1: Approve a pending account, and refuse a wrong state or an unknown account (AC-5, AC-66, AC-76)
- TSK-A4.2: Deactivate an account with a reason, only an active administrator may, never oneself, and a deactivated person is refused at once (AC-6, AC-63, AC-64, AC-65, AC-67)
- TSK-A4.3: Reinstate a deactivated account with a reason, and a failed Keycloak call leaves it deactivated (AC-7, AC-57, AC-59)
- TSK-A4.4: Promote an active user to administrator, with a reason, rules RULE-A3 (AC-49)
- TSK-A4.5: Demote an administrator, with a reason, never oneself and never the last one, the check and the change as one step, rules RULE-A1, RULE-A2 (AC-50, AC-51, AC-62)
- TSK-A4.6: Deactivate database first, then Keycloak, and a failed Keycloak call leaves the deactivation standing (AC-58)
- TSK-A4.7: Repeat a deactivation to send the Keycloak calls again (AC-77)


## Overview

The analysis sequence is in [UC-A4-approve-deactivate-and-reinstate-an-account-analysis-sequence.puml](diagrams/UC-A4-approve-deactivate-and-reinstate-an-account-analysis-sequence.puml) and the design sequence, with the routes, ports and adapters, in [UC-A4-approve-deactivate-and-reinstate-an-account-design-sequence.puml](diagrams/UC-A4-approve-deactivate-and-reinstate-an-account-design-sequence.puml). Both use the step numbers of the main flow.

## Analysis

### Revision 1

What the administrator and Playground say to each other, with no route, store, port or token. The diagram is
[UC-A4-approve-deactivate-and-reinstate-an-account-analysis-sequence.puml](diagrams/UC-A4-approve-deactivate-and-reinstate-an-account-analysis-sequence.puml).
Written for decision 13 (promote and demote) and updated for decision 14 (the order of a deactivation and a reinstatement, a reason for a reinstatement, the check and the change as one step, the audit entry to the Audit context). Not frozen yet: read it, then freeze it.

- A1 (step): The administrator chooses an account and what to do: approve, deactivate, reinstate, promote or demote
- A2 (step): The administrator gives a reason, except for an approval
- A3 (step): Playground checks that the person asking is an administrator
- A4 (step): Playground changes the account: its status for an approval, a deactivation or a reinstatement, its role for a promotion or a demotion. A deactivation changes the account first and then Keycloak, a reinstatement changes Keycloak first and then the account
- A5 (step): Playground has Keycloak disable the person and end their sessions (after the account is deactivated), or enable them again (before the account is active), for a deactivation or a reinstatement
- A6 (step): Playground records who made the change, to whom, and why, in the audit trail kept by the Audit context (BC-AUDIT), also when a change was only half done
- A7 (step): The person's next request is answered by what the account now allows
- A8 (rule): A change other than an approval needs a reason that says something, a reinstatement included (RULE-A3)
- A9 (rule): An administrator cannot deactivate or demote themselves (RULE-A2)
- A10 (rule): There is always an active administrator (RULE-A1)
- A11 (rule): A change must fit the account: only a pending account is approved, an active one deactivated, a deactivated one reinstated, an active user promoted, an administrator demoted
- A12 (rule): A promotion or a demotion changes Playground only, and Keycloak is not called
- A13 (rule): A pending person can only ask for their own status
- A14 (refusal): The person asking is not an administrator
- A15 (refusal): Keycloak cannot be reached during a deactivation (the deactivation stands) or a reinstatement (the account stays deactivated), and the administrator is told "Keycloak was not updated"
- A16 (outside system): Keycloak
- A17 (object): Account
- A18 (rule): Checking that an administrator remains and making the change are one step, so two changes at the same moment cannot leave none (RULE-A1)

## Design

The parts that do the work. The class diagram is [access-design.puml](../domain/diagrams/access-design.puml). The design sequence is [UC-A4-approve-deactivate-and-reinstate-an-account-design-sequence.puml](diagrams/UC-A4-approve-deactivate-and-reinstate-an-account-design-sequence.puml).

**Built:** the API for all five decisions, with the rules, the reason for a reinstatement, an audit entry written by the Access context and the Keycloak calls, and the administrator accounts page of the web server, which offers promote and demote with a reason. The API's `AccessService.change` already handles promote and demote (the domain rules, the reason and the audit entry), and its tests cover them.

**Planned for the alpha, not built:**
- D11: the order of a deactivation (decisions 10 and 14). BUILT: a deactivation saves our account, records its audit entry, commits, then calls Keycloak, and returns an outcome instead of raising (AC-58, AC-77, ADR 0009). A reinstatement calls Keycloak first, and a failure changes nothing and answers 502 (AC-59).
- D13: the check and the change as one step (a lock on the active administrator rows, ADR 0009), proved by a test that runs two changes at once (AC-62). Today `count_active_administrators` and `save` are two separate calls.
- D14: the audit entry goes to the Audit context (BC-AUDIT) through the AuditLog port. Today the Access adapter writes an `audit_entries` table of its own, which moves to Audit (decision 14).

- D1 (route): The five routes `POST /accounts/{id}/approve`, `deactivate`, `reinstate`, `promote` and `demote`, with `GET /accounts` and `GET /audit`, each behind the administrator guard
- D2 (guard): The chain of checks on every request: token, account, deactivated refused, pending refused, administrator only
- D3 (use case): AccessService.change
- D4 (domain rule): decide() and clean_reason(): the transitions, no self change, the last administrator, the reason
- D5 (aggregate): Account, with its role and status
- D6 (port): AccountRepository, with the count of active administrators
- D7 (port): AuditLog, answered by the Audit context (BC-AUDIT) and no longer by an Access table; it also records the outcome of a change
- D8 (port): IdentityProvider of the API (disable, enable, end sessions), not called for approve, promote or demote
- D9 (adapter): SqlAdapters on PostgreSQL (RDS on AWS) and KeycloakAdmin
- D10 (mapping): Domain errors answered as HTTP statuses in main.py (422 reason, 409 last administrator and wrong state, a self change refused, 404 no account)
- D11 (use case): BUILT: a deactivation changes our account first, then Keycloak, and the reinstatement reverse, each with its failure branch (decisions 10, 14 and 18)
- D12 (web): The administrator accounts page and its table, with the reason dialog, calling the API through the BackendApi port
- D13 (port): ALPHA, planned, not built: AccountRepository makes the last-administrator check and the change as one step (a lock on the active administrator rows), with a PostgreSQL test that runs two changes at once
- D14 (adapter): ALPHA, planned, not built: the AuditLog adapter wired by the composition root to the Audit context (BC-AUDIT)

## Changes from analysis to design

```
A1 became -> D1, D12
A2 became -> D1, D4, D12
A3 became -> D2
A4 became -> D3, D4, D5, D6, D11
A5 became -> D3, D8, D9, D11
A6 became -> D3, D7, D9, D14
A7 became -> D2, D5
A8 became -> D4
A9 became -> D4
A10 became -> D4, D6, D13
A11 became -> D4
A12 became -> D3
A13 became -> D2
A14 became -> D2, D10
A15 became -> D3, D10
A16 became -> D8, D9
A17 became -> D5
A18 became -> D3, D6, D13
```

## Not in this use case

- Signing in, signing out, refreshing the session and resetting a password. Those are Keycloak's (decision 1).
- Roles other than user and administrator, and project roles. They are parked for release R2 (decision 13).
- Adding a person to a project (UC-P2).
- A pending person's own status request (AC-4, AC-47) is UC-A3's. It was TSK-A4.2 here, and the slices were renumbered after it left.
