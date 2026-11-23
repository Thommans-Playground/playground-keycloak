"""Tests for adopt_tool.py. Run from this folder: python3 -m unittest test_adopt_tool"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "_vbench"))
import adopt_tool as a  # noqa: E402
import config  # noqa: E402


def put(root, rel, text=""):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return p


def make_repo():
    root = Path(tempfile.mkdtemp())
    put(root, "api/pyproject.toml", '[project]\ndependencies = ["fastapi", "pytest", "ruff", "mypy"]\n')
    put(root, "api/tests/test_x.py", 'import pytest\n@pytest.mark.ac("AC-1")\ndef test_a():\n    pass\n')
    put(root, "api/tests/test_y.py", "def test_b():\n    pass\n")
    put(root, "web/package.json", json.dumps({"dependencies": {"next": "1"}, "devDependencies": {"typescript": "5", "vitest": "1"}, "scripts": {"test": "vitest run", "lint": "eslint", "build": "next build"}}))
    put(root, "web/src/a.test.ts", "// Verifies AC-2\n")
    put(root, "docs/requirements.md", "FR-1 The system shall do a thing. FR-2 and UC-1.\n")
    put(root, "docs/adr/0001-first.md", "# one\n")
    put(root, ".github/workflows/ci.yml", "on: push\n")
    put(root, "node_modules/junk/package.json", "{}")
    return root


def snapshot(root):
    return sorted((str(p.relative_to(root)), p.stat().st_mtime_ns) for p in Path(root).rglob("*") if p.is_file())


class Tests(unittest.TestCase):
    def test_it_finds_stacks_tests_docs_and_ci(self):
        d = a.discover(make_repo())
        names = {s["path"]: s for s in d["stacks"]}
        self.assertEqual(names["api"]["framework"], "fastapi")
        self.assertEqual(names["api"]["test_framework"], "pytest")
        self.assertEqual(names["web"]["test_framework"], "vitest")
        self.assertEqual(names["web"]["tests"], "npm --prefix web test")
        self.assertEqual(d["tests"]["files"], {"python": 2, "js": 1})
        self.assertEqual(sum(d["tests"]["traced_to_ids"].values()), 2)
        self.assertIn(".github/workflows/ci.yml", d["ci"])
        self.assertIn("docs/requirements.md", d["docs"]["requirement_like"])
        self.assertIn("docs/adr", d["docs"]["adr_folders"])
        self.assertEqual(d["docs"]["ids_in_docs"]["FR"]["count"], 2)

    def test_it_skips_dependency_folders(self):
        d = a.discover(make_repo())
        self.assertNotIn("node_modules", json.dumps(d["stacks"]))

    def test_it_proposes_a_config_and_never_writes_one(self):
        root = make_repo()
        before = snapshot(root)
        d = a.discover(root)
        self.assertEqual(snapshot(root), before, "discover must not write or change any file")
        self.assertNotIn("test_stack", d["proposed_vbench_json"])  # pytest and vitest both in use
        self.assertEqual(d["proposed_vbench_json"]["adoption"], {"default": "legacy"})
        self.assertFalse((Path(root) / "vbench.json").exists())

    def test_an_empty_project_gets_gaps_and_a_ladder_that_says_what_to_do_first(self):
        d = a.discover(Path(tempfile.mkdtemp()))
        self.assertIn("no tests found", d["gaps"])
        self.assertIn("no requirement or use case documents found", d["gaps"])
        states = {s["step"][0]: s["state"] for s in d["ladder"]}
        self.assertIn("needs a stack", states["1"])
        self.assertIn("characterisation", states["2"])

    def test_it_reads_git_habits(self):
        root = make_repo()
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        for cmd in (["init", "-q", "-b", "main"], ["add", "."], ["commit", "-qm", "feat(x): one"], ["commit", "-q", "--allow-empty", "-m", "stuff"]):
            subprocess.run(["git", "-C", str(root), *cmd], env=env, check=True, capture_output=True)
        d = a.discover(root)
        self.assertEqual(d["git"]["base_branch"], "main")
        self.assertEqual(d["git"]["conventional_commits"], "1 of 2")

    def test_the_report_and_json_forms_run(self):
        root = make_repo()
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(a.main(["discover", str(root)]), 0)
        self.assertIn("A proposed vbench.json", out.getvalue())
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(a.main(["discover", str(root), "--json"]), 0)
        self.assertIn("proposed_vbench_json", json.loads(out.getvalue()))
        self.assertEqual(a.main(["discover", "/no/such/folder"]), 2)


def git_init(root, branches=(), commits=("feat(x): one",)):
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    run = lambda *c: subprocess.run(["git", "-C", str(root), *c], env=env, check=True, capture_output=True)
    run("init", "-q", "-b", "main")
    put(root, "README.md", "x")
    run("add", ".")
    for m in commits:
        run("commit", "-q", "--allow-empty", "-m", m)
    for b in branches:
        run("branch", b)


def loads_cleanly(testcase, d):
    """The proposal is written to a temp vbench.json and read by the harness's own loader."""
    tmp = Path(tempfile.mkdtemp())
    (tmp / "vbench.json").write_text(json.dumps(d["proposed_vbench_json"], indent=2))
    return config.load(tmp)


class More(unittest.TestCase):
    def test_every_proposal_is_accepted_by_the_config_loader(self):
        swift = Path(tempfile.mkdtemp())
        put(swift, "App.xcodeproj/project.pbxproj", "")
        put(swift, "Sources/A.swift", "")
        put(swift, "Tests/ATests.swift", "")
        node = Path(tempfile.mkdtemp())
        put(node, "package.json", json.dumps({"devDependencies": {"vitest": "1"}, "scripts": {"test": "vitest run"}}))
        layered = Path(tempfile.mkdtemp())
        put(layered, "pyproject.toml", '[project]\ndependencies=["pytest"]\n[tool.ruff]\n')
        put(layered, "app/domain/x.py")
        put(layered, "app/adapters/y.py")
        put(layered, "tests/test_architecture.py", "")
        kc = Path(tempfile.mkdtemp())
        put(kc, "docker-compose.yml", "services:\n  keycloak:\n    image: quay.io/keycloak/keycloak\n")
        for root in (make_repo(), Path(tempfile.mkdtemp()), swift, node, layered, kc):
            cfg = loads_cleanly(self, a.discover(root))
            self.assertIn("core", cfg["packs"])
        self.assertEqual(loads_cleanly(self, a.discover(layered))["packs"], ["core", "ddd"])
        self.assertEqual(a.discover(make_repo())["proposed_vbench_json"]["packs"], ["core"])
        self.assertIn("keycloak", a.discover(kc)["proposed_vbench_json"]["packs"])
        self.assertNotIn("security", a.discover(kc)["proposed_vbench_json"]["packs"])

    def test_id_families_have_a_count_and_a_role_and_patterns_follow_the_tests(self):
        root = Path(tempfile.mkdtemp())
        put(root, "docs/req.md", "STK-1 STK-2 FR-1 FR-2 FR-3 US-1 UC-P1 UC-P2 TC-1 TC-2 TC-3")
        put(root, "tests/test_a.py", 'import pytest\n@pytest.mark.tc("TC-1")\ndef test_a():\n    pass\n# Covers TC-2, TC-3\ndef test_tc_3_works():\n    pass\n')
        d = a.discover(root)
        ids = d["docs"]["ids_in_docs"]
        self.assertEqual(ids["FR"]["count"], 3)
        self.assertEqual(ids["FR"]["role"], "requirement")
        self.assertEqual(ids["US"]["role"], "story")
        self.assertEqual(ids["UC"]["role"], "use case")
        self.assertEqual(ids["TC"]["role"], "test case")
        fam = d["tests"]["id_families"]["TC"]
        self.assertEqual((fam["marker"], fam["comment"]), (1, 2))
        self.assertGreaterEqual(fam["title"], 1)
        pats = d["proposed_vbench_json"]["id_patterns"]
        self.assertEqual(pats["criterion"], r"TC-\d+")
        self.assertEqual(pats["usecase"], r"UC-[A-Z]\d+")
        self.assertIn("FR-", pats["requirement"])
        self.assertIn("STK-", pats["requirement"])
        loads_cleanly(self, d)

    def test_branch_styles_are_counted_and_the_dominant_one_named(self):
        root = Path(tempfile.mkdtemp())
        git_init(root, ["feature/a", "feature/b", "bugfix/c", "uc-12-login", "feat/d", "random"])
        g = a.discover(root)["git"]
        self.assertEqual(g["branch_styles"]["feature/"], 2)
        self.assertEqual(g["branch_styles"]["bugfix/"], 1)
        self.assertEqual(g["branch_styles"]["uc-"], 1)
        self.assertEqual(g["dominant_branch_style"], "feature/")
        self.assertEqual(g["typed_branches"], "5 of 7")

    def test_existing_agent_skills_are_listed_with_a_collision_warning(self):
        root = Path(tempfile.mkdtemp())
        put(root, ".claude/skills/v-model-trace/SKILL.md")
        put(root, ".agents/skills/ddd-helper/SKILL.md")
        put(root, ".claude/skills/vbench-req/SKILL.md")
        d = a.discover(root)
        self.assertEqual(d["agent_skills"][".claude/skills"], ["v-model-trace", "vbench-req"])
        self.assertEqual(d["agent_skills"][".agents/skills"], ["ddd-helper"])
        self.assertTrue(any("collide" in w for w in d["warnings"]))
        self.assertFalse(any("collide" in w for w in a.discover(Path(tempfile.mkdtemp()))["warnings"]))

    def test_other_doc_folders_and_their_markdown_are_counted(self):
        root = Path(tempfile.mkdtemp())
        put(root, "study-guide/a.md")
        put(root, "study-guide/b.md")
        put(root, "report/r.md")
        put(root, "notes/n.md")
        put(root, "design/d.md")
        put(root, "src/readme.md")
        d = a.discover(root)["docs"]
        self.assertEqual(d["doc_folders"], {"design": 1, "notes": 1, "report": 1, "study-guide": 2})

    def test_swift_is_unsupported_not_a_gap_and_gets_no_invented_commands(self):
        root = Path(tempfile.mkdtemp())
        put(root, "App.xcodeproj/project.pbxproj", "")
        put(root, "Sources/A.swift", "")
        put(root, "Tests/ATests.swift", "")
        d = a.discover(root)
        self.assertTrue(any(u["language"] == "swift" for u in d["unsupported_stacks"]))
        self.assertIn("pytest, vitest, playwright", d["unsupported_stacks"][0]["reason"])
        self.assertNotIn("no tests found", d["gaps"])
        for s in d["proposed_vbench_json"]["stacks"].values():
            self.assertEqual(set(s), {"path", "language"})
        self.assertNotIn("test_stack", d["proposed_vbench_json"])

    def test_lint_and_typecheck_only_when_configured(self):
        root = Path(tempfile.mkdtemp())
        put(root, "a/pyproject.toml", '[project]\ndependencies=["pytest"]\n# we do not use ruff or mypy\n')
        put(root, "b/pyproject.toml", '[project]\ndependencies=["pytest"]\n[tool.ruff]\nline-length=100\n[tool.mypy]\nstrict=true\n')
        put(root, "c/requirements.txt", "pytest\nruff==0.5\n")
        s = {x["path"]: x for x in a.discover(root)["stacks"]}
        self.assertNotIn("lint", s["a"])
        self.assertNotIn("typecheck", s["a"])
        self.assertEqual(s["b"]["lint"], "ruff check b")
        self.assertEqual(s["b"]["typecheck"], "mypy b")
        self.assertIn("lint", s["c"])
        self.assertNotIn("typecheck", s["c"])

    def test_layers_without_enforcement_are_reported_as_such(self):
        root = Path(tempfile.mkdtemp())
        put(root, "src/domain/a.py")
        put(root, "src/application/b.py")
        put(root, "src/adapters/c.py")
        d = a.discover(root)
        self.assertEqual(d["layers"], ["adapters", "application", "domain"])
        self.assertIn("layers present but no test enforces them", " ".join(d["gaps"]))
        self.assertNotIn("no architecture test found", " ".join(d["gaps"]))
        self.assertEqual(d["proposed_vbench_json"]["packs"], ["core"])

    def test_test_stack_only_when_exactly_one_framework_is_in_use(self):
        d = a.discover(make_repo())  # pytest and vitest
        self.assertNotIn("test_stack", d["proposed_vbench_json"])
        self.assertIn("pytest", d["test_stack_note"])
        node = Path(tempfile.mkdtemp())
        put(node, "package.json", json.dumps({"devDependencies": {"vitest": "1"}, "scripts": {"test": "vitest run"}}))
        self.assertEqual(a.discover(node)["proposed_vbench_json"]["test_stack"], "vitest")

    def test_it_reads_this_repo_without_writing(self):
        repo = HERE.parents[3]
        before = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout
        loads_cleanly(self, a.discover(repo))
        after = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True).stdout
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
