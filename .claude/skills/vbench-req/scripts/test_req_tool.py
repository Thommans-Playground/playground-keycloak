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


if __name__ == "__main__":
    unittest.main()
