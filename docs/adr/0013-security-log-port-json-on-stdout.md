# 0013 A SecurityLog port, one JSON line on stdout

- Status: accepted
- Date: 2026-11-20
- Decided by: the agent (technical), after decision 17 (owner)
- Note: this is the **API half**. It was first written as ADR 0010 on branch `feat/UC-A1-basic-logging`, for the old layout, and is renumbered 0013 here because 0010 to 0012 were taken. The **web half** (the BFF's `SecurityLog` port, `sign_in`, `session_start`, `session_end`, `token_refresh`) is still on that branch and is not merged.

## Context
NFR-5 and AC-48 are in the alpha: a log line for every refused sign in, every refused request and every session that starts or ends, with no token or code in it. UC-L1 (AC-82, decision 22) adds that reading the audit trail and every refusal of it write a line to this log and never an audit entry. On AWS the ECS `awslogs` driver sends stdout to CloudWatch, so nothing else is needed to ship the lines.

## Decision
- Each context that needs it declares a `SecurityLog` Protocol in its own `application/ports.py`, in its own words, with one method: `event(name, result, person_id=None, session_id=None, reason=None)`. Access uses it in its guards and its rule error handler; Audit uses it for `audit_read` and its own refusal handler. No shared kernel (ADR 0010, 0011). The domain does not log.
- One adapter class, `JsonStdoutSecurityLog`, in `app/infrastructure/security_log.py`, uses the standard library only and imports no context. It satisfies both ports structurally. Composition builds it and hands it to both contexts.
- It writes one JSON object per line to stdout with these keys only: `ts` (UTC, ISO 8601), `event`, `result`, `person_id` when known, `session` (the first 16 hex characters of a SHA-256 of the session id, never the id) and `reason`. `event`, `result` and `reason` must match `[a-z_]{1,40}`; a `reason` that does not is dropped, an `event` or `result` that does not becomes `invalid_event` or `invalid_result`. A `person_id` must look like an id. There is no way to pass a token, an email or typed text.
- Events in the API: `request_refused` / `refused` with `reason` the error code (`missing_token`, `invalid_token`, `account_deactivated`, `account_pending`, `forbidden`, and the code of any rule refusal), and `audit_read` / `ok` with the caller's account id. A success of any other route writes nothing. A refusal writes exactly one line.
- The guard that knows the account puts its id in `request.state.person_id`, so a later refusal by a rule or by Audit is logged with who it was.
- A `FakeSecurityLog` in `tests/fakes.py` records events for tests.

## Consequences
One more port in each context that logs, and the guards stay thin. Metrics, request ids and tracing are not part of the alpha (decision 17). The audit trail stays separate: this log is for operators, the trail is a record for administrators (decision 22). An architecture test proves that infrastructure imports no context and that the two ports do not import each other.

## Links
decisions 17 and 22; NFR-5; AC-48; AC-82; UC-L1 step 6 and TSK-L1.6; UC-A1 (web half, branch `feat/UC-A1-basic-logging`); ADR 0010, 0011.

## Amendments (21 Nov 2026)
The **web half** is built on branch `feat/UC-A1-finish-the-gaps` (pull request 24): the BFF's `SecurityLog` port, `JsonSecurityLog` and the events `sign_in`, `session_start`, `session_end` and `token_refresh`. The note at the top that it is "not merged" holds only until that pull request is merged. The web side does not yet set `person_id` in its lines.
