---
name: vbench-test-stack
description: Run the whole test gate on a fresh, isolated stack, the same checks CI runs, and report what passed, what failed and what it means. Starts Keycloak, the API, the web app and their databases from nothing in their own compose project, runs the unit suites, the PostgreSQL run, the integration and acceptance tests, then wipes the stack. Use whenever the user says "run everything", "fresh stack", "full test run", "is it green", "run the integration tests", "run CI locally", "can I merge", "verify UC-A1", or before a pull request, even if they never say "vbench". Also use it to read a failed CI run.
---

# vbench-test-stack

One command runs the whole gate from nothing, so a green result does not depend on what happens to be running or on
what an earlier test left behind. It is the same thing CI runs (`.github/workflows/ci.yml`).

The commands, the environment variables and the test levels are in `docs/TESTING.md`. The decision is
`docs/adr/0006-test-pyramid-and-isolated-stack.md`. This skill does not repeat them.

## What the script does

`scripts/test-stack.sh`, from the repo root:

| Command | What it does |
|---|---|
| `check` | Says whether ports 8080, 8000, 3000 and 5433 are free. |
| `up` | Builds and starts the stack in its own compose project (`playground-test`), and waits until Keycloak, the API and the web app answer. |
| `down` | Stops it and deletes ITS volumes only. It never touches the dev stack. |
| `run` | `check`, `up`, the stack tests, then `down` (also when a test fails). |
| `all` | The unit suites first (API on SQLite, web tests, lint, typecheck, the tool tests, the requirements and tag reports), then `run`. This is the whole gate. |

The stack tests are: the API tests again on the stack's own PostgreSQL (`playground_test`), the API integration tests
against a real Keycloak, and the web integration and acceptance tests over HTTP. Each test makes its own throwaway
Keycloak user and deletes it.

## Steps

1. **Check what is running.** `docker compose ps` at the repo root. The fresh stack uses the SAME ports as the dev stack
   (the Keycloak realm fixes the web address), so a running dev stack makes `check` fail.
2. **If the dev stack is running, ask before stopping it.** Stopping it is reversible and keeps its data:
   `docker compose stop`, and afterwards `docker compose start`. Never run `docker compose down -v` on the dev project:
   that deletes the dev databases. The script's `down` is safe, because it only names the `playground-test` project.
3. **Run it.** `scripts/test-stack.sh all` for the whole gate, or `run` for the stack tests only. It takes a few minutes
   the first time (image builds). Run it in the background and wait, do not poll.
4. **Report as facts**, with the numbers: the unit results, the PostgreSQL run, the integration and acceptance results,
   lint and typecheck, and the tag report (`at_tool.py report`: criteria with no test, deferred to R2, covered only by the
   stack run, rules with no test). Quote the failing test name and its assertion. Do not say "all green" without the
   counts.
5. **Restore the dev stack** if you stopped it (`docker compose start`) and say so. Confirm `curl` on the three
   addresses answers.
6. **Say what the result does NOT prove.** A green gate shows the tagged tests pass. It does not show that a person has
   reviewed the criteria (the stamps), or that a test is any good. `uc_tool.py validate` is still red until a person
   stamps the use cases.

## Reading a failure

- **Ports in use:** the dev stack, or another program. Stop it, do not change the ports (the realm needs 3000 and 8080).
- **A service did not answer:** read its logs with `docker compose -p playground-test -f docker-compose.yml logs <service>`
  before the stack is wiped (`up` leaves it running; `run` wipes it at the end, so use `up` to debug).
- **Keycloak cookie or login errors in a helper:** Keycloak sets `Secure` cookies even over http, and the test helpers keep
  them by hand. See `apps/web/src/testing/stack.ts` and `apps/api/tests/integration/helpers.py`.
- **A test passes alone and fails in the suite:** the suites run one test at a time. Look for shared state, a leftover
  user, or a clock.

## Rules

- Never edit a test to make the gate pass. If a test is wrong, say why and fix it in its own change.
- Never stamp, freeze or approve anything from here. Those are the owner's.
- Do not push, and do not change branch protection: that is set in the GitHub settings by a person.
