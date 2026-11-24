"""Tests for execlog_tool.py. Run from this folder: python3 -m unittest test_execlog_tool"""

import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import execlog_tool as x  # noqa: E402

SOURCE = "def clean(name):\n    return name.strip()\n"
SUMMARY = "# Summary\n\n#### P9.1: clean the name\n\nWhat and why.\n"
GOOD = """# Task P9.1: Clean the name

**Task ID:** TSK-P9.1 · **Use Case:** UC-P9 · **Criteria:** AC-1 · **Code matched at:** `abc1234`

What this does and why: [summary, task P9.1](summary.md#p91-clean-the-name).

Run from `apps/api/`: `uv run pytest tests/test_clean.py -q`

## Step 1: trim the name (AC-1)

**Test** (Unit): the name is trimmed.

```python
# tests/test_clean.py
def test_trim():
    assert clean(" a ") == "a"
```

**Code**:

```python
# src/clean.py
def clean(name):
    return name.strip()
```

**Logic.** Trim before anything else.
"""


def build(task=GOOD, summary=SUMMARY, source=SOURCE):
    root = Path(tempfile.mkdtemp())
    (root / "src").mkdir()
    (root / "src" / "clean.py").write_text(source, encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_clean.py").write_text('def test_trim():\n    assert clean(" a ") == "a"\n', encoding="utf-8")
    chapter = root / "docs" / "execution-logs" / "UC-P9-x" / "chapters" / "001-first"
    chapter.mkdir(parents=True)
    (chapter / "summary.md").write_text(summary, encoding="utf-8")
    (chapter / "TSK-P9.1-clean.md").write_text(task, encoding="utf-8")
    return root


class Tests(unittest.TestCase):
    def problems(self, **kw):
        return x.check(build(**kw))

    def test_a_task_that_follows_the_shape_has_no_problems(self):
        self.assertEqual(self.problems(), [])

    def test_a_task_with_no_step_is_refused(self):
        task = GOOD.split("## Step 1")[0]
        self.assertTrue(any("no step" in p for p in self.problems(task=task)))

    def test_a_step_with_no_test_is_refused(self):
        task = GOOD.replace("**Test** (Unit)", "**Note**")
        self.assertTrue(any("Test" in p for p in self.problems(task=task)))

    def test_a_test_level_must_be_one_of_the_known_ones(self):
        task = GOOD.replace("(Unit)", "(Vibes)")
        self.assertTrue(any("level" in p for p in self.problems(task=task)))

    def test_a_step_with_a_test_but_no_code_block_is_refused(self):
        task = GOOD.replace("```python\n# src/clean.py\ndef clean(name):\n    return name.strip()\n```\n", "")
        self.assertTrue(any("Code" in p for p in self.problems(task=task)))

    def test_a_step_with_no_logic_is_refused(self):
        task = GOOD.replace("**Logic.** Trim before anything else.\n", "")
        self.assertTrue(any("Logic" in p for p in self.problems(task=task)))

    def test_steps_are_numbered_from_one_without_gaps(self):
        task = GOOD.replace("## Step 1:", "## Step 2:")
        self.assertTrue(any("number" in p for p in self.problems(task=task)))

    def test_a_block_that_differs_from_its_file_is_refused(self):
        task = GOOD.replace("return name.strip()\n```", "return name.upper()\n```")
        self.assertTrue(any("src/clean.py" in p and "differs" in p for p in self.problems(task=task)))

    def test_a_block_marked_as_an_earlier_shape_is_not_compared(self):
        task = GOOD.replace("# src/clean.py\n", "# src/clean.py, stage 1 shape\n").replace("name.strip()", "name")
        self.assertEqual(self.problems(task=task), [])

    def test_a_link_to_a_summary_entry_that_does_not_exist_is_refused(self):
        self.assertTrue(any("summary" in p for p in self.problems(summary="# Summary\n")))

    def test_a_header_field_missing_is_refused(self):
        task = GOOD.replace("**Criteria:** AC-1 · ", "")
        self.assertTrue(any("Criteria" in p for p in self.problems(task=task)))

    def test_a_dash_is_refused(self):
        task = GOOD.replace("Trim before", "Trim — before")
        self.assertTrue(any("dash" in p for p in self.problems(task=task)))


if __name__ == "__main__":
    unittest.main()
