"""Editing one row of a markdown table without disturbing what is around it."""

from __future__ import annotations

import pytest

from vbench.domain.mdtable import TableError, cell_text, delete_row, locate, row_values, split_cells, upsert_row

DOC = """# Title

Some prose that must survive.

| ID | Problem | Who is affected |
|----|---------|-----------------|
| **STK-PRB-001** | First | The author |
| **STK-PRB-002** | Second | Everyone |

More prose.

| Other | Table |
|-------|-------|
| a | b |
"""
PROBLEMS = lambda h: "problem" in h  # noqa: E731


def test_cells_split_on_unescaped_pipes_only():
    assert split_cells("| **A-1** | one \\| two | three |") == ["**A-1**", "one | two", "three"]
    assert split_cells("|a|b|") == ["a", "b"]


def test_a_value_can_never_break_the_table():
    assert cell_text("a | b\nc   d") == "a \\| b c d"


def test_a_row_is_read_by_id_and_a_column_by_its_header():
    assert row_values(DOC, PROBLEMS, "STK-PRB-002") == {
        "id": "**STK-PRB-002**",
        "problem": "Second",
        "who is affected": "Everyone",
    }
    assert row_values(DOC, PROBLEMS, "STK-PRB-009") is None
    with pytest.raises(TableError):
        locate(DOC, lambda h: "nothing" in h)


def test_updating_a_row_changes_only_the_named_cells():
    out = upsert_row(DOC, PROBLEMS, "STK-PRB-001", {"who": "The reader"})
    assert "| **STK-PRB-001** | First | The reader |" in out
    assert out.replace("The reader", "The author") == DOC  # nothing else moved


def test_a_new_row_goes_after_the_last_one_and_the_rest_is_untouched():
    out = upsert_row(DOC, PROBLEMS, "STK-PRB-003", {"problem": "Third | with a pipe", "who": "Me"})
    lines = out.split("\n")
    at = lines.index("| **STK-PRB-003** | Third \\| with a pipe | Me |")
    assert lines[at - 1].startswith("| **STK-PRB-002**") and lines[at + 1] == ""
    assert "Some prose that must survive." in out and "| a | b |" in out


def test_the_templates_placeholder_row_is_replaced_by_the_first_real_one():
    template = "| ID | Problem | Who is affected |\n|--|--|--|\n| **STK-PRB-nnn** | (what goes wrong) | (who) |\n"
    out = upsert_row(template, PROBLEMS, "STK-PRB-001", {"problem": "Real", "who": "Someone"})
    assert out == "| ID | Problem | Who is affected |\n|--|--|--|\n| **STK-PRB-001** | Real | Someone |\n"


def test_a_row_is_deleted_by_id_and_a_missing_one_is_an_error():
    out = delete_row(DOC, PROBLEMS, "STK-PRB-001")
    assert "First" not in out and "Second" in out
    with pytest.raises(TableError):
        delete_row(DOC, PROBLEMS, "STK-PRB-009")


def test_naming_a_column_the_table_lacks_is_an_error_not_a_silent_skip():
    with pytest.raises(TableError, match="no `maturity` column"):
        upsert_row(DOC, PROBLEMS, "STK-PRB-001", {"maturity": "x"})
