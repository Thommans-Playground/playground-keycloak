"""Tests for at_tool.py. Run from this folder: python3 -m unittest test_at_tool"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import at_tool as at  # noqa: E402

rq, uc = at.rq, at.uc


def req(i, statement, **kw):
    row = {c: "" for c in rq.REQ_COLS}
    row.update(id=i, kind="functional", group="product", name="n", statement=statement,
              verification="acceptance test", today="not built", status="draft", release="R1")
    row.update(kw)
    return row


def ac(i, rid, level="acceptance", **kw):
    row = {c: "" for c in rq.AC_COLS}
    row.update(id=i, requirements=rid, given="a pending account", when="an administrator approves it",
               then="the account is active", test_level=level, status="draft")
    row.update(kw)
    return row


def make_root():
    root = Path(tempfile.mkdtemp())
    (root / "vbench.json").write_text(json.dumps({'id_prefix': 'UC', 'system_name': 'Verify AI', 'providers': ['keycloak'], 'actors': ['administrator', 'auditor', 'project_manager', 'engineer', 'person', 'guest', 'system'], 'areas': {'A': 'BC-ACCESS', 'C': 'BC-CHECKLISTS', 'E': 'BC-ENDPOINTS', 'F': 'BC-FILES', 'G': 'BC-FRAMEWORKS', 'L': 'BC-AUDIT', 'P': 'BC-PROJECTS', 'V': 'BC-EVALUATIONS'}, 'diagram': {'actor_style': {'administrator': 'Admin', 'auditor': 'Auditor', 'project_manager': 'PM', 'engineer': 'Engineer', 'person': 'Person', 'guest': 'Guest', 'system': 'Sys'}, 'actor_colour': {'administrator': '#E65100', 'auditor': '#AD1457', 'project_manager': '#00838F', 'engineer': '#5D4037', 'person': '#1565C0', 'guest': '#6A1B9A', 'system': '#455A64'}, 'context_colour': {'BC-ACCESS': '#E8F0FE', 'BC-PROJECTS': '#FFFDE7', 'BC-FILES': '#ECEFF1', 'BC-ENDPOINTS': '#FFF3E0', 'BC-CHECKLISTS': '#E8F5E9', 'BC-EVALUATIONS': '#EDE7F6', 'BC-AUDIT': '#FBE9E7', 'BC-FRAMEWORKS': '#F3E5F5'}, 'actor_is_a': [['project_manager', 'engineer']]}}))
    (root / "docs/requirements").mkdir(parents=True)
    (root / "docs/domain/ontology").mkdir(parents=True)
    rq.write_rows(root / rq.PATHS["req"], rq.REQ_COLS,
                  [req("FR-1", "The system shall approve an account."), req("FR-2", "The system shall x.", release="R2")])
    rq.write_rows(root / rq.PATHS["ac"], rq.AC_COLS,
                  [ac("AC-1", "FR-1"), ac("AC-2", "FR-1", when="a person who is not an administrator tries it"),
                   ac("AC-3", "FR-1", level="unit"), ac("AC-4", "FR-2"), ac("AC-5", "FR-1", status="retired")])
    return root


def put(root, name, text, folder="tests/acceptance"):
    p = root / folder / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def run(root, *args):
    out = io.StringIO()
    with redirect_stdout(out):
        code = at.main(["--root", str(root), *args])
    return code, out.getvalue()


def hash_of(root, ac_id):
    return uc.ac_hash(at.criteria(root)[ac_id])


class Tests(unittest.TestCase):
    def test_every_acceptance_criterion_has_no_test_when_there_is_no_folder(self):
        root = make_root()
        code, out = run(root, "report")
        self.assertEqual(code, 0)
        self.assertIn("no such folder yet", out)
        self.assertIn("ACCEPTANCE CRITERIA WITH NO TEST (3)", out)   # AC-1, AC-2, AC-4: not unit AC-3, not retired AC-5
        self.assertIn("AC-4", out)
        self.assertNotIn("AC-3 (proves", out)
        self.assertNotIn("AC-5 (proves", out)

    def test_a_tagged_test_covers_its_criterion(self):
        root = make_root()
        put(root, "a.test.ts", f"// Verifies AC-1 [reviewed {hash_of(root, 'AC-1')}]\n")
        _, out = run(root, "report")
        self.assertIn("ACCEPTANCE CRITERIA WITH NO TEST (2)", out)
        self.assertNotIn("AC-1 (proves", out)

    def test_a_pytest_marker_covers_its_criterion(self):
        root = make_root()
        put(root, "test_a.py", '@pytest.mark.ac("AC-1")\ndef test_x():\n    pass\n')
        _, out = run(root, "report")
        self.assertIn("ACCEPTANCE CRITERIA WITH NO TEST (2)", out)
        self.assertNotIn("AC-1 (proves", out)

    def test_one_test_can_carry_several_markers(self):
        root = make_root()
        put(root, "test_a.py", '@pytest.mark.ac("AC-1")\n@pytest.mark.ac("AC-2")\ndef test_x():\n    pass\n')
        _, out = run(root, "report")
        self.assertIn("2 Verifies tag(s) found for 2 criterion(s)", out)

    def test_a_comment_can_list_several_criteria(self):
        root = make_root()
        put(root, "a.test.ts", "// Verifies AC-1, AC-2\n")
        _, out = run(root, "report")
        self.assertIn("2 Verifies tag(s) found for 2 criterion(s)", out)

    def test_a_marker_with_a_wrong_hash_is_stale(self):
        root = make_root()
        put(root, "test_a.py", '@pytest.mark.ac("AC-1", reviewed="abcdef0")\ndef test_x():\n    pass\n')
        code, out = run(root, "report")
        self.assertEqual(code, 1)
        self.assertIn("STALE TESTS", out)

    def test_a_marker_for_an_unknown_criterion_is_a_problem(self):
        root = make_root()
        put(root, "test_a.py", '@pytest.mark.ac("AC-99")\ndef test_x():\n    pass\n')
        code, _ = run(root, "report")
        self.assertEqual(code, 1)

    def test_stamp_sets_the_hash_on_a_marker(self):
        root = make_root()
        p = put(root, "test_a.py", '@pytest.mark.ac("AC-1")\ndef test_x():\n    pass\n')
        run(root, "stamp", "AC-1")
        self.assertIn(f'@pytest.mark.ac("AC-1", reviewed="{hash_of(root, "AC-1")}")', p.read_text())
        self.assertEqual(run(root, "report")[0], 0)

    def test_a_tag_for_an_unknown_criterion_is_a_problem(self):
        root = make_root()
        put(root, "a.test.ts", "// Verifies AC-99\n")
        code, out = run(root, "report")
        self.assertEqual(code, 1)
        self.assertIn("a.test.ts:1 says Verifies AC-99", out)

    def test_stale_when_the_hash_does_not_match(self):
        root = make_root()
        put(root, "a.test.ts", "// Verifies AC-1 [reviewed abcdef0]\n")
        code, out = run(root, "report")
        self.assertEqual(code, 1)
        self.assertIn("STALE TESTS", out)
        self.assertIn("recorded abcdef0", out)

    def test_up_to_date_when_the_hash_matches(self):
        root = make_root()
        put(root, "a.test.ts", f"// Verifies AC-1 [reviewed {hash_of(root, 'AC-1')}]\n")
        code, out = run(root, "report")
        self.assertEqual(code, 0)
        self.assertIn("STALE TESTS: THE CRITERION CHANGED SINCE THE TEST WAS REVIEWED (0)", out)

    def test_a_changed_criterion_makes_its_test_stale(self):
        root = make_root()
        put(root, "a.test.ts", f"// Verifies AC-1 [reviewed {hash_of(root, 'AC-1')}]\n")
        rows = rq.read_rows(root / rq.PATHS["ac"])
        rows[0]["then"] = "the account is active and an email is sent"
        rq.write_rows(root / rq.PATHS["ac"], rq.AC_COLS, rows)
        code, out = run(root, "report")
        self.assertEqual(code, 1)
        self.assertIn("AC-1: recorded", out)

    def test_a_note_edit_does_not_make_a_test_stale(self):
        root = make_root()
        put(root, "a.test.ts", f"// Verifies AC-1 [reviewed {hash_of(root, 'AC-1')}]\n")
        rows = rq.read_rows(root / rq.PATHS["ac"])
        rows[0]["notes"] = "a new note"
        rq.write_rows(root / rq.PATHS["ac"], rq.AC_COLS, rows)
        self.assertEqual(run(root, "report")[0], 0)

    def test_a_test_with_no_hash_is_listed_but_not_a_failure(self):
        root = make_root()
        put(root, "a.test.ts", "// Verifies AC-1\n")
        code, out = run(root, "report")
        self.assertEqual(code, 0)
        self.assertIn("TESTS WITH NO REVIEW HASH (1)", out)

    def test_a_test_for_a_non_acceptance_criterion_is_noted(self):
        root = make_root()
        put(root, "a.test.ts", "// Verifies AC-3\n")
        _, out = run(root, "report")
        self.assertIn("AC-3 is a unit criterion", out)

    def test_release_filter(self):
        root = make_root()
        _, out = run(root, "report", "--release", "R1")
        self.assertIn("2 acceptance criteria for release R1", out)
        self.assertNotIn("AC-4 (proves", out)

    def test_node_modules_is_skipped(self):
        root = make_root()
        put(root, "node_modules/x/a.test.ts", "// Verifies AC-1\n")
        _, out = run(root, "report")
        self.assertIn("0 Verifies tag(s)", out)

    def test_use_case_listing_a_criterion_with_no_test(self):
        import uc_tool
        root = make_root()
        data = {"area": "A", "name": "Approve an account", "actor": "administrator", "satisfies": ["FR-1"],
                "criteria": ["AC-1"], "parameters": [], "objects": [], "rules": [], "effects": ["x"]}
        import sys as _s
        old = _s.stdin
        _s.stdin = io.StringIO(json.dumps(data))
        try:
            with redirect_stdout(io.StringIO()):
                uc_tool.main(["--root", str(root), "create"])
        finally:
            _s.stdin = old
        _, out = run(root, "report")
        self.assertIn("UC-A1 lists AC-1: no test", out)
        put(root, "a.test.ts", f"// Verifies AC-1 [reviewed {hash_of(root, 'AC-1')}]\n")
        _, out = run(root, "report")
        self.assertNotIn("UC-A1 lists AC-1: no test", out)

    # ---- skeleton

    def test_skeleton_prints_a_failing_placeholder_with_the_criterion_as_comments(self):
        root = make_root()
        code, out = run(root, "skeleton", "AC-1", "--stack", "vitest")
        self.assertEqual(code, 0)
        self.assertIn(f"Verifies AC-1 [reviewed {hash_of(root, 'AC-1')}]", out)
        self.assertIn("Given a pending account", out)
        self.assertIn('throw new Error("AC-1 is not written yet")', out)
        self.assertNotIn("expect(", out)          # never an invented assertion
        self.assertFalse((root / "tests/acceptance").exists())   # printing writes nothing

    def test_skeleton_for_each_stack(self):
        root = make_root()
        self.assertIn('import { test } from "@playwright/test"', run(root, "skeleton", "AC-1", "--stack", "playwright")[1])
        out = run(root, "skeleton", "AC-1", "--stack", "pytest")[1]
        self.assertIn("pytest.fail(", out)
        self.assertIn("def test_ac_1_", out)

    def test_skeleton_write_creates_one_file_and_then_refuses_a_second(self):
        root = make_root()
        code, out = run(root, "skeleton", "AC-1", "--stack", "vitest", "--write")
        self.assertEqual(code, 0)
        files = list((root / "tests/acceptance").glob("ac-1-*.test.ts"))
        self.assertEqual(len(files), 1)
        code, out = run(root, "skeleton", "AC-1", "--stack", "vitest", "--write")
        self.assertEqual(code, 1)
        self.assertIn("already has a test", out)
        self.assertEqual(run(root, "report")[0], 0)   # the new test is tagged, so it is not stale

    def test_skeleton_refuses_a_unit_criterion_and_an_unknown_stack(self):
        root = make_root()
        code, out = run(root, "skeleton", "AC-3", "--stack", "vitest")
        self.assertEqual(code, 1)
        self.assertIn("unit criterion", out)
        code, out = run(root, "skeleton", "AC-1", "--stack", "cobol")
        self.assertEqual(code, 1)
        self.assertIn("stack must be one of", out)
        code, out = run(root, "skeleton", "AC-1")      # no stack given: the default is pytest
        self.assertEqual(code, 0)
        self.assertIn("pytest.fail(", out)
        self.assertIn("test_ac_1_", out)

    def test_skeleton_text_has_no_dashes_of_its_own(self):
        root = make_root()
        out = run(root, "skeleton", "AC-1", "--stack", "vitest")[1]
        self.assertNotIn("\u2013", out)
        self.assertNotIn("\u2014", out)

    # ---- stamp and show

    def test_stamp_sets_the_hash_and_keeps_crlf(self):
        root = make_root()
        p = root / "tests/acceptance/a.test.ts"
        p.parent.mkdir(parents=True)
        p.write_bytes(b"// Verifies AC-1 [reviewed abcdef0]\r\nit('x', () => {});\r\n")
        code, out = run(root, "stamp", "AC-1")
        self.assertEqual(code, 0)
        data = p.read_bytes()
        self.assertIn(f"Verifies AC-1 [reviewed {hash_of(root, 'AC-1')}]".encode(), data)
        self.assertIn(b"\r\n", data)
        self.assertNotIn(b"abcdef0", data)
        self.assertEqual(run(root, "report")[0], 0)

    def test_stamp_adds_a_hash_to_a_tag_without_one(self):
        root = make_root()
        p = put(root, "a.test.ts", "// Verifies AC-1\n")
        run(root, "stamp", "AC-1")
        self.assertIn("[reviewed ", p.read_text())

    def test_stamp_with_no_test_says_so(self):
        root = make_root()
        code, out = run(root, "stamp", "AC-1")
        self.assertEqual(code, 1)
        self.assertIn("no test carries this tag", out)

    def test_show(self):
        root = make_root()
        put(root, "a.test.ts", "// Verifies AC-1 [reviewed abcdef0]\n")
        _, out = run(root, "show", "AC-1")
        self.assertIn("proves FR-1: The system shall approve an account.", out)
        self.assertIn("STALE (recorded abcdef0)", out)
        self.assertEqual(run(root, "show", "AC-99")[0], 1)

    def test_the_tool_never_edits_the_csv_files(self):
        root = make_root()
        before = [(root / rq.PATHS[k]).read_bytes() for k in ("req", "ac")]
        put(root, "a.test.ts", "// Verifies AC-1\n")
        for args in (("report",), ("show", "AC-1"), ("stamp", "AC-1"), ("skeleton", "AC-2", "--stack", "vitest", "--write")):
            run(root, *args)
        self.assertEqual(before, [(root / rq.PATHS[k]).read_bytes() for k in ("req", "ac")])


if __name__ == "__main__":
    unittest.main()
