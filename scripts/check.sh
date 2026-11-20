#!/usr/bin/env bash
# The checks CI runs, on your machine. One definition of "green" (ADR 0014).
#   scripts/check.sh fix      format and auto-fix everything: ruff (API), prettier and eslint --fix (web)
#   scripts/check.sh          the fast gate: format and lint checks, types, unit tests, requirement and test-tag checks
#   scripts/check.sh full     the fast gate, then the fresh stack: PostgreSQL, integration and acceptance tests (needs Docker,
#                             and the dev stack stopped; see scripts/test-stack.sh)
#   scripts/check.sh api|web|trace   one part of the fast gate (CI runs each as its own job)
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD
MODE=${1:-fast}

step() { printf '\n==> %s\n' "$*"; }

api() {
  cd "$ROOT/apps/api"
  step "api: ruff format --check"; uv run ruff format --check .
  step "api: ruff check";          uv run ruff check .
  step "api: pytest (SQLite)";     uv run pytest -q
}

web() {
  cd "$ROOT/apps/web"
  step "web: prettier --check"; npx prettier --check .
  step "web: eslint";           npm run lint
  step "web: typecheck";        npm run typecheck
  step "web: unit tests";       npm test
}

trace() {
  cd "$ROOT"
  step "trace: tests of the traceability tools"
  for d in .claude/skills/vbench-*/scripts; do
    for t in "$d"/test_*.py; do
      if [ -e "$t" ]; then (cd "$d" && python3 -m unittest "$(basename "${t%.py}")"); fi
    done
  done
  step "trace: requirements are well formed"; python3 .claude/skills/vbench-req/scripts/req_tool.py validate
  step "trace: test tags name real criteria"; python3 .claude/skills/vbench-at/scripts/at_tool.py report > /dev/null
}

fix() {
  step "api: ruff"; (cd apps/api && uv run ruff check --fix . && uv run ruff format .)
  step "web: prettier and eslint"; (cd apps/web && npx prettier --write . > /dev/null && npm run lint -- --fix)
}

case "$MODE" in
  fix)   fix ;;
  fast)  api; web; trace ;;
  api)   api ;;
  web)   web ;;
  trace) trace ;;
  full)  api; web; trace; step "stack: PostgreSQL, integration and acceptance"; cd "$ROOT" && scripts/test-stack.sh run ;;
  *) echo "usage: scripts/check.sh [fix|fast|full|api|web|trace]" >&2; exit 2 ;;
esac
printf '\nOK: %s\n' "$MODE"
