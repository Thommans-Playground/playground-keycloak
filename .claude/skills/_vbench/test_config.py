"""Tests for config.py. Run: python3 -m unittest discover -s .claude/skills/_vbench -p "test_*.py" """

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config  # noqa: E402

REPO = Path(__file__).resolve().parents[3]


def load(settings):
    root = Path(tempfile.mkdtemp())
    (root / "vbench.json").write_text(json.dumps(settings), encoding="utf-8")
    return config.load(root)


class Tests(unittest.TestCase):
    def test_with_no_file_the_defaults_hold(self):
        cfg = config.load(tempfile.mkdtemp())
        self.assertEqual(cfg["git"], {"remote": "origin", "repo": None, "base_branch": None,
                                      "pr": {"draft": False, "labels": [], "reviewers": []}})
        self.assertEqual(cfg["stacks"], {})

    def test_git_settings_are_read_and_merged_over_the_defaults(self):
        cfg = load({"git": {"repo": "acme/shop", "pr": {"draft": True}}})
        self.assertEqual(cfg["git"]["remote"], "origin")          # kept
        self.assertEqual(cfg["git"]["repo"], "acme/shop")         # set
        self.assertEqual(cfg["git"]["pr"], {"draft": True, "labels": [], "reviewers": []})

    def test_git_base_branch_is_used_when_the_top_level_one_is_not_set(self):
        self.assertEqual(load({"git": {"base_branch": "develop"}})["base_branch"], "develop")
        self.assertEqual(load({"base_branch": "trunk", "git": {"base_branch": "develop"}})["base_branch"], "trunk")

    def test_stacks_are_read(self):
        stacks = {"api": {"path": "apps/api", "language": "python", "tests": "uv run pytest"}}
        self.assertEqual(load({"stacks": stacks})["stacks"], stacks)

    def test_a_typo_inside_git_or_a_stack_is_caught(self):
        for bad in ({"git": {"remtoe": "origin"}},
                    {"git": {"pr": {"draught": True}}},
                    {"stacks": {"api": {"path": "x", "language": "python", "tset": "pytest"}}}):
            with self.assertRaises(SystemExit, msg=str(bad)):
                load(bad)

    def test_a_stack_needs_a_path_and_a_language(self):
        for bad in ({"stacks": {"api": {"language": "python"}}}, {"stacks": {"api": {"path": "apps/api"}}}):
            with self.assertRaises(SystemExit, msg=str(bad)):
                load(bad)

    def test_the_wrong_kind_of_value_is_caught(self):
        for bad in ({"git": {"pr": {"draft": "yes"}}}, {"git": {"pr": {"labels": "bug"}}}, {"stacks": []}):
            with self.assertRaises(SystemExit, msg=str(bad)):
                load(bad)

    def test_an_unknown_top_level_key_is_still_refused(self):
        with self.assertRaises(SystemExit):
            load({"nonsense": 1})

    def test_this_repos_own_vbench_json_is_valid(self):
        cfg = config.load(REPO)
        self.assertEqual(cfg["git"]["remote"], "origin")
        self.assertEqual(cfg["base_branch"], "main")
        self.assertEqual(sorted(cfg["stacks"]), ["api", "web"])
        self.assertEqual(cfg["areas"], {"A": "BC-ACCESS", "P": "BC-PROJECTS"})


if __name__ == "__main__":
    unittest.main()
