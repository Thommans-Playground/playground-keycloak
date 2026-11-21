#!/usr/bin/env python3
"""DEVELOPMENT ONLY. Puts dummy people and dummy projects into the LOCAL dev stack, so the pages look real.

Run it from the API's uv environment (it needs `psycopg`, which is there; nothing else but the standard library):

    cd apps/api
    uv run python ../../scripts/seed-demo.py            # prints the plan, writes nothing
    uv run python ../../scripts/seed-demo.py --yes      # writes it (safe to run again: it skips what exists)
    uv run python ../../scripts/seed-demo.py --purge --yes   # removes ONLY what this script made
    add --dry-run to any of them to print the plan and never connect

The dummy people all share one password: "Demo123!" (not temporary). They are at @demo.example.test, which is
also how everything this script made is recognised. The existing dev accounts (admin@example.test, maya@example.test)
are looked up and never created, changed or removed. Run the stack first (docker compose up -d --build) and sign in
once as admin@ and maya@ so their accounts exist.

It writes as the database OWNER role (the API role cannot write most of this), so it refuses to run unless Keycloak and
the database are on localhost / 127.0.0.1, and refuses when ENVIRONMENT or APP_ENV says production.
Settings: KEYCLOAK_URL (default http://localhost:8080), KEYCLOAK_ADMIN / KEYCLOAK_ADMIN_PASSWORD (admin / admin, the
master realm), SEED_DB_URL (default postgresql://playground:playground@localhost:5433/playground).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEMO_DOMAIN = "@demo.example.test"
DEMO_PASSWORD = "Demo123!"  # DEVELOPMENT ONLY
REALM = "playground"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
NAMESPACE = uuid.UUID("5eed0000-0000-4000-8000-00000000d3a0")  # fixed, so ids are the same on every run
ADA_EMAIL = "admin@example.test"
MAYA_EMAIL = "maya@example.test"

# (name, email local part, role, status)
PEOPLE = [
    ("Tan Wei Ming", "tan.weiming", "user", "active"),
    ("Nur Aisyah Binte Rahman", "nur.aisyah", "user", "active"),
    ("Priya Nair", "priya.nair", "administrator", "active"),
    ("Lim Jia Hui", "lim.jiahui", "user", "active"),
    ("Muhammad Hafiz", "muhammad.hafiz", "user", "active"),
    ("Chen Xiu Ying", "chen.xiuying", "user", "pending"),
    ("Ravi Kumar", "ravi.kumar", "user", "deactivated"),
    ("Siti Nurhaliza", "siti.nurhaliza", "user", "active"),
]
DEACTIVATE_REASON = "Left the programme; access no longer needed."
PROMOTE_REASON = "Second administrator for cover."

# (project name, member emails). Ada creates all; the first two members are the creation details, the rest are added.
PROJECTS = [
    ("Citizen Services Portal", [MAYA_EMAIL, "tan.weiming", "nur.aisyah", "lim.jiahui"]),
    ("Permit Processing Review", [MAYA_EMAIL, "priya.nair", "muhammad.hafiz"]),
    ("Data Quality Audit", ["tan.weiming", "siti.nurhaliza"]),
    ("Chatbot Evaluation Pilot", ["nur.aisyah", "lim.jiahui", "muhammad.hafiz", "siti.nurhaliza", "priya.nair"]),
    ("Annual Report Draft", ["lim.jiahui", "tan.weiming", MAYA_EMAIL]),
]


def demo_email(local: str) -> str:
    return local if "@" in local else local + DEMO_DOMAIN


def plan_people() -> list[dict]:
    return [
        {
            "name": n,
            "email": demo_email(l),
            "role": r,
            "status": s,
            "id": str(uuid.uuid5(NAMESPACE, "account:" + demo_email(l))),
        }
        for n, l, r, s in PEOPLE
    ]


def plan_projects() -> list[dict]:
    return [
        {"name": n, "members": [demo_email(m) for m in ms], "id": str(uuid.uuid5(NAMESPACE, "project:" + n))}
        for n, ms in PROJECTS
    ]


def project_ids() -> list[str]:
    return [p["id"] for p in plan_projects()]


# ---- safety -------------------------------------------------------------------------------------------------------


def check_safety(keycloak_url: str, db_url: str, env: dict) -> None:
    """Raise SystemExit unless this is plainly the local dev stack."""
    for var in ("ENVIRONMENT", "APP_ENV"):
        if env.get(var, "").strip().lower() in {"prod", "production"}:
            raise SystemExit(f"Refusing: {var} says production.")
    for label, url in (("KEYCLOAK_URL", keycloak_url), ("SEED_DB_URL", db_url)):
        host = urllib.parse.urlparse(url).hostname
        if host not in LOCAL_HOSTS:
            raise SystemExit(f"Refusing: {label} host {host!r} is not localhost / 127.0.0.1.")


# ---- SQL (as the owner role) ----------------------------------------------------------------------------------------


def sql_statements(people: list[dict], projects: list[dict], ada: dict, maya: dict | None, kc_ids: dict) -> list[tuple]:
    """Every write as (sql, params). Each is idempotent: it skips a row that exists."""
    by_email = {p["email"]: p for p in people}
    if maya:
        by_email[maya["email"]] = maya
    out: list[tuple] = []

    def ref(p: dict) -> tuple:
        return (p["id"], p["name"], p["email"])

    def audit(kind, actor, action, target_id, target_name, target_email, details, reason):
        a = ref(actor) if actor else (None, None, None)
        out.append(
            (
                "INSERT INTO audit_entries (kind, actor_id, actor_name, actor_email, action, target_id, target_name,"
                " target_email, details, reason) SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s::json,%s WHERE NOT EXISTS ("
                "SELECT 1 FROM audit_entries WHERE kind=%s AND action=%s AND target_id=%s"
                " AND actor_id IS NOT DISTINCT FROM %s AND details::text = %s::json::text)",
                (
                    kind,
                    a[0],
                    a[1],
                    a[2],
                    action,
                    target_id,
                    target_name,
                    target_email,
                    json.dumps(details),
                    reason,
                    kind,
                    action,
                    target_id,
                    a[0],
                    json.dumps(details),
                ),
            )
        )

    for p in people:
        ident = kc_ids.get(p["email"], p["id"])
        out.append(
            (
                "INSERT INTO accounts (id, identity, name, email, role, status, created, created_by)"
                " VALUES (%s,%s,%s,%s,%s,%s,now(),%s) ON CONFLICT DO NOTHING",
                (p["id"], ident, p["name"], p["email"], p["role"], p["status"], None),
            )
        )
        audit("account", None, "register", p["id"], p["name"], p["email"], [], None)
        if p["status"] in ("active", "deactivated"):
            audit("account", ada, "approve", p["id"], p["name"], p["email"], [], None)
        if p["role"] == "administrator":
            audit("account", ada, "promote", p["id"], p["name"], p["email"], [], PROMOTE_REASON)
        if p["status"] == "deactivated":
            audit("account", ada, "deactivate", p["id"], p["name"], p["email"], [], DEACTIVATE_REASON)

    for pr in projects:
        members = [by_email[e] for e in pr["members"] if e in by_email]
        out.append(
            (
                "INSERT INTO projects (id, name, created_by) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (pr["id"], pr["name"], ada["id"]),
            )
        )
        for m in members:
            out.append(
                (
                    "INSERT INTO memberships (project_id, account_id, added_by) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                    (pr["id"], m["id"], ada["id"]),
                )
            )
        det = lambda ms: [{"id": m["id"], "name": m["name"], "email": m["email"]} for m in ms]  # noqa: E731
        audit("project", ada, "create_project", pr["id"], pr["name"], None, det(members[:2]), None)
        for m in members[2:]:
            audit("project", ada, "add_member", pr["id"], pr["name"], None, det([m]), None)
    return out


def purge_statements(emails: list[str], pids: list[str]) -> list[tuple]:
    """Delete ONLY demo rows: accounts at the demo domain, the demo projects (by fixed id AND creator-free name list),
    their memberships, and audit entries naming a demo account or a demo project. Order respects the foreign key."""
    like = "%" + DEMO_DOMAIN
    return [
        (
            "DELETE FROM memberships WHERE project_id = ANY(%s) OR account_id IN"
            " (SELECT id FROM accounts WHERE email LIKE %s)",
            (pids, like),
        ),
        ("DELETE FROM projects WHERE id = ANY(%s)", (pids,)),
        (
            "DELETE FROM audit_entries WHERE (kind='project' AND target_id = ANY(%s))"
            " OR target_email LIKE %s OR actor_email LIKE %s",
            (pids, like, like),
        ),
        ("DELETE FROM accounts WHERE email LIKE %s", (like,)),
    ]


# ---- Keycloak -------------------------------------------------------------------------------------------------------


class Keycloak:
    def __init__(self, base: str, admin: str, password: str):
        self.base = base.rstrip("/")
        form = urllib.parse.urlencode(
            {"grant_type": "password", "client_id": "admin-cli", "username": admin, "password": password}
        ).encode()
        self.token = self._call(
            "POST",
            "/realms/master/protocol/openid-connect/token",
            form,
            auth=False,
            ctype="application/x-www-form-urlencoded",
        )["access_token"]

    def _call(self, method, path, body=None, auth=True, ctype="application/json"):
        if body is not None and not isinstance(body, bytes):
            body = json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=body, method=method)
        req.add_header("Content-Type", ctype)
        if auth:
            req.add_header("Authorization", "Bearer " + self.token)
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}

    def find(self, email: str) -> str | None:
        q = urllib.parse.urlencode({"username": email, "exact": "true"})
        found = self._call("GET", f"/admin/realms/{REALM}/users?{q}")
        return found[0]["id"] if found else None

    def create(self, person: dict) -> str:
        first, _, last = person["name"].partition(" ")
        self._call(
            "POST",
            f"/admin/realms/{REALM}/users",
            {
                "username": person["email"],
                "email": person["email"],
                "firstName": first,
                "lastName": last or first,
                "enabled": person["status"] != "deactivated",
                "emailVerified": True,
                "credentials": [{"type": "password", "value": DEMO_PASSWORD, "temporary": False}],
            },
        )
        return self.find(person["email"])

    def delete(self, user_id: str) -> None:
        self._call("DELETE", f"/admin/realms/{REALM}/users/{user_id}")


# ---- run ------------------------------------------------------------------------------------------------------------


def describe(purge: bool) -> str:
    people, projects = plan_people(), plan_projects()
    if purge:
        return (
            f"PURGE plan: delete Keycloak users, accounts, audit entries at *{DEMO_DOMAIN}; delete "
            f"{len(projects)} demo projects ({', '.join(p['name'] for p in projects)}) and their memberships."
        )
    lines = [
        f"SEED plan: {len(people)} people (password {DEMO_PASSWORD!r}), {len(projects)} projects, created by {ADA_EMAIL}"
    ]
    lines += [f"  person  {p['email']:<34} {p['name']:<26} {p['role']:<14} {p['status']}" for p in people]
    lines += [
        f"  project {p['name']:<28} members: {', '.join(m.replace(DEMO_DOMAIN, '') for m in p['members'])}"
        for p in projects
    ]
    return "\n".join(lines)


def main(argv=None, env=None) -> int:
    env = os.environ if env is None else env
    ap = argparse.ArgumentParser(description="Seed (or purge) dummy people and projects. DEV ONLY.")
    ap.add_argument("--yes", action="store_true", help="required to write anything")
    ap.add_argument("--purge", action="store_true", help="remove only what this script made")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, never connect")
    args = ap.parse_args(argv)

    kc_url = env.get("KEYCLOAK_URL", "http://localhost:8080")
    db_url = env.get("SEED_DB_URL", "postgresql://playground:playground@localhost:5433/playground")
    check_safety(kc_url, db_url, env)
    print(describe(args.purge))
    if args.dry_run or not args.yes:
        print("Nothing written." + ("" if args.yes or args.dry_run else " Add --yes to do it."))
        return 0

    import psycopg
    from psycopg.types.json import Json  # noqa: F401  (json is passed as text and cast in SQL)

    kc = Keycloak(kc_url, env.get("KEYCLOAK_ADMIN", "admin"), env.get("KEYCLOAK_ADMIN_PASSWORD", "admin"))
    people, projects = plan_people(), plan_projects()
    with psycopg.connect(db_url) as conn:
        if args.purge:
            removed_kc = 0
            for p in people:
                uid = kc.find(p["email"])
                if uid:
                    kc.delete(uid)
                    removed_kc += 1
            counts = {}
            for sql, params in purge_statements([p["email"] for p in people], project_ids()):
                cur = conn.execute(sql, params)
                counts[sql.split()[2]] = cur.rowcount
            print(f"Purged: keycloak users {removed_kc}, " + ", ".join(f"{k} {v}" for k, v in counts.items()))
            return 0

        def lookup(email):
            row = conn.execute("SELECT id, name, email FROM accounts WHERE email = %s", (email,)).fetchone()
            return {"id": row[0], "name": row[1], "email": row[2]} if row else None

        ada, maya = lookup(ADA_EMAIL), lookup(MAYA_EMAIL)
        if not ada:
            print(f"WARNING: {ADA_EMAIL} has no account yet (sign in once as admin). Nothing written.")
            return 1
        if not maya:
            print(f"WARNING: {MAYA_EMAIL} has no account yet (sign in once as maya). Projects skip her.")
        kc_ids, created = {}, 0
        for p in people:
            uid = kc.find(p["email"])
            if not uid:
                uid, created = kc.create(p), created + 1
            kc_ids[p["email"]] = uid
        n = {"accounts": 0, "audit_entries": 0, "projects": 0, "memberships": 0}
        for sql, params in sql_statements(people, projects, ada, maya, kc_ids):
            n[sql.split()[2]] += conn.execute(sql, params).rowcount
        print(f"Done: keycloak users created {created}, " + ", ".join(f"{k} added {v}" for k, v in n.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
