# Testing

Each level proves more and runs slower. Most tests sit at the bottom.

| Level | What it proves | API (`apps/api`) | Web (`apps/web`) |
|---|---|---|---|
| Unit | one rule or value, no I/O | `uv run pytest tests/test_domain.py` | `npm test` (domain files) |
| Use case | a use case with fake ports | `uv run pytest tests/test_service.py` | `npm test` (application files) |
| Adapter | one adapter against its real partner | `uv run pytest tests/test_adapters_*.py` (SQLite, or PostgreSQL with `TEST_DATABASE_URL`) | `INTEGRATION=1 npm run test:integration` (`src/adapters/*.it.ts`, real Keycloak) |
| Integration | the API, Keycloak and the database together | `INTEGRATION=1 uv run pytest tests/integration` | `INTEGRATION=1 npm run test:integration` |
| Acceptance | an acceptance criterion, through the running web app | same as above | `INTEGRATION=1 npm run test:integration` (`src/acceptance/*.it.ts`) |

`npm test` runs only `*.test.ts`. The slow tests are `*.it.ts`, so a normal run never needs the stack.

## The INTEGRATION=1 switch

The integration and acceptance tests need a running stack. They run only when `INTEGRATION=1` is set. Without it every
one of them is skipped, and says why. With it, a stack that cannot be reached makes the suite fail: it never goes green
by skipping.

Addresses come from environment variables, with local defaults:

| Variable | Default |
|---|---|
| `KEYCLOAK_URL` | `http://localhost:8080` |
| `API_URL` | `http://localhost:8000` |
| `APP_URL` | `http://localhost:3000` |
| `KEYCLOAK_REALM` | `playground` |

The Keycloak realm fixes the web address (`http://localhost:3000/auth/callback`), so `APP_URL` has to stay as it is
unless the realm changes too.

The web tests use plain `fetch` and a small cookie jar (`apps/web/src/testing/stack.ts`). There is no browser and no
extra dependency. They run one at a time (`--test-concurrency=1`).

## Throwaway users

Each test makes its own person in Keycloak through the admin REST API, with the `playground-backend` service account:
`it-<epoch>-<random>@example.test`. An `after` hook deletes them from Keycloak, also when a test fails. The person's
account row in the API database stays behind (the API has no delete), so the dev database slowly collects `it-` rows.
The fresh test stack below does not have this problem: its volumes are deleted.

Only throwaway accounts change state. The tests sign in as `admin@example.test` to approve, deactivate and reinstate
them, and never change `admin@` or `maya@`.

## A fresh test stack

`scripts/test-stack.sh` runs its own stack (compose project `playground-test`, its own volumes), on the SAME ports as
the dev stack, so stop the dev stack first (`docker compose down`).

```
scripts/test-stack.sh up     build and start Keycloak, the API, the web app; wait until all answer
scripts/test-stack.sh down   stop it and delete its volumes
scripts/test-stack.sh run    up, run the API and web integration suites, then down (also when a test fails)
```

CI will call `scripts/test-stack.sh run`.
