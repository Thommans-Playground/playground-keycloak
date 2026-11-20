# 0015 The Projects context: layout, ports, tables and tests

- Status: accepted
- Date: 2026-11-20
- Decided by: the agent (technical), after decision 23 (owner)

## Context
UC-P1, UC-P2 and UC-P3 are specified and reviewed, and Projects is the next context. ADR 0010 gives it the same folders as every context, ADR 0002 says it receives a `Caller`, ADR 0011 gives it the `People` idea and says Access answers it, and ADR 0013 gives each context its own `SecurityLog`. The reviewers asked for the choices to be written down once, before the first test.

## Decision
- **Layout (ADR 0010).** `app/projects/` has `domain/` (`project.py` with the aggregate `Project` and the entity `Membership` inside it, `name.py` with `ProjectName`, `caller.py` with the `Caller` of Projects, `errors.py`), `application/` (`ports.py`: `ProjectRepository`, `AccountStatus`, `People`, `AuditLog`, `SecurityLog`; `service.py`: `ProjectsService`) and `adapters/inbound/` (`http.py`, `schemas.py`, `errors.py`) and `adapters/outbound/` (`sql.py`). No shared kernel: Projects has its own `Caller`, built in `composition/` by `projects_caller(account)`, beside `audit_caller`. Projects imports no other context.
- **`AccountStatus.active_among(ids)`** returns the ids that are active among those given, and leaves out any that are unknown or not active. It is answered by a **new Access use case**, `AccessService.active_among(ids)`, built test first before Projects, so Access's own rule for an active account applies and Projects never reads an account. A bridge in `composition/` calls it on the request's session.
- **`People.names_of(ids)`** returns for each known id its name and email, and leaves out unknown ids. It is a separate port from `AccountStatus`, because a name is not a status, and it is answered by Access in `composition/`.
- **The audit bridge.** Projects' `AuditLog` entry carries the project id and name, the actor and the members, with names taken from `People` at that moment. A `ProjectsAuditBridge` in `composition/` turns it into `AuditService.record` on the same session, so the change and its entry commit together (ADR 0011, BC-AUDIT table).
- **Tables.** One Alembic migration (ADR 0012) makes `projects` and `memberships`. Ids are random UUID strings made in the domain, so a 404 reveals nothing (no count, no order). Grants are per table and by column, with no default privileges: the API role gets INSERT and SELECT on `projects` and no UPDATE and no DELETE; INSERT, SELECT and DELETE on `memberships`, no UPDATE. A PostgreSQL grant test like AC-80 proves it (AC-95). Membership writes are the difference between the rows before and after: adding an existing member changes nothing and writes no entry. A unique key on (project, account) means two concurrent adds leave one row (AC-90).
- **Input.** A project name follows the rule of reasons (AC-81): no control or bidirectional override characters, trimmed, 1 to 100 characters counted as Unicode characters. The first members are capped at 50 and de-duplicated (AC-89, AC-92). Request bodies refuse unknown fields (AC-93).
- **Logging.** Every refusal and every read writes one line to the security log (AC-48) through Projects' own `SecurityLog` port (ADR 0013). A refusal and a read write no audit entry (decision 22).
- **Tests.** The architecture test loops over all contexts, so Projects is held to ADR 0010 with no new rule. A test checks that every route under `/projects` depends on the guard chain, including a deactivated person, a pending person and a request with no token, with a real `{project_id}` (AC-94, like AC-4).
- **The contract.** The create and the open answers carry the empty lists `files`, `endpoints` and `evaluations` (decision 23).

## Consequences
More files and two small bridges, and one Access use case that exists only for Projects. The cost is paid once, and no context imports another. The grant test runs on PostgreSQL only. The ids are longer than counters, and a list has no stable order beyond the creation time. No paging in the alpha (decision 23).

## Links
Decision 23; ADR 0002, 0003, 0010, 0011, 0012, 0013; BC-PROJECTS; projects-design.puml; UC-P1, UC-P2, UC-P3; AC-48, AC-89 to AC-95.
