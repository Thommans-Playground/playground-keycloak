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
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
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
        put(root, "a.it.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
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
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL", row(out, "Rules"))
        self.assertIn("RULE-E1", row(out, "Rules"))
        put(root, "test_r.py", '@pytest.mark.rule("RULE-E1")\ndef test_x():\n    assert 1 + 1 == 2\n')
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 0, out)
        self.assertIn("ok", row(out, "Rules"))

    def test_an_unstamped_use_case_warns_and_fails_when_strict(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        unstamp(root)
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 0, out)
        self.assertIn("warn", row(out, "Review"))
        self.assertIn("not stamped", row(out, "Review"))
        self.assertEqual(vc(root, "UC-E1", "--strict")[0], 1)

    def test_a_stamped_use_case_is_ok_and_a_changed_criterion_makes_it_stale_and_fail(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
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
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        p = uc_file(root)
        p.write_text(p.read_text() + "\n## Analysis\n\n### Revision 1\n\n- A1 (object): E\n- A2 (step): s\n"
                     "\n## Design\n\n- D1 (aggregate): E\n\n## Changes from analysis to design\n\n- A1 kept -> D1\n")
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL", row(out, "Analysis"))
        self.assertIn("A2", row(out, "Analysis"))

    def test_a_linked_diagram_that_does_not_exist_is_a_warning(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        p = uc_file(root)
        p.write_text(p.read_text() + "\nSee diagrams/UC-E1-move-design-sequence.puml\n")
        code, out = vc(root, "UC-E1")
        self.assertIn("warn", row(out, "Design"))
        self.assertIn("does not exist", row(out, "Design"))

    def test_json_has_the_rows_the_verdict_and_the_commit(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        code, out = vc(root, "UC-E1", "--json")
        data = json.loads(out)
        self.assertEqual(data["uc"], "UC-E1")
        self.assertIn("commit", data)
        self.assertEqual(data["ok"], code == 0)
        self.assertTrue(all({"level", "spec", "proof", "status", "detail"} <= set(r) for r in data["rows"]))

    def test_all_checks_every_use_case_and_exits_1_if_any_fails(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
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


def mark_security(root, note="security SEC-CONF-1"):
    """The use case's one criterion becomes a security criterion: its Notes start with `security`."""
    path = root / rq.PATHS["ac"]
    rows = rq.read_rows(path)
    for r in rows:
        if r["id"] == "AC-1":
            r["notes"] = note
    rq.write_rows(path, rq.AC_COLS, rows)


class SecurityRow(unittest.TestCase):
    def test_a_use_case_with_no_security_criterion_warns_that_it_was_not_probed(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        _, out = vc(root, "UC-E1")
        self.assertIn("warn", row(out, "Security"))
        self.assertIn("/vbench-security-test UC-E1", row(out, "Security"))

    def test_a_security_criterion_with_no_test_fails(self):
        root = make_uc()
        mark_security(root)
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 1)
        self.assertIn("FAIL", row(out, "Security"))
        self.assertIn("AC-1", row(out, "Security"))

    def test_a_security_criterion_with_a_test_is_ok(self):
        root = make_uc()
        mark_security(root)
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        _, out = vc(root, "UC-E1")
        self.assertIn("ok", row(out, "Security"))

    def test_a_security_criterion_covered_only_by_the_stack_run_warns(self):
        root = make_uc()
        mark_security(root)
        put(root, "a.it.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        _, out = vc(root, "UC-E1")
        self.assertIn("warn", row(out, "Security"))

    def test_the_security_row_comes_before_the_review_row(self):
        root = make_uc()
        _, out = vc(root, "UC-E1")
        levels = [ln.split()[0] for ln in out.splitlines() if ln.split() and ln.split()[0] in ("Slices", "Security", "Review")]
        self.assertEqual(levels, ["Slices", "Security", "Review"])


def set_ac(root, **fields):
    """Change fields of the one criterion, AC-1."""
    path = root / rq.PATHS["ac"]
    rows = rq.read_rows(path)
    for r in rows:
        if r["id"] == "AC-1":
            r.update(fields)
    rq.write_rows(path, rq.AC_COLS, rows)


def drop_ac(root):
    path = root / rq.PATHS["ac"]
    rq.write_rows(path, rq.AC_COLS, [r for r in rq.read_rows(path) if r["id"] != "AC-1"])


PY = '@pytest.mark.ac("AC-1")\ndef test_x():\n    assert 1 + 1 == 2\n'


class FalseGreens(unittest.TestCase):
    """Each of these used to say ok while nothing was proved (found by a red-team review, Nov 2026)."""

    def fails(self, root, level="Criteria"):
        code, out = vc(root, "UC-E1")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL", row(out, level), out)
        return out

    def test_a_retired_criterion_is_not_a_green_use_case(self):
        root = make_uc()
        set_ac(root, status="retired")
        self.assertIn("AC-1", row(self.fails(root), "Criteria"))

    def test_a_listed_criterion_that_is_gone_is_not_a_green_use_case(self):
        root = make_uc()
        drop_ac(root)
        self.assertIn("AC-1", row(self.fails(root), "Criteria"))

    def test_a_test_that_is_commented_out_by_a_js_runner_word_does_not_count(self):
        for body in ("xit('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n",
                     "it.todo('x (Verifies AC-1)');\n",
                     "test.fixme('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n",
                     "xdescribe('x (Verifies AC-1)', () => {});\n",
                     "it.skipIf(true)('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n",
                     "it.runIf(false)('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n"):
            root = make_uc()
            put(root, "a.test.ts", body)
            with self.subTest(body=body):
                self.fails(root)

    def test_a_python_marker_that_does_not_sit_on_a_running_test_does_not_count(self):
        for name, body in (
            ("a helper, not a test", '@pytest.mark.ac("AC-1")\ndef helper():\n    assert 1 + 1 == 2\n'),
            ("a skip above the marker", '@pytest.mark.skip\n@pytest.mark.ac("AC-1")\ndef test_x():\n    assert 1 + 1 == 2\n'),
            ("a whole-module skip", 'pytestmark = pytest.mark.skip\n' + PY),
            ("a skip inside the body", '@pytest.mark.ac("AC-1")\ndef test_x():\n    pytest.skip("later")\n    assert 1 + 1 == 2\n'),
            ("an expected failure", '@pytest.mark.ac("AC-1")\n@pytest.mark.xfail\ndef test_x():\n    assert 1 + 1 == 2\n'),
            ("a marker in a docstring", 'DOC = """\n@pytest.mark.ac("AC-1")\ndef test_x():\n    assert 1 + 1 == 2\n"""\n'),
        ):
            root = make_uc()
            put(root, "test_a.py", body)
            with self.subTest(name):
                self.fails(root)

    def test_a_test_with_no_assertion_is_a_warning_not_a_proof(self):
        for name, fname, body in (("js", "a.test.ts", "it('x (Verifies AC-1)', () => {});\n"),
                                  ("python", "test_a.py", '@pytest.mark.ac("AC-1")\ndef test_x():\n    pass\n'),
                                  ("trivial assert", "test_a.py", '@pytest.mark.ac("AC-1")\ndef test_x():\n    assert True\n')):
            root = make_uc()
            put(root, fname, body)
            _, out = vc(root, "UC-E1")
            with self.subTest(name):
                self.assertIn("warn", row(out, "Criteria"), out)
                self.assertIn("no assertion", row(out, "Criteria"))

    def test_a_stale_review_hash_on_a_test_fails(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1 [reviewed deadbee])', () => { expect(1).toBe(1); });\n")
        out = self.fails(root)
        self.assertIn("stale", row(out, "Criteria"))

    def test_one_tag_that_names_several_criteria_is_only_a_warning(self):
        root = make_uc(criteria=("AC-1",))
        put(root, "a.test.ts", "it('x (Verifies AC-1, AC-2)', () => { expect(1).toBe(1); });\n")
        _, out = vc(root, "UC-E1")
        self.assertIn("warn", row(out, "Criteria"), out)
        self.assertIn("combined", row(out, "Criteria"))

    def test_a_deferral_to_r2_needs_a_decision(self):
        root = make_uc()
        set_ac(root, notes="R2 someday")
        _, out = vc(root, "UC-E1")
        self.assertIn("warn", row(out, "Criteria"), out)
        self.assertIn("no decision", row(out, "Criteria"))
        set_ac(root, notes="R2 (decision 13)")
        _, out = vc(root, "UC-E1")
        self.assertIn("ok", row(out, "Criteria"), out)

    def test_a_security_criterion_is_found_by_its_sec_id_wherever_the_note_puts_it(self):
        root = make_uc()
        set_ac(root, notes="proves a refusal, SEC-ATHZ-1")
        self.fails(root, "Security")

    def test_a_retired_security_criterion_is_flagged(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        set_ac(root, notes="security SEC-CONF-1", status="retired")
        _, out = vc(root, "UC-E1")
        self.assertIn("retired", row(out, "Security"), out)

    def test_a_use_case_with_no_design_is_a_warning_even_without_analysis(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        _, out = vc(root, "UC-E1")
        self.assertIn("warn", row(out, "Design"), out)

    def test_all_does_not_hide_a_use_case_whose_header_is_broken(self):
        root = make_uc()
        run_uc(root, "create", stdin=json.dumps(dict(tuc.NEW, area="P", criteria=[])))
        next((root / "docs/usecases").glob("UC-P1-*.md")).write_text("garbage")
        code, out = vc(root, "--all")
        self.assertEqual(code, 1, out)
        self.assertIn("UC-P1", out)

    def test_all_with_no_use_case_is_not_a_pass(self):
        root = tuc.make_root()
        code, out = vc(root, "--all")
        self.assertEqual(code, 1, out)
        self.assertIn("0 checked", out)

    def test_the_result_line_counts_the_warnings_it_hides(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        _, out = vc(root, "UC-E1")
        self.assertRegex(out, r"RESULT UC-E1: ok with \d+ warning")


def configure(root, **settings):
    """Lay settings over the fixture's vbench.json (adoption, packs, results...)."""
    f = root / "vbench.json"
    data = json.loads(f.read_text())
    data.update(settings)
    f.write_text(json.dumps(data))


def junit(root, cases, name="results.xml"):
    """A JUnit XML file. cases: (classname, name, outcome) with outcome passed, failed or skipped."""
    body = ""
    for cls, nm, outcome in cases:
        inner = {"passed": "", "failed": "<failure message=\"boom\"/>", "skipped": "<skipped/>"}[outcome]
        body += f'<testcase classname="{cls}" name="{nm}">{inner}</testcase>'
    (root / name).write_text(f'<?xml version="1.0"?><testsuites><testsuite name="s">{body}</testsuite></testsuites>')
    return name


class Adoption(unittest.TestCase):
    """A strangler: legacy areas are observed, adopting ones warn, adopted ones fail (ADR 0019)."""

    def untested(self, **settings):
        root = make_uc()  # a use case with a criterion and no test: a FAIL when adopted
        configure(root, **settings)
        return root

    def test_the_default_is_adopted_so_a_gap_fails(self):
        code, out = vc(self.untested(), "UC-E1")
        self.assertEqual(code, 1, out)

    def test_a_legacy_area_is_observed_not_failed(self):
        code, out = vc(self.untested(adoption={"default": "legacy"}), "UC-E1")
        self.assertEqual(code, 0, out)
        self.assertIn("legacy", row(out, "Criteria"))
        self.assertNotIn("FAIL", row(out, "Criteria"))

    def test_an_adopting_area_turns_a_failure_into_a_warning(self):
        code, out = vc(self.untested(adoption={"default": "adopting"}), "UC-E1")
        self.assertEqual(code, 0, out)
        self.assertIn("warn", row(out, "Criteria"))
        self.assertIn("adopting", row(out, "Criteria"))

    def test_one_area_can_be_adopted_while_the_rest_is_legacy(self):
        code, out = vc(self.untested(adoption={"default": "legacy", "E": "adopted"}), "UC-E1")
        self.assertEqual(code, 1, out)

    def test_the_json_says_how_far_the_area_is(self):
        _, out = vc(self.untested(adoption={"default": "legacy"}), "UC-E1", "--json")
        self.assertEqual(json.loads(out)["adoption"], "legacy")


class Baseline(unittest.TestCase):
    """Hold the line: today's known gaps do not fail, a new or changed gap does."""

    def test_a_gap_in_the_baseline_warns_and_a_new_one_still_fails(self):
        root = make_uc()
        self.assertEqual(vc(root, "--all", "--baseline", "write")[0], 1)  # writing it reports, it never hides the run
        self.assertTrue((root / ".claude/vbench-baseline.json").is_file())
        code, out = vc(root, "--all")
        self.assertEqual(code, 0, out)
        self.assertIn("known gap", out)
        run_uc(root, "create", stdin=json.dumps(dict(tuc.NEW, area="P", criteria=["AC-1"])))  # a new use case, a new gap
        code, out = vc(root, "--all")
        self.assertEqual(code, 1, out)

    def test_a_gap_whose_detail_changed_is_new_again(self):
        root = make_uc()
        vc(root, "--all", "--baseline", "write")
        put(root, "a.test.ts", "it('x (Verifies AC-1 [reviewed deadbee])', () => { expect(1).toBe(1); });\n")  # now stale
        code, out = vc(root, "--all")
        self.assertEqual(code, 1, out)

    def test_no_baseline_ignores_the_file(self):
        root = make_uc()
        vc(root, "--all", "--baseline", "write")
        self.assertEqual(vc(root, "--all", "--no-baseline")[0], 1)


class Packs(unittest.TestCase):
    def test_a_pack_that_is_off_has_no_rows(self):
        root = make_uc()
        configure(root, packs=["core"])
        _, out = vc(root, "UC-E1")
        for level in ("Security", "Design", "Rules", "Analysis"):
            self.assertEqual(row(out, level), "", level)
        self.assertIn("ok", row(out, "Requirements") + row(out, "Criteria") + "ok")

    def test_all_packs_on_is_the_default(self):
        _, out = vc(make_uc(), "UC-E1")
        self.assertIn("Security", out)
        self.assertIn("Design", out)


class SmallTier(unittest.TestCase):
    def test_a_small_change_needs_no_analysis_or_freeze(self):
        root = make_uc()
        f = uc_file(root)
        f.write_text(f.read_text().replace("id: UC-E1\n", "id: UC-E1\ntier: small\n", 1))
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        _, out = vc(root, "UC-E1")
        self.assertIn("ok", row(out, "Analysis"), out)
        self.assertIn("small", row(out, "Analysis"))

    def test_the_default_tier_still_asks_for_the_analysis(self):
        _, out = vc(make_uc(), "UC-E1")
        self.assertIn("warn", row(out, "Analysis"), out)


class TestResults(unittest.TestCase):
    """With a JUnit file, 'has a test' becomes 'the test passed'."""

    def setUp(self):
        self.root = make_uc()
        put(self.root, "test_a.py", PY, folder="tests/unit")

    def run_with(self, cases):
        return vc(self.root, "UC-E1", "--results", junit(self.root, cases))

    def test_a_passing_test_proves_it(self):
        code, out = self.run_with([("tests.unit.test_a", "test_x", "passed")])
        self.assertIn("ok", row(out, "Criteria"), out)

    def test_a_failing_test_fails_the_criterion(self):
        code, out = self.run_with([("tests.unit.test_a", "test_x", "failed")])
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL", row(out, "Criteria"))
        self.assertIn("failed", row(out, "Criteria"))

    def test_a_test_with_no_result_is_a_warning(self):
        _, out = self.run_with([("tests.unit.test_other", "test_y", "passed")])
        self.assertIn("warn", row(out, "Criteria"), out)
        self.assertIn("no result", row(out, "Criteria"))

    def test_a_skipped_test_is_not_a_pass(self):
        _, out = self.run_with([("tests.unit.test_a", "test_x", "skipped")])
        self.assertIn("warn", row(out, "Criteria"), out)

    def test_without_results_the_trace_says_it_checks_existence_only(self):
        _, out = vc(self.root, "UC-E1")
        self.assertIn("existence only", out)

    def test_a_js_test_is_matched_by_its_criterion_id(self):
        root = make_uc()
        put(root, "a.test.ts", "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n")
        name = junit(root, [("a.test.ts", "x (Verifies AC-1)", "failed")])
        code, out = vc(root, "UC-E1", "--results", name)
        self.assertEqual(code, 1, out)


if __name__ == "__main__":
    unittest.main()
