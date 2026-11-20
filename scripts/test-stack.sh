#!/usr/bin/env bash
# A fresh, isolated stack for the integration and acceptance tests, and for CI.
#   scripts/test-stack.sh check   say whether the ports the stack needs are free
#   scripts/test-stack.sh up      build and start Keycloak, the API, the web app and their databases, wait until they answer
#   scripts/test-stack.sh down    stop it and delete ITS volumes, so the next run starts from nothing
#   scripts/test-stack.sh run     check, up, run the stack tests, then down (down also runs when a test fails)
#   scripts/test-stack.sh all     the unit suites first, then run: the whole gate, the same as CI
# It uses its own compose project name (playground-test), so `down -v` never touches the dev stack's volumes.
# It uses the SAME ports as the dev stack (the Keycloak realm fixes the web address), so the dev stack must be stopped:
#   docker compose stop        (and later: docker compose start)
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT=playground-test
COMPOSE=(docker compose -p "$PROJECT" -f docker-compose.yml)
KEYCLOAK_URL=${KEYCLOAK_URL:-http://localhost:8080}
API_URL=${API_URL:-http://localhost:8000}
APP_URL=${APP_URL:-http://localhost:3000}
PORTS=(8080 8000 3000 5433 6380)
TEST_DB_URL=${TEST_DATABASE_URL:-postgresql+psycopg://playground:playground@localhost:5433/playground_test}

# A port that is already taken means the dev stack (or something else) is running: stop here, with a clear message.
check_ports() {
  local busy=()
  for p in "${PORTS[@]}"; do
    if (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null; then busy+=("$p"); fi
  done
  if ((${#busy[@]})); then
    echo "These ports are already in use: ${busy[*]}" >&2
    echo "Stop the dev stack first:  docker compose stop   (start it again later with: docker compose start)" >&2
    return 1
  fi
  echo "ports ${PORTS[*]} are free"
}

# Keycloak, the API and the web app have no health check, so wait until each one answers.
wait_for() {
  local name=$1 url=$2
  for _ in $(seq 1 120); do
    if curl -fsS -o /dev/null --max-time 3 "$url"; then echo "$name is ready"; return 0; fi
    sleep 2
  done
  echo "$name did not answer at $url" >&2
  return 1
}

# On exit: if anything failed, print the stack's logs first (they are gone once the volumes are deleted), then wipe it.
cleanup() {
  local code=$?
  if [ "$code" -ne 0 ]; then
    echo "== the run failed (exit $code): the last lines of each service's log"
    "${COMPOSE[@]}" logs --no-color --tail=120 || true
  fi
  "${COMPOSE[@]}" down -v --remove-orphans || true
  exit "$code"
}

start() {
  "${COMPOSE[@]}" up -d --build --wait --wait-timeout 300
  wait_for keycloak "$KEYCLOAK_URL/realms/playground/.well-known/openid-configuration"
  wait_for api "$API_URL/health"
  wait_for web "$APP_URL/"
}

stack_tests() {
  export INTEGRATION=1
  echo "== API on the stack's PostgreSQL (playground_test)"
  (cd apps/api && TEST_DATABASE_URL="$TEST_DB_URL" uv run pytest -q)
  echo "== API integration tests"
  (cd apps/api && uv run pytest -q tests/integration)
  echo "== web integration and acceptance tests"
  (cd apps/web && npm run test:integration)
}

unit_tests() {
  echo "== API unit tests (SQLite)"
  (cd apps/api && uv run pytest -q)
  echo "== web unit tests, lint, typecheck"
  (cd apps/web && npm test && npm run lint && npm run typecheck)
  echo "== traceability tools and the tag report"
  for d in .claude/skills/vbench-*/scripts; do
    for t in "$d"/test_*.py; do
      if [ -e "$t" ]; then (cd "$d" && python3 -m unittest "$(basename "${t%.py}")"); fi
    done
  done
  python3 .claude/skills/vbench-req/scripts/req_tool.py validate
  python3 .claude/skills/vbench-at/scripts/at_tool.py report | tail -3
  echo "== the V cycle of every use case (informational until the use cases are stamped)"
  python3 .claude/skills/vbench-vcycle/scripts/vcycle.py --all | grep -E "^RESULT|^USE CASES" || true
}

case "${1:-}" in
  check) check_ports ;;
  up) check_ports; start ;;
  down) "${COMPOSE[@]}" down -v --remove-orphans ;;
  run)
    check_ports
    trap cleanup EXIT
    start
    stack_tests
    ;;
  all)
    unit_tests
    check_ports
    trap cleanup EXIT
    start
    stack_tests
    ;;
  *)
    echo "usage: $0 check|up|down|run|all" >&2
    exit 2
    ;;
esac
