"""Tests for terms_tool.py. Run from this folder: python3 -m unittest test_terms_tool"""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import terms_tool as t  # noqa: E402

REPO = HERE.parents[3]

CARD = """---
term: Nonce
say: A random value that ties an id token to one sign in.
aliases: [nonce, replay]
code:
  - src/auth.py :: make_nonce
guide: 1.8 State
check: What does a nonce stop?
---

## In one line

x

## Why we need it

x

## In our code

x

## Look for yourself

x
"""


def make_repo(card=CARD, source="def make_nonce():\n    pass\n"):
    root = Path(tempfile.mkdtemp())
    (root / "vbench.json").write_text("{}")
    (root / t.CARDS).mkdir(parents=True)
    (root / t.CARDS / "nonce.md").write_text(card)
    (root / "src").mkdir()
    (root / "src/auth.py").write_text(source)
    (root / "docs").mkdir(exist_ok=True)
    (root / t.GUIDE).write_text("### 1.8 State and nonce\n")
    return root


def run(root, *args):
    out = io.StringIO()
    with redirect_stdout(out):
        code = t.main(["--root", str(root), *args])
    return code, out.getvalue()


class Tests(unittest.TestCase):
    def test_a_good_card_passes_the_check(self):
        code, out = run(make_repo(), "check")
        self.assertEqual(code, 0, out)

    def test_a_code_pointer_to_a_symbol_that_is_gone_fails(self):
        code, out = run(make_repo(source="def other():\n    pass\n"), "check")
        self.assertEqual(code, 1)
        self.assertIn("make_nonce", out)

    def test_a_code_pointer_to_a_missing_file_fails(self):
        root = make_repo()
        (root / "src/auth.py").unlink()
        code, out = run(root, "check")
        self.assertEqual(code, 1)
        self.assertIn("src/auth.py", out)

    def test_a_card_with_no_check_question_or_section_fails(self):
        code, out = run(make_repo(card=CARD.replace("check: What does a nonce stop?\n", "").replace("## Look for yourself", "## Other")), "check")
        self.assertEqual(code, 1)
        self.assertIn("missing check", out)
        self.assertIn("Look for yourself", out)

    def test_a_study_guide_heading_that_is_gone_fails(self):
        root = make_repo()
        (root / t.GUIDE).write_text("### 9.9 Something else\n")
        code, out = run(root, "check")
        self.assertEqual(code, 1)
        self.assertIn("1.8 State", out)

    def test_find_names_the_terms_a_text_uses_and_seen_removes_them(self):
        root = make_repo()
        _, out = run(root, "find", "The nonce is checked", "--unseen")
        self.assertIn("Nonce", out)
        run(root, "seen", "nonce")
        _, out = run(root, "find", "The nonce is checked", "--unseen")
        self.assertIn("no terms", out)
        self.assertIn("nonce", (root / t.SEEN).read_text())

    def test_an_alias_inside_another_word_is_not_a_hit(self):
        _, out = run(make_repo(), "find", "a noncentral replayable thing", "--unseen")
        self.assertIn("no terms", out)

    def test_every_real_card_is_well_formed_and_points_at_real_code(self):
        """The cards of this repo cannot rot: a changed symbol or a missing file fails here."""
        code, out = run(REPO, "check")
        self.assertEqual(code, 0, out)
        self.assertGreaterEqual(len(t.cards(REPO)), 13)


if __name__ == "__main__":
    unittest.main()
