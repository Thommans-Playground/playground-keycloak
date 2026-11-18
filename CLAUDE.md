# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Phase 1 is built: a working Keycloak auth module, from the source specs ([docs/specs/keycloak-auth-module.md](docs/specs/keycloak-auth-module.md)).

- `keycloak-config/`: Docker compose and the `playground` realm import (the part that becomes the `keycloak-config` repo in phase 2).
- `apps/api/`: FastAPI, Python 3.12+, managed with `uv`. One folder for each bounded context under `app/` (today `access/`): `domain/` is pure rules (no HTTP, no framework), `ports.py` the ports, `service.py` the use cases, `adapters/` Keycloak admin and SQLAlchemy over PostgreSQL (`api-db`, the engine of Amazon RDS). `main.py` is the composition root and maps rules to HTTP statuses. `tests/test_architecture.py` enforces the boundaries.
- `apps/web/`: Next.js 16 (App Router, `proxy.ts` not `middleware.ts`), TypeScript, shadcn (Base UI, so `render` not `asChild`), `openid-client`. The server side (the BFF) is ports and adapters: `src/domain/` pure rules, `src/application/` use cases and `ports.ts`, `src/adapters/` Keycloak, in-memory stores and `fetch`, `src/composition.ts` the one place that picks them; pages and components stay thin. Tests are `node --test` (Node runs TypeScript directly, so no test runner to install). Read `node_modules/next/dist/docs/` before changing Next code.

Commands: `docker compose up -d --build` at the root runs everything (Keycloak, API, web; the guide is docs/GETTING-STARTED.md); or `docker compose up -d` in `keycloak-config/` for Keycloak alone; `uv run uvicorn app.main:create_app --factory` and `uv run pytest` in `apps/api/`; `npm run dev`, `npm run build`, `npm test`, `npm run lint` in `apps/web/`. Full steps in README.md.

Rules that matter: the token says who, our database says what they may do (roles and status are read on every request); the browser never sees a token; account changes need a reason and are audited. The specs live under `docs/`: `requirements/` (markdown tables), `domain/` (`contexts/`, `ontology/`, `decisions.md`, `diagrams/`) and `usecases/`. `docs/specs/keycloak-auth-module.md` is the build spec distilled from them.

## Project intent

This is a playground for learning Keycloak (per README.md), with two intended phases of work:

1. **Local Keycloak hands-on setup** — running Keycloak (via Docker), configuring realms/clients/users, and wiring a sample app to it over OIDC (Authorization Code + PKCE), then exploring realm export/import, custom themes, and SPIs.
2. **Multi-repo distribution** — packaging the resulting realm config/theme/SPI artifacts into a dedicated `keycloak-config` repo, distributed to other company project repos via Google's `repo` multi-repository tool (a manifest repo referencing `keycloak-config` alongside each product repo, with per-project revision pinning).

When adding code, prefer structuring it around these two phases rather than a generic app layout.

## Target and way of working

The playground is a prototype for an application of an organisation that is **AWS native**. The final application always runs on AWS, so each piece here has an AWS equivalent: PostgreSQL becomes Amazon RDS (or Aurora) for PostgreSQL, Keycloak runs on ECS Fargate with RDS, the web session store (in memory today) becomes ElastiCache, secrets go to Secrets Manager, project files to S3, logs to CloudWatch. Keep to the prototype's engines so the move is configuration, not a rewrite (decision 4 in `docs/domain/decisions.md`).

The application follows **domain driven design**, **test driven development** and **hexagonal architecture (ports and adapters)**, for maintainability (decisions 4 and 5). The API holds the business rules in a pure domain per bounded context. The frontend's server side (the BFF) follows ports and adapters and TDD; its pages and components stay thin, with no ports of their own. In practice: the domain imports nothing outside itself; everything that touches the outside (database, Keycloak, session store, the API, AWS services) is a port with an adapter; a rule or use case gets its failing test first; an architecture test on each side fails if a boundary is crossed. Run the API tests on SQLite for speed, and on PostgreSQL (`TEST_DATABASE_URL`, always the `playground_test` database, never `playground`: the tests drop every table and refuse any name that does not end in `_test`) before you finish.

## Reviews

Three read-only agents review the specs, and each teaches (what is wrong, why it matters, up to three options): `vbench-spec-challenger` (does the spec agree with itself), `vbench-security-reviewer` (OWASP and the OAuth BCP, against the generic checklists in `.claude/skills/_vbench/standards/security/` and our overlay `docs/standards/security-checklist.md`) and `vbench-design-reviewer` (DDD, ports and adapters, the AWS target). Run all three, together, after you write or change a use case, its diagrams, a requirement or a decision, and before it is built; skip them only for a change that touches no flow, criterion, diagram or decision. They never edit, and a person decides. A decision that accepts a risk goes in the checklist's "Accepted for now" list.
