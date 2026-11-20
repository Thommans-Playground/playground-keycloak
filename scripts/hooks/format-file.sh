#!/usr/bin/env bash
# Claude Code PostToolUse hook: format the one file that was just written or edited. Reads the hook JSON on stdin.
# Never fails the tool call: formatting is a courtesy here, and scripts/check.sh and CI are the gate.
f=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null) || exit 0
[ -f "$f" ] || exit 0
root=$(cd "$(dirname "$0")/../.." && pwd)
case "$f" in
  "$root"/apps/api/*.py)
    (cd "$root/apps/api" && uv run --quiet ruff check --fix --quiet "$f"; uv run --quiet ruff format --quiet "$f") >/dev/null 2>&1 ;;
  "$root"/apps/web/src/*.ts|"$root"/apps/web/src/*.tsx|"$root"/apps/web/src/*/*.ts|"$root"/apps/web/src/*/*.tsx|"$root"/apps/web/src/*/*/*.ts|"$root"/apps/web/src/*/*/*.tsx|"$root"/apps/web/src/*/*/*/*.ts|"$root"/apps/web/src/*/*/*/*.tsx)
    (cd "$root/apps/web" && npx --no-install prettier --write --log-level silent "$f") >/dev/null 2>&1 ;;
esac
exit 0
