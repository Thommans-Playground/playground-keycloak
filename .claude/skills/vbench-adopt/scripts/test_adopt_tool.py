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
import adopt_tool as a  # noqa: E402


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
        self.assertEqual(names["web"]["tests"], "npm test")
        self.assertEqual(d["tests"]["files"], {"python": 2, "js": 1})
        self.assertEqual(sum(d["tests"]["traced_to_ids"].values()), 2)
        self.assertIn(".github/workflows/ci.yml", d["ci"])
        self.assertIn("docs/requirements.md", d["docs"]["requirement_like"])
        self.assertIn("docs/adr", d["docs"]["adr_folders"])
        self.assertEqual(d["docs"]["ids_in_docs"]["FR"], 2)

    def test_it_skips_dependency_folders(self):
        d = a.discover(make_repo())
        self.assertNotIn("node_modules", json.dumps(d["stacks"]))

    def test_it_proposes_a_config_and_never_writes_one(self):
        root = make_repo()
        before = snapshot(root)
        d = a.discover(root)
        self.assertEqual(snapshot(root), before, "discover must not write or change any file")
        self.assertEqual(d["proposed_vbench_json"]["test_stack"], "pytest")
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


if __name__ == "__main__":
    unittest.main()
