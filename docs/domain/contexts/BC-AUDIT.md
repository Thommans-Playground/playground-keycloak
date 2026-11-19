```yaml
id: BC-AUDIT
type: context
name: Audit
status: draft
kind: generic
owns: []
  # OBJ-L1 (the audit entry) is not in the ontology yet. Hand it to vbench-ontology, then list it here.
refers_to:
  - context: BC-ACCESS
    how: by account id only. Access writes its account changes here, through its own AuditLog port and a bridge in the composition root
  - context: BC-PROJECTS
    how: by project id and account id only. Projects writes its project changes here, through its own AuditLog port and a bridge in the composition root
ports_needed:
  - name: AuditRepository
    answers: Add an audit entry, and list the entries newest first.
    status: built
must_not:
  - Write to Access or Projects data. It holds entries about them, and never changes an account, a role, a project or a member.
  - Import another context. Access and Projects call it through the bridge that the composition root wires, never directly.
  - Decide who may read it by looking up a role. It takes a Caller (decision 14) and checks is administrator.
  - Edit or delete an entry. The trail is append only.
questions:
  - What happened, who did it, to what, and why?
  - Which account and project changes has an administrator made?
satisfies:
  - id: FR-13
  - id: FR-17
```

# Audit context

## What it is

It keeps **the trail of what people changed**: every change to an account (UC-A4) and every project creation and
member change (UC-P1, UC-P2), in one place, so an administrator reads one list and not two. It was part of Access
until decision 14 made it a context of its own, so that Projects can write to the same trail without Access and
Projects knowing about each other.

It records. It never decides. Whether a change is allowed is for Access or Projects. By the time Audit is called, the
change is done.

## Its boundary

It owns the audit table (`audit_entries`) and the administrator's read of it. It does not own any account or project
data and never writes to it.

An **entry** holds:

- the **actor**: who did it (account id, with their name and email at that time), or nobody for a system action such as the
  first administrator being set up,
- the **action**: what was done (approve, deactivate, reinstate, promote, demote, register, create a project, add a
  member, remove a member),
- the **kind** of thing it was done to (account or project) and **which one** (its id, with its name, and its email for an
  account, at that time),
- the **people involved** (the details): for a project creation the first members, for a member change the member,
- the **reason**, where one was asked (RULE-A3 for accounts, not for adding a member, decision 14),
- the **time**.

Names and emails are **copied into the entry when the event happens**. A person can rename themselves in Keycloak, and
a trail that follows the live name would rewrite history. Copying also keeps an entry readable if an account or a
project is later changed. This is a plain correction of the present name, not a history of names: the trail says
what the person was called when it happened.

## How the other contexts write to it

Access and Projects each keep their **own `AuditLog` port**, written in their own words. The **composition root**
(`main.py`) wires, for each, a small adapter (a bridge) that turns the call into Audit's use case,
`AuditService.record(entry)`. So Access never imports Audit and Projects never imports Audit, and the architecture
test that forbids one context importing another still holds. Only the composition root knows all three.

```mermaid
flowchart LR
    A[Access AuditLog port] --> BA[bridge in the composition root]
    P[Projects AuditLog port] --> BP[bridge in the composition root]
    BA --> S[AuditService.record]
    BP --> S
    S --> R[AuditRepository port]
    R --> DB[(audit_entries on PostgreSQL)]
```

The administrator reads the trail through `AuditService.read(caller)`. A person who is not an administrator is refused.

## Who does what

| Access and Projects | Audit |
| ------------------- | ----- |
| Decide whether a change is allowed, and make it | Records that it happened, once it has |
| Know the people and the project by id, and look up their names | Keeps the names and emails as they were |
| Ask for a reason where the rule needs one | Stores the reason, and never asks for one |
| Say who is the caller | Lets only an administrator read |

## The rules it holds

None of its own yet. The rules that make an entry necessary are in the other contexts:
[RULE-A3](../ontology/RULE-A3-account-change-needs-a-reason.md) an account change needs a reason, and decision 14 for
project member changes (an audit entry, no reason).

## The use cases

[UC-L1](../../usecases/UC-L1-view-the-audit-trail.md) view the audit trail. Writing an entry is not a use case of its own: it is the
last step of UC-A4, UC-P1 and UC-P2.

## Open questions

For the product owner to decide.

1. Should an entry be kept for a read, or for a refused change? Not in the alpha: only changes that happened are recorded.
2. How long is the trail kept, and can it be exported? Nothing is decided. The alpha keeps every entry.
3. Should the list be paged and filtered by kind, person or date? Today it returns everything, newest first.

## Built, and not yet built

Built: the audit table, written by Access for each account change (`audit_entries`: time, actor id, action, target id,
reason), and the administrator's `GET /audit` and the table on the admin accounts page. They still live in
Access's code.

Not built: the Audit context itself (its own folder, `AuditService`, `AuditRepository`, `SqlAudit`), the `kind` and
`details` columns and the names and emails at the time, the bridges, the Alembic migration that moves the table
(decision 14), project entries, and the read that returns both kinds.
