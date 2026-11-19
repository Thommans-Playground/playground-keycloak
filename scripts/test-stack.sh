#!/usr/bin/env bash
# A fresh, isolated stack for the integration and acceptance tests (and for CI later).
#   scripts/test-stack.sh up      build and start Keycloak, the API, the web app and their databases, wait until healthy
#   scripts/test-stack.sh down    stop it and delete its volumes, so the next run starts from nothing
#   scripts/test-stack.sh run     up, run both integration suites, then down (down runs even when a test fails)
# It uses its own compose project name, so its volumes never touch the dev stack's. It uses the SAME ports as the dev
# stack (the Keycloak realm fixes the web address), so stop the dev stack first: docker compose down
# To run the tests against a stack that is already up, skip this script and set INTEGRATION=1 (see docs/TESTING.md).
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT=playground-test
COMPOSE=(docker compose -p "$PROJECT" -f docker-compose.yml)
KEYCLOAK_URL=${KEYCLOAK_URL:-http://localhost:8080}
API_URL=${API_URL:-http://localhost:8000}
APP_URL=${APP_URL:-http://localhost:3000}

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
start() {
  "${COMPOSE[@]}" up -d --build --wait --wait-timeout 300
  wait_for keycloak "$KEYCLOAK_URL/realms/playground/.well-known/openid-configuration"
  wait_for api "$API_URL/health"
  wait_for web "$APP_URL/"
}

case "${1:-}" in
  up)
    start
    ;;
  down)
    "${COMPOSE[@]}" down -v --remove-orphans
    ;;
  run)
    trap '"${COMPOSE[@]}" down -v --remove-orphans' EXIT
    start
    export INTEGRATION=1
    (cd apps/api && uv run pytest -q tests/integration)
    (cd apps/web && npm run test:integration)
    ;;
  *)
    echo "usage: $0 up|down|run" >&2
    exit 2
    ;;
esac
