"""Tests for vcycle.py. Run from this folder: python3 -m unittest test_vcycle"""

import io
import json
import re
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "vbench-uc" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "vbench-at" / "scripts"))
import test_uc_tool as tuc  # noqa: E402  (its fixture: a small repo, and a use case to create in it)
import vcycle as v  # noqa: E402

rq, u = tuc.rq, tuc.u


def run_uc(root, *args, **kw):
    return tuc.run(root, *args, **kw)


def vc(root, *args):
    out = io.StringIO()
    with redirect_stdout(out):
        code = v.main(["--root", str(root), "--tests-dir", "tests", *args])
    return code, out.getvalue()


def make_uc(rules=None, criteria=("AC-1",)):
    root = tuc.make_root()
    new = dict(tuc.NEW, criteria=list(criteria), rules=rules or [])
    run_uc(root, "create", stdin=json.dumps(new))
    return root


def put(root, name, text, folder="tests/unit"):
    p = root / folder / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def uc_file(root):
    return next((root / "docs/usecases").glob("UC-E1-*.md"))


def unstamp(root):
    p = uc_file(root)
    p.write_text(re.sub(r"\n\s+reviewed: [0-9a-f]{7}", "", p.read_text()))


def row(out, level):
    return next((ln for ln in out.splitlines() if ln.startswith(level)), "")


class Tests(unittest.TestCase):
    def test_a_proven_use_case_passes(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => {});\n")
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 0, out)
        self.assertIn("UC-E1", out)
        self.assertIn("ok", row(out, "Criteria"))

    def test_a_criterion_with_no_test_fails_and_is_named(self):
        root = make_uc()
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL", row(out, "Criteria"))
        self.assertIn("AC-1", row(out, "Criteria"))

    def test_a_criterion_covered_only_by_the_stack_run_warns_and_fails_when_strict(self):
        root = make_uc()
        put(root, "a.it.ts", "it('x (Verifies AC-1)', () => {});\n")
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 0, out)
        self.assertIn("warn", row(out, "Criteria"))
        self.assertIn("stack run", row(out, "Criteria"))
        self.assertEqual(vc(root, "UC-E1", "--strict")[0], 1)

    def test_a_criterion_deferred_to_r2_is_not_a_failure(self):
        root = make_uc()
        rows = rq.read_rows(root / rq.PATHS["ac"])
        rows[0]["notes"] = "R2 hardening: deferred by decision 13."
        rq.write_rows(root / rq.PATHS["ac"], rq.AC_COLS, rows)
        code, out = vc(root, "UC-E1")
        self.assertIn("deferred", row(out, "Criteria"))
        self.assertNotIn("FAIL", row(out, "Criteria"))

    def test_a_listed_rule_needs_a_test(self):
        root = make_uc(rules=["RULE-E1"])
        (root / "docs/domain/ontology/RULE-E1-x.md").write_text("```yaml\nid: RULE-E1\ntype: rule\nname: x\n```\n")
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => {});\n")
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL", row(out, "Rules"))
        self.assertIn("RULE-E1", row(out, "Rules"))
        put(root, "test_r.py", '@pytest.mark.rule("RULE-E1")\ndef test_x():\n    pass\n')
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 0, out)
        self.assertIn("ok", row(out, "Rules"))

    def test_an_unstamped_use_case_warns_and_fails_when_strict(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => {});\n")
        unstamp(root)
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 0, out)
        self.assertIn("warn", row(out, "Review"))
        self.assertIn("not stamped", row(out, "Review"))
        self.assertEqual(vc(root, "UC-E1", "--strict")[0], 1)

    def test_a_stamped_use_case_is_ok_and_a_changed_criterion_makes_it_stale_and_fail(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => {});\n")
        self.assertIn("ok", row(vc(root, "UC-E1")[1], "Review"))
        rows = rq.read_rows(root / rq.PATHS["ac"])
        rows[0]["then"] = "something else entirely"
        rq.write_rows(root / rq.PATHS["ac"], rq.AC_COLS, rows)
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL", row(out, "Review"))
        self.assertIn("stale", row(out, "Review"))

    def test_a_lost_analysis_element_fails(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => {});\n")
        p = uc_file(root)
        p.write_text(p.read_text() + "\n## Analysis\n\n### Revision 1\n\n- A1 (object): E\n- A2 (step): s\n"
                     "\n## Design\n\n- D1 (aggregate): E\n\n## Changes from analysis to design\n\n- A1 kept -> D1\n")
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL", row(out, "Analysis"))
        self.assertIn("A2", row(out, "Analysis"))

    def test_a_linked_diagram_that_does_not_exist_is_a_warning(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => {});\n")
        p = uc_file(root)
        p.write_text(p.read_text() + "\nSee diagrams/UC-E1-move-design-sequence.puml\n")
        code, out = vc(root, "UC-E1")
        self.assertIn("warn", row(out, "Design"))
        self.assertIn("does not exist", row(out, "Design"))

    def test_json_has_the_rows_the_verdict_and_the_commit(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => {});\n")
        code, out = vc(root, "UC-E1", "--json")
        data = json.loads(out)
        self.assertEqual(data["uc"], "UC-E1")
        self.assertIn("commit", data)
        self.assertEqual(data["ok"], code == 0)
        self.assertTrue(all({"level", "spec", "proof", "status", "detail"} <= set(r) for r in data["rows"]))

    def test_all_checks_every_use_case_and_exits_1_if_any_fails(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => {});\n")
        run_uc(root, "create", stdin=json.dumps(dict(tuc.NEW, area="P", criteria=[], satisfies=["FR-2"])))
        code, out = vc(root, "--all")
        self.assertIn("UC-E1", out)
        self.assertIn("UC-P1", out)
        self.assertIn("USE CASES", out.upper())

    def test_an_unknown_use_case_is_an_error(self):
        root = make_uc()
        code, out = vc(root, "UC-Z9")
        self.assertEqual(code, 1)
        self.assertIn("No use case UC-Z9", out)


if __name__ == "__main__":
    unittest.main()
