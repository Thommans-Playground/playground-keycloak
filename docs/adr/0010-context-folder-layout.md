# 0010 One folder layout for every bounded context in the API

- Status: accepted
- Date: 2026-11-20
- Decided by: the agent (technical). The two owner questions it leaves open are listed under Consequences.

## Context
The API had one context (Access) with `ports.py`, `service.py` and `adapters/` side by side, and `main.py` held the routes, the schemas, the guards, the error map and the wiring (240 lines). Audit and Projects are next (ADR 0003, BC-PROJECTS), and each must be built the same way, with a place for everything. Three reviewers (design, spec, security) read the proposal; their findings shaped this.

## Decision
We follow the layout of *Architecture Patterns with Python* (ports and adapters, service layer, composition root). Every context under `app/` has exactly:

```
<context>/
  domain/                  rules, pure: standard library and itself only
  application/             use cases (service.py) and the ports they need (ports.py)
  adapters/
    inbound/               drives the app: http.py (routes and guards), schemas.py, errors.py (rule -> HTTP status)
    outbound/              driven by the app: sql.py, keycloak_admin.py, token_verifier.py
```

Outside the contexts there are only three things:
- `main.py`: the entry point (`app.main:create_app`), one import.
- `composition/`: the composition root. The only place that sees every adapter and wires them to the use cases.
- `infrastructure/`: settings and the declarative `Base`. They belong to no context.

Import rules (all enforced by `tests/test_architecture.py`, each failure says why):
- `domain` imports the standard library and itself.
- `application` imports the domain and itself, never a framework or an adapter.
- `inbound` imports the application, the domain and web libraries. `outbound` imports the application (ports), the domain and infrastructure libraries. Neither imports the other.
- Only `composition/` imports adapters. A context never imports another context.
- A new top level package, a loose file in a context, or a new folder in a layer fails the test until this ADR is changed on purpose.

Choices made here:
- **Use cases are the inbound ports.** The HTTP adapter calls `AccessService` directly. No Protocol per use case; a reviewer should not flag this as a port without an adapter.
- **One service module per context for now.** It is split into one file per operation only when it grows or two operations need different dependencies.
- **The token verifier is an outbound adapter** (`JwtTokenVerifier`) behind the `TokenVerifier` port; `Principal` and `InvalidToken` are part of the port.
- **Tests stay grouped by level** (ADR 0006) and are not split per context yet.
- **No shared kernel.** Nothing needs one today (see Consequences).

## Consequences
- Easier: a new context is a copy of the shape; the test tells a person what is misplaced.
- Harder: more files and folders for a small codebase. We accept it for the sake of the second and third context.
- This change moved files and split `main.py`. Behaviour is unchanged (same routes, same errors, same codes), and the suites pass on SQLite and PostgreSQL.
- FastAPI 0.163 keeps an included router as a wrapper, so a test that walks `app.routes` must descend into it (`_api_routes` in `tests/test_api.py`). Without that the "every route refuses a pending person" test checks nothing.

Not done here, and why:
- **Access guards stay in the inbound adapter.** Moving them into a domain policy changes the error body (`detail.code` today) that the BFF reads, so it is a separate, tested change.
- **`KeycloakAdmin` still takes the whole `Settings`.** It should take plain values, so a move to Secrets Manager touches only `composition/`.
- **`/audit` still reads `svc.audit` directly**, and `set_outcome` still edits an entry. Both are settled when Audit is built.
- **The Audit context itself, one session per request across the bridge, and Alembic** are ADR 0003 and 0004.

Open for the owner (they decide the Audit build, not this move):
1. Is the audit trail strictly append-only, with a second entry for the Keycloak outcome, or is one narrow update of `outcome` allowed (by entry id)?
2. Is a tiny stdlib-only shared kernel (base `DomainError`, a clock) allowed in the domain, or does each context keep its own, including its own `Caller` type?

## Links
ADR 0001, 0002, 0003, 0004, 0006, 0009; AC-36 (NFR-3); BC-AUDIT; decision 14.
