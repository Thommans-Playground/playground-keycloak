"""Tests for next_tool.py. Run from this folder: python3 -m unittest test_next_tool"""

import io
import json
import re
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "vbench-vcycle" / "scripts"))
import test_vcycle as tv  # noqa: E402  (its fixtures: real use cases in temp repos)
import next_tool as nt  # noqa: E402

TESTED = "it('x (Verifies AC-1)', () => { expect(1).toBe(1); });\n"


def nx(root, *args):
    out = io.StringIO()
    with redirect_stdout(out):
        code = nt.main(["--root", str(root), "--tests-dir", "tests", *args])
    return code, out.getvalue()


def step(root, *extra):
    code, out = nx(root, "next", "UC-E1", "--json", *extra)
    return json.loads(out)


def rewrite_rows(root, level, status, detail):
    """Fake one trace row, to reach states that are hard to build (and statuses that do not exist yet)."""
    return {"level": level, "status": status, "detail": detail, "spec": "s", "proof": "p"}


class Mapping(unittest.TestCase):
    def test_no_criteria_goes_to_req_in_say_what(self):
        root = tv.make_uc(criteria=())
        s = step(root)
        self.assertEqual(s["moment"], "say_what")
        self.assertEqual(s["skill"], "/vbench-req")
        self.assertIn("no criteria", s["reason"])

    def test_a_criterion_with_no_test_goes_to_at_then_tdd_in_build(self):
        root = tv.make_uc()
        s = step(root)
        self.assertEqual(s["moment"], "build")
        self.assertEqual(s["skill"], "/vbench-at")
        self.assertIn("/vbench-tdd", s["then"])
        self.assertIn("AC-1", s["reason"])

    def test_analysis_not_frozen_or_missing_goes_to_uc_and_the_reviewers_in_say_the_shape(self):
        root = tv.make_uc()
        tv.put(root, "a.test.ts", TESTED)
        s = step(root)
        self.assertEqual(s["moment"], "say_shape")
        self.assertEqual(s["skill"], "/vbench-uc")
        self.assertIn("vbench-design-reviewer", s["then"])
        self.assertIn("vbench-spec-challenger", s["then"])
        self.assertIn("vbench-security-reviewer", s["then"])

    def test_a_rule_with_no_test_goes_to_tdd_in_build(self):
        rows = [rewrite_rows(None, "Requirements", "ok", ""),
                rewrite_rows(None, "Criteria", "ok", ""),
                rewrite_rows(None, "Rules", "FAIL", "no test: RULE-E1")]
        s = nt.decide("UC-E1", rows)
        self.assertEqual((s["moment"], s["skill"]), ("build", "/vbench-tdd"))

    def test_slices_fail_goes_to_uc_in_say_the_shape(self):
        rows = [rewrite_rows(None, "Slices", "FAIL", "slice names no criterion")]
        s = nt.decide("UC-E1", rows)
        self.assertEqual((s["moment"], s["skill"]), ("say_shape", "/vbench-uc"))

    def test_design_warn_goes_to_uc_in_say_the_shape(self):
        s = nt.decide("UC-E1", [rewrite_rows(None, "Design", "warn", "no Design section")])
        self.assertEqual((s["moment"], s["skill"]), ("say_shape", "/vbench-uc"))

    def test_security_not_probed_goes_to_security_test_with_the_use_case_id(self):
        s = nt.decide("UC-E1", [rewrite_rows(None, "Security", "warn", "not probed yet")])
        self.assertEqual(s["skill"], "/vbench-security-test")
        self.assertEqual(s["command"], "/vbench-security-test UC-E1")
        self.assertEqual(s["moment"], "build")

    def test_a_security_criterion_with_no_test_goes_to_tdd(self):
        s = nt.decide("UC-E1", [rewrite_rows(None, "Security", "FAIL", "no test: AC-1")])
        self.assertEqual(s["skill"], "/vbench-tdd")

    def test_stack_run_only_goes_to_test_stack(self):
        s = nt.decide("UC-E1", [rewrite_rows(None, "Criteria", "warn", "stack run: AC-1")])
        self.assertEqual(s["skill"], "/vbench-test-stack")

    def test_review_unstamped_or_stale_is_the_owners_and_never_run_for_them(self):
        for status, detail in (("warn", "not stamped: 1 link(s)"), ("FAIL", "stale: AC-1 changed")):
            s = nt.decide("UC-E1", [rewrite_rows(None, "Review", status, detail)])
            self.assertEqual(s["skill"], "the owner")
            self.assertIn("diff", s["command"].lower())
            self.assertIn("stamp", s["will_not"].lower())

    def test_a_fail_is_taken_before_an_earlier_warn(self):
        rows = [rewrite_rows(None, "Requirements", "warn", "x"), rewrite_rows(None, "Rules", "FAIL", "no test: R")]
        self.assertEqual(nt.decide("UC-E1", rows)["skill"], "/vbench-tdd")

    def test_the_first_fail_wins_left_to_right(self):
        rows = [rewrite_rows(None, "Criteria", "FAIL", "no test: AC-1"), rewrite_rows(None, "Rules", "FAIL", "no test: R")]
        self.assertEqual(nt.decide("UC-E1", rows)["skill"], "/vbench-at")

    def test_the_first_warn_wins_left_to_right_when_nothing_fails(self):
        rows = [rewrite_rows(None, "Analysis", "warn", "not frozen"), rewrite_rows(None, "Review", "warn", "not stamped")]
        self.assertEqual(nt.decide("UC-E1", rows)["skill"], "/vbench-uc")

    def test_every_step_says_what_it_will_not_do(self):
        s = step(tv.make_uc())
        self.assertTrue(s["will_not"])


class Open(unittest.TestCase):
    def test_all_rows_ok_says_nothing_is_open(self):
        rows = [rewrite_rows(None, lv, "ok", "") for lv in nt.LEVELS]
        s = nt.decide("UC-E1", rows)
        self.assertIsNone(s["skill"])
        self.assertEqual(s["warnings"], 0)
        self.assertIn("Nothing is open", nt.render(s))

    def test_unknown_statuses_and_levels_are_skipped(self):
        rows = [rewrite_rows(None, "Requirements", "legacy", "x"), rewrite_rows(None, "Mystery", "FAIL", "y"),
                rewrite_rows(None, "Criteria", "ok", "")]
        s = nt.decide("UC-E1", rows)
        self.assertIsNone(s["skill"])

    def test_an_unknown_status_does_not_hide_a_known_warning(self):
        rows = [rewrite_rows(None, "Requirements", "legacy", "x"), rewrite_rows(None, "Rules", "warn", "stack run only: R")]
        self.assertEqual(nt.decide("UC-E1", rows)["skill"], "/vbench-test-stack")

    def test_a_use_case_without_a_fail_is_not_called_done_and_counts_its_warnings(self):
        rows = [rewrite_rows(None, "Analysis", "warn", "not frozen"), rewrite_rows(None, "Security", "warn", "not probed"),
                rewrite_rows(None, "Review", "warn", "not stamped")]
        s = nt.decide("UC-E1", rows)
        self.assertEqual(s["warnings"], 3)
        text = nt.render(s)
        self.assertIn("3 warning", text)
        self.assertNotIn("Nothing is open", text)

    def test_a_real_use_case_with_all_levels_ok_but_security_still_has_a_warning(self):
        root = tv.make_uc()
        tv.put(root, "a.test.ts", TESTED)
        s = step(root)
        self.assertGreaterEqual(s["warnings"], 1)


class Output(unittest.TestCase):
    def test_the_text_has_the_four_things_a_person_needs(self):
        code, out = nx(tv.make_uc(), "next", "UC-E1")
        self.assertEqual(code, 0)
        self.assertIn("You are at: BUILD", out)
        self.assertIn("UC-E1", out)
        self.assertIn("Next: /vbench-at", out)
        self.assertIn("will NOT", out)
        self.assertIn("no test", out)

    def test_json_shape(self):
        s = step(tv.make_uc())
        for key in ("uc", "name", "moment", "skill", "command", "reason", "level", "then", "will_not", "warnings", "fails", "tier"):
            self.assertIn(key, s)
        self.assertEqual(s["uc"], "UC-E1")
        self.assertEqual(s["level"], "Criteria")

    def test_an_unknown_use_case_is_an_error(self):
        code, out = nx(tv.make_uc(), "next", "UC-Z9")
        self.assertEqual(code, 1)
        self.assertIn("UC-Z9", out)

    def test_tier_is_shown_when_the_header_has_it_and_changes_nothing(self):
        root = tv.make_uc()
        plain = step(root)
        p = tv.uc_file(root)
        p.write_text(re.sub(r"(\nstatus: draft)", r"\1\ntier: small", p.read_text(), count=1))
        s = step(root)
        self.assertEqual(s["tier"], "small")
        self.assertEqual((s["skill"], s["reason"]), (plain["skill"], plain["reason"]))
        self.assertIn("small", nx(root, "next", "UC-E1")[1])

    def test_with_no_id_it_picks_the_use_case_that_most_needs_attention(self):
        root = tv.make_uc()
        tv.put(root, "a.test.ts", TESTED)
        tv.run_uc(root, "create", stdin=json.dumps(dict(tv.tuc.NEW, area="P", criteria=[], satisfies=["FR-2"])))
        data = json.loads(nx(root, "next", "--json")[1])
        self.assertEqual(data["uc"], "UC-P1")

    def test_all_lists_every_use_case_worst_first(self):
        root = tv.make_uc()
        tv.put(root, "a.test.ts", TESTED)
        tv.run_uc(root, "create", stdin=json.dumps(dict(tv.tuc.NEW, area="P", criteria=[], satisfies=["FR-2"])))
        code, out = nx(root, "all")
        self.assertLess(out.index("UC-P1"), out.index("UC-E1"))
        data = json.loads(nx(root, "all", "--json")[1])
        self.assertEqual([x["uc"] for x in data["use_cases"]], ["UC-P1", "UC-E1"])
        self.assertIn("moment", data["use_cases"][0])

    def test_it_writes_nothing(self):
        root = tv.make_uc()
        before = sorted((p, p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file())
        nx(root, "next", "UC-E1")
        nx(root, "all")
        self.assertEqual(before, sorted((p, p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()))


class NewStates(unittest.TestCase):
    """The trace now tells a real test from a hollow one, and a passing one from a failing one."""

    def test_a_test_with_no_assertion_goes_to_tdd(self):
        root = tv.make_uc()
        tv.put(root, "a.test.ts", "it('x (Verifies AC-1)', () => {});\n")
        s = step(root)
        self.assertEqual((s["moment"], s["skill"]), ("build", "/vbench-tdd"))
        self.assertIn("assertion", s["reason"])

    def test_a_failing_test_goes_to_tdd(self):
        root = tv.make_uc()
        tv.put(root, "test_a.py", tv.PY, folder="tests/unit")
        tv.configure(root, results=tv.junit(root, [("tests.unit.test_a", "test_x", "failed")]))
        s = step(root)
        self.assertEqual((s["moment"], s["skill"]), ("build", "/vbench-tdd"))

    def test_a_stale_test_hash_goes_to_at(self):
        root = tv.make_uc()
        tv.put(root, "a.test.ts", "it('x (Verifies AC-1 [reviewed deadbee])', () => { expect(1).toBe(1); });\n")
        s = step(root)
        self.assertEqual(s["skill"], "/vbench-at")


if __name__ == "__main__":
    unittest.main()
