"""Tests for scripts/purge-test-data.sh against a throwaway PostgreSQL container (hand made tables with the same names
and columns as the migrations). Needs docker.  python3 -m unittest scripts/test_purge_test_data.py"""

import os
import pathlib
import subprocess
import time
import unittest
import uuid

SCRIPT = str(pathlib.Path(__file__).with_name("purge-test-data.sh"))
SCHEMA = """
CREATE TABLE accounts (id text primary key, identity text, name text, email text, role text, status text, created timestamp, created_by text);
CREATE TABLE projects (id text primary key, name text, created_by text, created_at timestamp default now());
CREATE TABLE memberships (project_id text references projects(id), account_id text, added_by text, added_at timestamp default now());
CREATE TABLE audit_entries (id serial primary key, kind text default 'account', actor_id text, target_id text, action text, actor_email text, target_email text);
INSERT INTO accounts (id, name, email) VALUES
 ('t1','Integration Test','it-1700-ab12@example.test'),
 ('t2','Integration Throwaway','it-99-0f@example.test'),
 ('d1','Ada Demo','ada@demo.example.test'),
 ('r1','Maya','maya@example.test'),
 ('r2','Integration Test','real.person@example.test'),
 ('r3','Someone','it-1-ab@example.test');
INSERT INTO projects (id, name, created_by) VALUES
 ('p1','Mine1a2b3c4d','r1'), ('p2','Pendingabcdefgh12','r1'), ('p3','Apollo','d1'), ('p4','Mine','r1'), ('p5','Mine1A2B3C4D','r1');
INSERT INTO memberships (project_id, account_id) VALUES ('p1','t1'), ('p1','r1'), ('p3','d1'), ('p3','t2'), ('p4','r1');
INSERT INTO audit_entries (kind, actor_id, target_id, action) VALUES
 ('account','t1','t1','register'), ('account','r1','t2','approve'), ('project','r1','p1','create_project'),
 ('project','r1','p3','create_project'), ('account','r1','r1','register');
"""


def docker_ok() -> bool:
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=20).returncode == 0
    except Exception:
        return False


@unittest.skipUnless(docker_ok(), "docker is not available")
class PurgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.name = "purge-test-" + uuid.uuid4().hex[:8]
        subprocess.run(
            ["docker", "run", "--rm", "-d", "--name", cls.name, "-e", "POSTGRES_PASSWORD=x", "postgres:16"],
            check=True, capture_output=True,
        )
        for _ in range(60):
            if subprocess.run(["docker", "exec", cls.name, "pg_isready", "-U", "postgres"], capture_output=True).returncode == 0:
                time.sleep(1)  # the init server restarts once
                if subprocess.run(["docker", "exec", cls.name, "pg_isready", "-U", "postgres"], capture_output=True).returncode == 0:
                    break
            time.sleep(1)
        cls.psql = f"docker exec -i {cls.name} psql -U postgres -d postgres"

    @classmethod
    def tearDownClass(cls):
        subprocess.run(["docker", "rm", "-f", cls.name], capture_output=True)

    def sql(self, text):
        r = subprocess.run(self.psql.split() + ["-X", "-q", "-At", "-v", "ON_ERROR_STOP=1"], input=text, text=True, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def setUp(self):
        self.sql("DROP TABLE IF EXISTS memberships, audit_entries, projects, accounts;" + SCHEMA)

    def run_script(self, *args, **env):
        e = {**os.environ, "PURGE_TESTING": "1", "PURGE_PSQL_CMD": self.psql, **env}
        return subprocess.run([SCRIPT, *args], env=e, text=True, capture_output=True)

    def ids(self, table):
        return self.sql(f"SELECT string_agg(id::text, ',' ORDER BY id) FROM {table}")

    def test_dry_run_changes_nothing_and_counts(self):
        r = self.run_script("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("to remove: accounts=2 projects=2 memberships=3 audit_entries=3", r.stdout)
        self.assertEqual(self.ids("accounts"), "d1,r1,r2,r3,t1,t2")

    def test_yes_removes_only_test_rows_and_is_idempotent(self):
        r = self.run_script("--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.ids("accounts"), "d1,r1,r2,r3")
        self.assertEqual(self.ids("projects"), "p3,p4,p5")
        self.assertEqual(self.sql("SELECT count(*) FROM memberships"), "2")
        self.assertEqual(self.sql("SELECT string_agg(target_id, ',' ORDER BY id) FROM audit_entries"), "p3,r1")
        self.assertIn("remaining: accounts=4 projects=3 memberships=2 audit_entries=2", r.stdout)
        again = self.run_script("--yes")
        self.assertIn("to remove: accounts=0 projects=0 memberships=0 audit_entries=0", again.stdout)

    def test_requires_a_flag(self):
        self.assertEqual(self.run_script().returncode, 2)

    def test_refuses_production_and_remote_targets(self):
        for env in ({"ENVIRONMENT": "production"}, {"APP_ENV": "Prod"}, {"PGHOST": "db.example.com"},
                    {"DATABASE_URL": "postgresql://u:p@db.rds.amazonaws.com/x"}):
            r = self.run_script("--yes", **env)
            self.assertEqual(r.returncode, 3, env)
            self.assertIn("REFUSED", r.stderr)
        self.assertEqual(self.ids("accounts"), "d1,r1,r2,r3,t1,t2")

    def test_refuses_other_compose_project_and_swapped_command_without_flag(self):
        r = subprocess.run([SCRIPT, "--yes"], env={**os.environ, "COMPOSE_PROJECT_NAME": "playground-test"}, text=True, capture_output=True)
        self.assertEqual(r.returncode, 3)
        r = subprocess.run([SCRIPT, "--yes"], env={**os.environ, "PURGE_PSQL_CMD": "echo", "PURGE_TESTING": ""}, text=True, capture_output=True)
        self.assertEqual(r.returncode, 3)


if __name__ == "__main__":
    unittest.main()
