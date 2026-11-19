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

The integration and acceptance tests need a running stack. They run only when `INTEGRATION=1` is set. Without it the web
ones (`*.it.ts`) are skipped and say so, and the API ones (`apps/api/tests/integration`) are not even collected, so a
normal `uv run pytest` neither runs nor mentions them. With it, a stack that cannot be reached makes the suite fail: it
never goes green by skipping.

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
the dev stack, so stop the dev stack first (`docker compose stop`, and `docker compose start` afterwards). Never run
`docker compose down -v` on the dev project: that deletes its databases.

```
scripts/test-stack.sh check  say whether the ports are free
scripts/test-stack.sh up     build and start Keycloak, the API, the web app; wait until all answer
scripts/test-stack.sh down   stop it and delete its volumes
scripts/test-stack.sh run    check, up, the stack tests, then down (also when a test fails)
scripts/test-stack.sh all    the unit suites first, then run: the whole gate
```

The `vbench-test-stack` skill (`/vbench-test-stack`) runs it for you and reports the result.

## The V cycle report

`python3 .claude/skills/vbench-vcycle/scripts/vcycle.py UC-A1` (or `/vbench-vcycle UC-A1`, or `--all`) joins the
checks into one table for a use case: requirements, criteria and their tests, analysis, rules and their tests, design
and diagrams, slices, and the review stamps. Each row is ok, warn or FAIL, and the exit code is 1 on a FAIL (on a warn
too with `--strict`). It reads files and runs nothing: it shows that a tagged test exists, not that it passes, so it
goes with the test runs and never replaces them. CI keeps `vcycle.json` as the record of each run.

## CI

`.github/workflows/ci.yml` runs on every pull request and on pushes to `main`, in four jobs: the API tests (SQLite and a
PostgreSQL service), the web tests (tests, lint, typecheck, build), the traceability tools and tag report, and the
fresh stack (`scripts/test-stack.sh run`). The use case check (`uc_tool.py validate`) is informational until a person
has stamped the use cases. Dependabot (`.github/dependabot.yml`) opens weekly pull requests for dependencies and
base images. A required human review and the required checks are set in the GitHub repository settings, not in a file.
