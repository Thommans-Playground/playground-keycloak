"""Unit tests for scripts/seed-demo.py. No stack needed:  python3 -m unittest scripts/test_seed_demo.py"""

import importlib.util
import io
import pathlib
import unittest
from contextlib import redirect_stdout

spec = importlib.util.spec_from_file_location("seed", pathlib.Path(__file__).with_name("seed-demo.py"))
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)

LOCAL = ("http://localhost:8080", "postgresql://u:p@127.0.0.1:5433/playground")


class PlanTest(unittest.TestCase):
    def test_emails_unique_and_demo_domain(self):
        emails = [p["email"] for p in seed.plan_people()]
        self.assertEqual(len(emails), len(set(emails)))
        self.assertTrue(all(e.endswith(seed.DEMO_DOMAIN) for e in emails))

    def test_mix_of_statuses_and_roles(self):
        people = seed.plan_people()
        statuses = [p["status"] for p in people]
        self.assertEqual(statuses.count("pending"), 1)
        self.assertEqual(statuses.count("deactivated"), 1)
        self.assertGreaterEqual(statuses.count("active"), 5)
        self.assertEqual([p["role"] for p in people].count("administrator"), 1)

    def test_project_members_exist_and_sizes(self):
        known = {p["email"] for p in seed.plan_people()} | {seed.MAYA_EMAIL}
        projects = seed.plan_projects()
        for pr in projects:
            self.assertTrue(2 <= len(pr["members"]) <= 5, pr["name"])
            self.assertEqual(len(pr["members"]), len(set(pr["members"])))
            self.assertTrue(set(pr["members"]) <= known, pr["name"])
        self.assertGreaterEqual(sum(seed.MAYA_EMAIL in p["members"] for p in projects), 2)

    def test_ids_deterministic(self):
        self.assertEqual(seed.plan_people(), seed.plan_people())
        self.assertEqual(len(set(seed.project_ids())), len(seed.PROJECTS))

    def test_statements_skip_missing_maya_and_never_touch_existing_accounts(self):
        ada = {"id": "a", "name": "Ada", "email": seed.ADA_EMAIL}
        stmts = seed.sql_statements(seed.plan_people(), seed.plan_projects(), ada, None, {})
        sqls = " ".join(s for s, _ in stmts)
        self.assertNotIn("UPDATE", sqls)
        self.assertNotIn("DELETE", sqls)
        for s, params in stmts:
            self.assertTrue(s.startswith("INSERT"))
            if "INTO accounts" in s:
                self.assertTrue(params[3].endswith(seed.DEMO_DOMAIN))
        members = [p for s, p in stmts if "INTO memberships" in s]
        self.assertTrue(all(m[2] == "a" for m in members))


class SafetyTest(unittest.TestCase):
    def test_local_ok(self):
        seed.check_safety(*LOCAL, {})

    def test_refuses_remote_keycloak(self):
        with self.assertRaises(SystemExit):
            seed.check_safety("https://kc.example.com", LOCAL[1], {})

    def test_refuses_remote_db(self):
        with self.assertRaises(SystemExit):
            seed.check_safety(LOCAL[0], "postgresql://u:p@db.rds.amazonaws.com/playground", {})

    def test_refuses_production(self):
        for var in ("ENVIRONMENT", "APP_ENV"):
            with self.assertRaises(SystemExit):
                seed.check_safety(*LOCAL, {var: "Production"})

    def test_yes_is_required(self):
        # Without --yes it prints the plan and returns before any connection (psycopg is not even imported).
        for argv in ([], ["--purge"], ["--dry-run", "--yes"]):
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(seed.main(argv, env={}), 0)
            self.assertIn("Nothing written", buf.getvalue())

    def test_main_refuses_remote_before_anything(self):
        with self.assertRaises(SystemExit):
            seed.main(["--yes"], env={"KEYCLOAK_URL": "http://kc.prod.example.com"})


class PurgeTest(unittest.TestCase):
    def test_only_demo_rows_selected(self):
        stmts = seed.purge_statements([], seed.project_ids())
        self.assertTrue(all(s.startswith("DELETE FROM") for s, _ in stmts))
        for s, params in stmts:
            self.assertTrue(any(isinstance(p, list) or str(p).endswith(seed.DEMO_DOMAIN) for p in params))
            self.assertIn("WHERE", s)
        accounts = [(s, p) for s, p in stmts if s.startswith("DELETE FROM accounts")][0]
        self.assertEqual(accounts[1], ("%" + seed.DEMO_DOMAIN,))
        self.assertNotIn(
            "example.test", "".join(str(p) for _, ps in stmts for p in ps).replace("demo.example.test", "")
        )


if __name__ == "__main__":
    unittest.main()
