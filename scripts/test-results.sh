#!/usr/bin/env bash
# Run the fast unit suites and write their results as JUnit XML, so `vcycle.py` can say a criterion's test PASSED and not
# only that it exists (vbench.json "results"). Files go to .claude/test-results/ (git-ignored). Stack tests (integration and
# acceptance) are run by scripts/test-stack.sh; add their XML to the same folder to count them too.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=$PWD/.claude/test-results
mkdir -p "$OUT"
echo "==> api: pytest (SQLite) -> $OUT/api.xml"
(cd apps/api && uv run pytest -q --junitxml="$OUT/api.xml" >/dev/null) || echo "   (some API tests failed: see the XML)"
echo "==> web: node --test -> $OUT/web.xml"
(cd apps/web && node --test --test-reporter=junit --test-reporter-destination="$OUT/web.xml" "src/**/*.test.ts" >/dev/null 2>&1) || echo "   (some web tests failed: see the XML)"
echo "wrote $(ls "$OUT"/*.xml | wc -l | tr -d ' ') file(s). Then: python3 .claude/skills/vbench-vcycle/scripts/vcycle.py --all"
