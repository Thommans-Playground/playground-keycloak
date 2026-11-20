"""Tests for req_tool.py. Run: python3 -m unittest .claude/skills/vbench-req/scripts/test_req_tool.py"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import req_tool as t  # noqa: E402


def make_root(reqs, acs):
    root = Path(tempfile.mkdtemp())
    (root / "docs/requirements").mkdir(parents=True)
    (root / "docs/domain/ontology").mkdir(parents=True)
    (root / t.PATHS["req"]).write_bytes(b"x\r\n")  # the real files use CRLF, and the script keeps it
    t.write_rows(root / t.PATHS["req"], t.REQ_COLS, reqs)
    t.write_rows(root / t.PATHS["ac"], t.AC_COLS, acs)
    return root


def req(i, statement, **kw):
    row = {c: "" for c in t.REQ_COLS}
    row.update(id=i, kind="functional", group="product", name="n", statement=statement,
              verification="acceptance test", today="not built", status="draft")
    row.update(kw)
    return row


def ac(i, rq, **kw):
    row = {c: "" for c in t.AC_COLS}
    row.update(id=i, requirements=rq, given="g", when="w", then="t", test_level="acceptance",
               status="draft")
    row.update(kw)
    return row


def run(root, *args, stdin=""):
    out = io.StringIO()
    old = sys.stdin
    sys.stdin = io.StringIO(stdin)
    try:
        with redirect_stdout(out):
            code = t.main(["--root", str(root), *args])
    finally:
        sys.stdin = old
    return code, out.getvalue()


class Tests(unittest.TestCase):
    def test_next_ids(self):
        root = make_root([req("FR-4", "The system shall a."), req("NFR-2", "The system shall b.", kind="constraint")],
                         [ac("AC-9", "FR-4")])
        _, out = run(root, "next-ids")
        self.assertIn("FR-5", out)
        self.assertIn("NFR-3", out)
        self.assertIn("AC-10", out)

    def test_search_finds_reworded_requirement(self):
        root = make_root([req("FR-1", "The system shall let an administrator approve a pending account."),
                          req("FR-2", "The system shall export a checklist to Excel.")], [ac("AC-1", "FR-1")])
        _, out = run(root, "search", "an administrator can approve an account")
        self.assertIn("FR-1", out.split("EXISTING REQUIREMENTS")[1].split("FR-2")[0])
        self.assertIn("AC-1", out)

    def test_search_new_thing_is_new(self):
        root = make_root([req("FR-1", "The system shall export a checklist to Excel.")], [])
        _, out = run(root, "search", "send an email reminder every morning")
        self.assertIn("looks new", out)

    def test_validate_catches_bad_rows(self):
        root = make_root([req("FR-1", "Let admins approve."), req("FR-1", "The system shall x.")],
                         [ac("AC-1", "FR-99")])
        code, out = run(root, "validate")
        self.assertEqual(code, 1)
        self.assertIn("duplicate id", out)
        self.assertIn("does not start with", out)
        self.assertIn("FR-99, which does not exist", out)

    def test_quality_needs_scenario(self):
        root = make_root([req("NFR-1", "The system shall be quick.", kind="quality")], [])
        code, out = run(root, "validate")
        self.assertEqual(code, 1)
        self.assertIn("missing", out)

    def test_append_assigns_ids_and_keeps_crlf(self):
        root = make_root([req("FR-1", "The system shall a.")], [ac("AC-1", "FR-1")])
        item = {"kind": "functional", "name": "b", "statement": "The system shall b.",
                "verification": "acceptance test", "release": "R1"}
        code, out = run(root, "append", "requirements", stdin=json.dumps(item))
        self.assertEqual(code, 0)
        self.assertIn("FR-2", out)
        data = (root / t.PATHS["req"]).read_bytes()
        self.assertIn(b"\r\n", data)
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))
        code, out = run(root, "append", "acceptance",
                        stdin=json.dumps({"requirements": ["FR-2"], "given": "a", "when": "b", "then": "c",
                                          "test_level": "unit"}))
        self.assertEqual(code, 0)
        self.assertIn("AC-2", out)

    def test_append_refuses_unknown_requirement(self):
        root = make_root([req("FR-1", "The system shall a.")], [])
        code, out = run(root, "append", "acceptance",
                        stdin=json.dumps({"requirements": "FR-7", "given": "a", "when": "b", "then": "c",
                                          "test_level": "unit"}))
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", out)

    def test_dry_run_writes_nothing(self):
        root = make_root([req("FR-1", "The system shall a.")], [])
        before = (root / t.PATHS["req"]).read_bytes()
        run(root, "append", "requirements", "--dry-run",
            stdin=json.dumps({"kind": "functional", "statement": "The system shall b.",
                              "verification": "unit test"}))
        self.assertEqual(before, (root / t.PATHS["req"]).read_bytes())

    def test_update_changes_a_field_but_not_the_id(self):
        root = make_root([req("FR-1", "The system shall a.")], [])
        code, _ = run(root, "update", "FR-1", stdin=json.dumps({"release": "R2"}))
        self.assertEqual(code, 0)
        self.assertEqual(t.read_rows(root / t.PATHS["req"])[0]["release"], "R2")
        with self.assertRaises(SystemExit):
            run(root, "update", "FR-1", stdin=json.dumps({"id": "FR-2"}))

    def test_retired_words_flagged(self):
        vocab = [{"term": "assign", "kind": "retired word", "use_instead": "(dropped)", "meaning": "ADR 21"}]
        strict, watch = t.retired_words("let a manager assign items", vocab)
        self.assertEqual(len(strict), 1)
        self.assertEqual(watch, [])


class MarkdownFormatTests(unittest.TestCase):
    """The requirements and criteria are markdown tables, read back as the same flat rows."""

    def roundtrip(self, reqs, acs):
        root = make_root(reqs, acs)
        return root, t.read_rows(root / t.PATHS["req"]), t.read_rows(root / t.PATHS["ac"])

    def test_rows_survive_a_write_and_read(self):
        reqs = [req("FR-1", "The system shall a.", area="A", release="R1", today="built", objects="OBJ-A1",
                    sources="ADR 1; ADR 2", notes="One note."),
                req("FR-2", "The system shall b.", area="A"),
                req("FR-3", "The system shall c.", area="P")]
        _, back, _ = self.roundtrip(reqs, [])
        self.assertEqual(sorted(back, key=lambda r: r["id"]), sorted(reqs, key=lambda r: r["id"]))

    def test_a_quality_row_goes_to_its_own_table_with_its_scenario(self):
        q = req("NFR-1", "The system shall check access.", kind="quality", quality="Security",
                stimulus="s", environment="e", response="r", measure="m", verification="inspection")
        root, back, _ = self.roundtrip([req("FR-1", "The system shall a.", area="A"), q], [])
        self.assertIn(q, back)
        text = (root / t.PATHS["req"]).read_text(encoding="utf-8")
        self.assertIn("## Quality, constraint and process requirements", text)
        self.assertLess(text.index("FR-1"), text.index("NFR-1"))

    def test_process_rows_keep_their_group(self):
        p = req("NFR-2", "The team shall test a restore.", kind="process", group="process")
        _, back, _ = self.roundtrip([p], [])
        self.assertEqual(back[0]["group"], "process")

    def test_pipes_and_line_breaks_in_a_cell_survive(self):
        r = req("FR-1", "The system shall treat a | b as two.", notes="Line one.\nLine two with | a pipe.")
        _, back, _ = self.roundtrip([r], [ac("AC-1", "FR-1", given="x | y", then="a\nb")])
        self.assertEqual(back[0]["statement"], r["statement"])
        self.assertEqual(back[0]["notes"], r["notes"])

    def test_criteria_roundtrip_and_empty_notes_column_is_left_out(self):
        acs = [ac("AC-1", "FR-1"), ac("AC-2", "FR-1; FR-2", test_level="unit")]
        root, _, back = self.roundtrip([req("FR-1", "The system shall a.")], acs)
        self.assertEqual(back, acs)
        self.assertNotIn("Notes", (root / t.PATHS["ac"]).read_text(encoding="utf-8"))

    def test_empty_files_are_readable(self):
        root, reqs, acs = self.roundtrip([], [])
        self.assertEqual((reqs, acs), ([], []))
        self.assertIn("_None yet._", (root / t.PATHS["ac"]).read_text(encoding="utf-8"))

    def test_the_file_is_a_markdown_table_a_person_can_read(self):
        root, _, _ = self.roundtrip([req("FR-1", "The system shall a.", area="A")], [])
        text = (root / t.PATHS["req"]).read_text(encoding="utf-8")
        self.assertIn("### Area A", text)
        self.assertIn("| ID | Name | Statement |", text)
        self.assertNotIn("stimulus", text.lower())

    def test_a_hand_edited_cell_is_read(self):
        root, _, _ = self.roundtrip([req("FR-1", "The system shall a.", area="A")], [])
        path = root / t.PATHS["req"]
        path.write_text(path.read_text(encoding="utf-8").replace("The system shall a.", "The system shall z."),
                        encoding="utf-8")
        self.assertEqual(t.read_rows(path)[0]["statement"], "The system shall z.")

    def test_append_keeps_the_area_and_adds_the_row(self):
        root = make_root([req("FR-1", "The system shall a.", area="A")], [])
        code, _ = run(root, "append", "requirements",
                      stdin=json.dumps({"kind": "functional", "area": "P", "name": "n",
                                        "statement": "The system shall b.", "verification": "unit test"}))
        self.assertEqual(code, 0)
        rows = {r["id"]: r for r in t.read_rows(root / t.PATHS["req"])}
        self.assertEqual(rows["FR-2"]["area"], "P")
        self.assertEqual(rows["FR-1"]["area"], "A")

    def test_convert_turns_the_csv_files_into_markdown(self):
        root = Path(tempfile.mkdtemp())
        (root / "docs/requirements").mkdir(parents=True)
        t.write_rows(root / "docs/requirements/requirements.csv", t.REQ_COLS, [req("FR-1", "The system shall a.")])
        t.write_rows(root / "docs/requirements/acceptance-criteria.csv", t.AC_COLS, [ac("AC-1", "FR-1")])
        code, out = run(root, "convert")
        self.assertEqual(code, 0)
        self.assertEqual(t.read_rows(root / t.PATHS["req"])[0]["id"], "FR-1")
        self.assertEqual(t.read_rows(root / t.PATHS["ac"])[0]["id"], "AC-1")
        self.assertTrue((root / "docs/requirements/requirements.csv").exists())
        code, out = run(root, "convert")
        self.assertIn("already exists", out)

    def write_uc(self, root, name, body):
        d = root / t.PATHS["usecases"]
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(body, encoding="utf-8")

    def uc_text(self, i, name, criteria, desc):
        ids = "".join("  - id: %s\n" % c for c in criteria)
        return ("```yaml\nid: %s\ntype: use-case\nname: %s\nsatisfies:\n  - id: FR-1\ncriteria:\n%s```\n\n"
                "## Description\n\n%s\n\n## Flow\n\nmore\n" % (i, name, ids, desc))

    def test_duplicates_requirements_skips_retired_and_reports_nothing_else(self):
        root = make_root([req("FR-1", "The system shall let an administrator approve a pending account.", name="Approve account"),
                          req("FR-2", "The system shall let an administrator approve a pending account.", name="Approve an account"),
                          req("FR-3", "The system shall let an administrator approve a pending account.", name="Approve account",
                              status="retired"),
                          req("FR-4", "The system shall export a checklist to Excel.", name="Export")], [])
        code, out = run(root, "duplicates", "--kind", "requirements")
        self.assertEqual(code, 0)
        self.assertIn("FR-1  FR-2", out)
        self.assertNotIn("FR-3", out)
        self.assertNotIn("FR-4", out)
        self.assertIn("prompt for a person", out)
        self.assertNotIn("ACCEPTANCE", out)

    def test_duplicates_threshold_override(self):
        root = make_root([req("FR-1", "The system shall approve an account.", name="Approve"),
                          req("FR-2", "The system shall approve a user.", name="Approve")], [])
        _, out = run(root, "duplicates", "--kind", "requirements", "--threshold", "0.99")
        self.assertNotIn("FR-1  FR-2", out)
        _, out = run(root, "duplicates", "--kind", "requirements", "--threshold", "0.3")
        self.assertIn("FR-1  FR-2", out)

    def test_duplicates_acceptance_and_same_behaviour_different_requirement(self):
        root = make_root([req("FR-1", "The system shall a."), req("FR-2", "The system shall b.")],
                         [ac("AC-1", "FR-1", given="a pending account", when="the administrator approves it",
                             then="the account becomes active"),
                          ac("AC-2", "FR-1", given="a pending account", when="the administrator approves it",
                             then="the account becomes active"),
                          ac("AC-3", "FR-2", given="a user", when="something else happens",
                             then="the account becomes active"),
                          ac("AC-4", "FR-1", given="a pending account", when="the administrator approves it",
                             then="the account becomes active", status="retired")])
        _, out = run(root, "duplicates", "--kind", "acceptance")
        self.assertIn("AC-1  AC-2", out)
        self.assertNotIn("AC-4", out)
        self.assertIn("same behaviour, different requirement", out)
        self.assertIn("AC-1  AC-3", out.split("same behaviour, different requirement")[1])

    def test_duplicates_usecases(self):
        root = make_root([req("FR-1", "The system shall a.")], [])
        self.write_uc(root, "UC-X1-a.md", self.uc_text("UC-X1", "Approve an account", ["AC-1", "AC-2", "AC-3"],
                                                       "An administrator approves a pending account."))
        self.write_uc(root, "UC-X2-b.md", self.uc_text("UC-X2", "Approve a pending account", ["AC-2", "AC-3", "AC-9"],
                                                       "An administrator approves a pending account."))
        self.write_uc(root, "UC-X3-c.md", self.uc_text("UC-X3", "Export a report", ["AC-20"], "Export to Excel."))
        self.write_uc(root, "UC-README.md", "no yaml block here\n")
        code, out = run(root, "duplicates", "--kind", "usecases")
        self.assertEqual(code, 0)
        self.assertIn("UC-X1  UC-X2", out)
        self.assertNotIn("UC-X3", out)
        self.assertIn("AC-2", out.split("listed by more than one")[1])
        self.assertIn("UC-X1, UC-X2", out)
        self.assertNotIn("AC-20", out.split("listed by more than one")[1])


if __name__ == "__main__":
    unittest.main()
