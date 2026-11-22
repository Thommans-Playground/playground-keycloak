"""The report card: one use case as a table of the V, the specification left and its verification right."""

from __future__ import annotations

from vbench.domain.model import UcRow
from vbench.domain.vcard import render_card


def row(**kw) -> UcRow:
    base = dict(
        uc="UC-N-001",
        acs=3,
        covered=3,
        enforced=3,
        code=True,
        tested=True,
        next="/vbench:v-4-verify UC-N-001",
        tasks=2,
        tasks_closed=2,
        wave=0,
        stage="verify",
    )
    return UcRow(**{**base, **kw})


def card(r: UcRow) -> list[str]:
    return render_card(r, paint=lambda tone, text: text)


def test_the_card_names_the_use_case_and_the_next_step():
    first = card(row())[0]
    assert "UC-N-001" in first
    assert "/vbench:v-4-verify UC-N-001" in first


def test_the_table_has_three_layers_then_the_code():
    lines = "\n".join(card(row()))
    for left in ("Requirements", "Design", "Tasks"):
        assert left in lines
    for right in ("Acceptance", "Integration", "Unit tests"):
        assert right in lines
    assert lines.index("Requirements") < lines.index("Design") < lines.index("Tasks") < lines.index("Code")
    assert lines.index("Acceptance") < lines.index("Integration") < lines.index("Unit tests")


def test_the_two_sides_are_columns_of_one_table_a_layer_to_a_row():
    lines = card(row())
    rows = [ln for ln in lines if ln.startswith("| ") and not ln.startswith("| ---")]
    assert rows[0] == "| Layer | Specification | Verification |"
    assert [ln.split("|")[1].strip() for ln in rows[1:]] == ["1", "2", "3", "Code"]
    assert "Requirements" in rows[1] and "Acceptance" in rows[1]  # a layer's specification beside its proof
    assert "Design" in rows[2] and "Integration" in rows[2]
    assert "Tasks" in rows[3] and "Unit tests" in rows[3]


def test_each_side_says_what_the_files_say_and_marks_it():
    marks: list[tuple[str, str]] = []

    def paint(tone: str, text: str) -> str:
        marks.append((tone, text))
        return text

    started = row(stage="code", code=False, tested=False, covered=0, tasks_closed=0)
    text = "\n".join(render_card(started, paint=paint))
    assert "0/3 covered" in text
    assert "0/2 closed" in text
    assert ("ok", "●") in marks  # requirements and design are done
    assert ("muted", "○") in marks  # nothing is built or proved yet
    assert not any(tone == "id" for tone, _ in marks[1:])  # labels stay plain; only the dot and the facts are styled


def test_a_level_the_script_does_not_track_says_so_instead_of_a_colour():
    text = "\n".join(card(row()))
    assert "not tracked" in text  # integration verification


def test_a_use_case_with_no_criteria_yet_is_marked_not_started():
    text = "\n".join(
        card(row(stage="requirements", acs=0, covered=0, enforced=0, tasks=0, tasks_closed=0, code=False, tested=False))
    )
    assert "not written" in text


def test_one_criterion_is_singular():
    assert "1 AC " in "\n".join(card(row(acs=1, covered=1, enforced=1))) + " "
    assert "1 ACs" not in "\n".join(card(row(acs=1, covered=1, enforced=1)))


def test_the_shape_of_the_dot_says_the_state_without_colour():
    text = "\n".join(card(row(stage="code", covered=1, tasks_closed=1, code=False, tested=False)))
    assert "● Requirements" in text  # finished
    assert "◐ Tasks" in text  # in progress
    assert "○ Unit tests" in text  # not started
