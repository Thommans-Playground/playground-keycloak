# playground-keycloak

Playground for Keycloak: a working auth module (Keycloak + FastAPI + Next.js with shadcn), built from the source specs.

Study guide for the sign-in mechanism, with experiments: [docs/AUTH-STUDY-GUIDE.md](docs/AUTH-STUDY-GUIDE.md).

Study material in [docs/study/](docs/study/): the [Keycloak study plan](docs/study/keycloak-study-plan.md), the [web hexagon concepts](docs/study/web-hexagon-concepts.md), and test-first build lessons for [sign in](docs/study/UC-A10-sign-in-test-first.md) and [sign out](docs/study/UC-A11-sign-out-test-first.md).

Spec: [docs/specs/keycloak-auth-module.md](docs/specs/keycloak-auth-module.md). The specs it came from now live under `docs/`: [requirements](docs/requirements/requirements.md), [use cases](docs/usecases/), and the [domain](docs/domain/) (contexts, ontology, decisions).

**New here? Read [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) first.**

## Run it

Everything in Docker (Keycloak, API, web):

```bash
docker compose up -d --build   # then http://localhost:3000
```

Or, for working on the code (Keycloak in Docker, API and web on your machine):

```bash
# 1. Keycloak (needs Docker). http://localhost:8080, admin / admin
cd keycloak-config && docker compose up -d

# 2. API. http://localhost:8000/docs
cd apps/api && cp .env.example .env && uv sync
uv run uvicorn app.main:create_app --factory --port 8000

# 3. Web. http://localhost:3000
cd apps/web && npm install && npm run dev
```

Sign in as `admin@example.test` / `Admin123!` (first administrator) or `maya@example.test` / `Maya123!` (starts pending until approved). "Create account" registers a new person in Keycloak, who then waits as pending.

## Tests

```bash
cd apps/api && uv run pytest     # domain rules, token checks, account flows (fake Keycloak admin), on SQLite in memory
cd apps/api && TEST_DATABASE_URL=postgresql+psycopg://playground:playground@localhost:5433/playground_test uv run pytest   # the same tests on PostgreSQL (docker compose up -d api-db). Use the *_test database: the tests drop every table, and refuse any other name
cd apps/web && npm test          # safeReturnTo
```

## How it fits together

| | |
|---|---|
| `keycloak-config/` | Docker compose and the `playground` realm (clients, service account, seeded people). Phase 2 moves this to its own repo |
| `apps/api/` | FastAPI. Checks the token (JWKS, issuer, audience, expiry) on every request, owns accounts, roles, status and the audit trail |
| `apps/web/` | Next.js BFF. Authorization code flow with PKCE, tokens kept on the server, one HttpOnly cookie in the browser, `/api/backend/*` forwards to the API |
