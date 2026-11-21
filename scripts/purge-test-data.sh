#!/usr/bin/env bash
# Remove the rows the integration and acceptance tests leave in the DEV database (development only).
#   scripts/purge-test-data.sh --dry-run    print what would go, change nothing
#   scripts/purge-test-data.sh --yes        remove it, in one transaction
# Test rows are ONLY: accounts with email it-<digits>-<hex>@example.test named 'Integration Test' or 'Integration
# Throwaway'; projects named <known prefix> + 8 or more lowercase letters or digits; their memberships; audit entries
# whose actor or target is one of them. The seed demo data (@demo.example.test) and real accounts are never matched.
# There is no delete route for projects and the audit trail is append only, so this runs as the database OWNER role,
# through `docker compose exec` on the local api-db container. It refuses anything but the local dev compose project.
# (PURGE_PSQL_CMD + PURGE_TESTING=1 swap the psql command for a throwaway PostgreSQL in scripts/test_purge_test_data.py.)
set -euo pipefail
cd "$(dirname "$0")/.."

DEV_PROJECT=playground-keycloak
MODE=""
for a in "$@"; do
  case "$a" in
    --dry-run) MODE=dry ;;
    --yes) MODE=yes ;;
    *) echo "unknown argument: $a (use --dry-run or --yes)" >&2; exit 2 ;;
  esac
done
[ -n "$MODE" ] || { echo "usage: $0 --dry-run | --yes" >&2; exit 2; }

refuse() { echo "REFUSED: $*" >&2; exit 3; }

for v in ENVIRONMENT APP_ENV; do
  case "$(printf '%s' "${!v:-}" | tr '[:upper:]' '[:lower:]')" in
    prod|production|live) refuse "$v says production" ;;
  esac
done
case "${PGHOST:-localhost}" in localhost|127.0.0.1|::1) ;; *) refuse "PGHOST=$PGHOST is not local" ;; esac
case "${DATABASE_URL:-}${MIGRATION_DATABASE_URL:-}" in
  *@localhost*|*@127.0.0.1*|*@api-db*|"") ;;
  *) refuse "DATABASE_URL points at a remote host" ;;
esac

if [ "${PURGE_TESTING:-}" = 1 ] && [ -n "${PURGE_PSQL_CMD:-}" ]; then
  # shellcheck disable=SC2206
  PSQL=($PURGE_PSQL_CMD)
else
  [ "${COMPOSE_PROJECT_NAME:-$DEV_PROJECT}" = "$DEV_PROJECT" ] || refuse "compose project is ${COMPOSE_PROJECT_NAME}, not $DEV_PROJECT"
  [ -z "${PURGE_PSQL_CMD:-}" ] || refuse "PURGE_PSQL_CMD is only for the script's own test"
  docker compose -p "$DEV_PROJECT" ps -q api-db 2>/dev/null | grep -q . || refuse "the local $DEV_PROJECT api-db container is not running"
  PSQL=(docker compose -p "$DEV_PROJECT" exec -T api-db psql -U playground -d playground)
fi
PSQL+=(-X -q -v ON_ERROR_STOP=1 -At -F ' ')

PREFIXES='Mine|Theirs|Elsewhere|AdminOne|AdminTwo|Seen|Hidden|Controls|Adds|Removes|Methods|Eligible|Created|Nobody|Pending'
SELECT_SQL="
CREATE TEMP TABLE t_accounts ON COMMIT DROP AS SELECT id FROM accounts
  WHERE email ~ '^it-[0-9]+-[0-9a-f]+@example[.]test\$' AND name IN ('Integration Test', 'Integration Throwaway');
CREATE TEMP TABLE t_projects ON COMMIT DROP AS SELECT id FROM projects
  WHERE name ~ '^($PREFIXES)[a-z0-9]{8,}\$';
CREATE TEMP TABLE t_audit ON COMMIT DROP AS SELECT id FROM audit_entries
  WHERE actor_id IN (SELECT id FROM t_accounts) OR target_id IN (SELECT id FROM t_accounts)
     OR (kind = 'project' AND target_id IN (SELECT id FROM t_projects));
CREATE TEMP TABLE t_members ON COMMIT DROP AS SELECT project_id, account_id FROM memberships
  WHERE project_id IN (SELECT id FROM t_projects) OR account_id IN (SELECT id FROM t_accounts);
SELECT 'to remove: accounts=' || (SELECT count(*) FROM t_accounts) || ' projects=' || (SELECT count(*) FROM t_projects)
  || ' memberships=' || (SELECT count(*) FROM t_members) || ' audit_entries=' || (SELECT count(*) FROM t_audit);
"
DELETE_SQL="
DELETE FROM audit_entries WHERE id IN (SELECT id FROM t_audit);
DELETE FROM memberships m USING t_members t WHERE m.project_id = t.project_id AND m.account_id = t.account_id;
DELETE FROM projects WHERE id IN (SELECT id FROM t_projects);
DELETE FROM accounts WHERE id IN (SELECT id FROM t_accounts);
"
REMAIN_SQL="SELECT 'remaining: accounts=' || (SELECT count(*) FROM accounts) || ' projects=' || (SELECT count(*) FROM projects)
  || ' memberships=' || (SELECT count(*) FROM memberships) || ' audit_entries=' || (SELECT count(*) FROM audit_entries);"

if [ "$MODE" = dry ]; then
  printf 'BEGIN;\n%s\nROLLBACK;\n' "$SELECT_SQL" | "${PSQL[@]}"
  echo "dry run: nothing changed"
else
  printf 'BEGIN;\n%s\n%s\nCOMMIT;\n' "$SELECT_SQL" "$DELETE_SQL" | "${PSQL[@]}"
fi
printf '%s\n' "$REMAIN_SQL" | "${PSQL[@]}"
