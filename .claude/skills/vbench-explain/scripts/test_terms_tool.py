"""Tests for terms_tool.py. Run from this folder: python3 -m unittest test_terms_tool"""

import datetime
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


def add_card(root, slug, term, aliases, prereq=None):
    extra = f"prereq: [{', '.join(prereq)}]\n" if prereq else ""
    text = CARD.replace("term: Nonce", f"term: {term}").replace("[nonce, replay]", f"[{aliases}]")
    text = text.replace("guide: 1.8 State\n", extra + "guide: 1.8 State\n")
    (root / t.CARDS / f"{slug}.md").write_text(text)


def at(day):
    """Make the tool believe today is `day` (a date string)."""
    t.today = lambda: datetime.date.fromisoformat(day)


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


class RankAndPrereq(unittest.TestCase):
    def setUp(self):
        self.root = make_repo()
        add_card(self.root, "alpha", "Alpha", "alpha")
        add_card(self.root, "beta", "Beta", "beta, beta thing")
        add_card(self.root, "gamma", "Gamma", "gamma")
        self.addCleanup(lambda: setattr(t, "today", datetime.date.today))

    def test_find_ranks_by_mentions_and_prints_two_by_default(self):
        _, out = run(self.root, "find", "beta beta beta, alpha, gamma gamma, nonce")
        lines = [ln for ln in out.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 2, out)
        self.assertIn("Beta", lines[0])

    def test_limit_and_all(self):
        text = "beta beta alpha gamma nonce"
        _, out = run(self.root, "find", text, "--limit", "1")
        self.assertEqual(len(out.strip().splitlines()), 1)
        _, out = run(self.root, "find", text, "--all")
        self.assertEqual(len(out.strip().splitlines()), 4)

    def test_a_more_specific_alias_counts_more(self):
        _, out = run(self.root, "find", "alpha and a beta thing", "--limit", "1")
        self.assertIn("Beta", out)

    def test_a_term_is_not_offered_before_its_prerequisite(self):
        add_card(self.root, "delta", "Delta", "delta", prereq=["alpha"])
        _, out = run(self.root, "find", "delta delta", "--unseen")
        self.assertIn("Alpha", out)
        self.assertNotIn("Delta", out)
        run(self.root, "seen", "alpha")
        _, out = run(self.root, "find", "delta delta", "--unseen")
        self.assertIn("Delta", out)

    def test_check_fails_on_a_prereq_that_is_not_a_card_and_on_a_cycle(self):
        add_card(self.root, "delta", "Delta", "delta", prereq=["nothing"])
        code, out = run(self.root, "check")
        self.assertEqual(code, 1)
        self.assertIn("nothing", out)
        add_card(self.root, "delta", "Delta", "delta", prereq=["epsilon"])
        add_card(self.root, "epsilon", "Epsilon", "epsilon", prereq=["delta"])
        code, out = run(self.root, "check")
        self.assertEqual(code, 1)
        self.assertIn("cycle", out)

    def test_due_after_three_days_then_after_fourteen_days_since_review(self):
        at("2026-11-01")
        run(self.root, "seen", "alpha")
        at("2026-11-03")
        _, out = run(self.root, "due")
        self.assertIn("nothing is due", out)
        at("2026-11-04")
        _, out = run(self.root, "due")
        self.assertIn("Alpha", out)
        run(self.root, "reviewed", "alpha")
        at("2026-11-17")
        _, out = run(self.root, "due")
        self.assertIn("nothing is due", out)
        at("2026-11-18")
        _, out = run(self.root, "due")
        self.assertIn("Alpha", out)

    def test_the_seen_file_stays_readable_and_old_lines_still_count(self):
        (self.root / t.SEEN).parent.mkdir(parents=True)
        (self.root / t.SEEN).write_text("beta 2026-10-01\n")
        at("2026-11-04")
        run(self.root, "reviewed", "alpha")  # not seen yet: refused
        _, out = run(self.root, "due")
        self.assertIn("Beta", out)
        run(self.root, "reviewed", "beta")
        text = (self.root / t.SEEN).read_text()
        self.assertIn("beta reviewed 2026-11-04", text)
        self.assertEqual(t.seen(self.root), {"beta"})

    def test_reviewed_refuses_a_term_not_yet_seen(self):
        code, _ = run(self.root, "reviewed", "alpha")
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
