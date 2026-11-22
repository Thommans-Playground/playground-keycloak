#!/bin/bash
# Sign in to the LOCAL stack as a development account and print the path of a cookie jar, so a probe can reuse the
# session. Refuses any host that is not localhost. Prints no password and no token.
#   session.sh <email> <password> [web-origin]      default origin http://localhost:3000
set -euo pipefail
EMAIL=${1:?email}; PASS=${2:?password}; ORIGIN=${3:-http://localhost:3000}
case "$ORIGIN" in http://localhost:*|http://127.0.0.1:*) ;; *) echo "refused: $ORIGIN is not a local address" >&2; exit 2;; esac
JAR=$(mktemp -t vbench-sec-jar)
PAGE=$(curl -s -L -c "$JAR" -b "$JAR" "$ORIGIN/auth/login")
ACTION=$(printf '%s' "$PAGE" | python3 -c "import sys,re,html; m=re.search(r'<form[^>]*action=\"([^\"]+)\"',sys.stdin.read()); print(html.unescape(m.group(1)) if m else '')")
[ -n "$ACTION" ] || { echo "no login form: is the stack up (docker compose up -d)?" >&2; rm -f "$JAR"; exit 1; }
case "$ACTION" in http://localhost:*|http://127.0.0.1:*) ;; *) echo "refused: sign-in form is at $ACTION" >&2; rm -f "$JAR"; exit 2;; esac
curl -s -L -c "$JAR" -b "$JAR" -o /dev/null --data-urlencode "username=$EMAIL" --data-urlencode "password=$PASS" "$ACTION"
grep -q playground_session "$JAR" || { echo "sign in failed for $EMAIL" >&2; rm -f "$JAR"; exit 1; }
echo "$JAR"
