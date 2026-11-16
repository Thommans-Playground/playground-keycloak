"""The requirements as one readable sheet, and an explanation beside every name."""

from __future__ import annotations

from pathlib import Path

from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.app.export import export_state
from vbench.domain.describe import diagram_title, first_line, humanise, module_summary
from vbench.domain.requirements_doc import read_criteria, read_requirements, tables
from vbench.domain.vview import build_v

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "notes-app"


class NoRepo:
    def branch(self) -> str:
        return ""

    def commits(self, base: str) -> list[str]:
        return []


def sheet() -> dict:
    return export_state(load_config(EXAMPLE), FsWorkspace(EXAMPLE), NoRepo())["requirements"]


def test_the_requirements_doc_reads_as_data():
    doc = read_requirements(load_config(EXAMPLE), FsWorkspace(EXAMPLE))
    assert [p.id for p in doc.problems] == ["STK-PRB-001", "STK-PRB-002", "STK-PRB-003"]
    first = doc.problems[0]
    assert (
        first.text.startswith("Small pieces of text")
        and first.who == "The author"
        and first.cost.startswith("They write")
    )
    assert [r.id for r in doc.requests] == ["STK-REQ-001", "STK-REQ-002"]
    assert doc.requests[0].raised_by == "STK-PER-001" and doc.requests[1].problems == ("STK-PRB-002",)
    fr = doc.functional[0]
    assert fr.id == "REQ-FR-001" and fr.story.startswith("As an author, I want") and fr.satisfies == ("STK-REQ-001",)
    nfr = doc.quality[1]
    assert (nfr.id, nfr.quality) == ("REQ-NFR-002", "Input limits")
    assert nfr.source == "The author" and "100 KB plus one byte" in nfr.measure and nfr.response


def test_template_placeholder_rows_are_not_requirements(tmp_path: Path):
    template = Path(__file__).resolve().parent.parent / "src/vbench/templates/docs/00-requirements-engineering.md"
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/00-requirements-engineering.md").write_text(template.read_text())
    (tmp_path / ".vbench").mkdir()
    (tmp_path / ".vbench/config.toml").write_text("[vbench]\n")
    doc = read_requirements(load_config(tmp_path), FsWorkspace(tmp_path))
    assert (doc.problems, doc.requests, doc.functional, doc.quality) == ((), (), (), ())


def test_a_table_is_read_by_its_header_names_so_an_older_doc_still_reads():
    old = (
        "| ID | Quality | Fit criterion | How to verify |\n|--|--|--|--|\n"
        "| **REQ-NFR-001** | Speed | under 1 s | time it |\n"
    )
    ((header, rows),) = tables(old)
    assert header[2] == "fit criterion" and rows[0][0] == "**REQ-NFR-001**"


def test_criteria_carry_their_given_when_then_text_and_what_they_satisfy():
    got = read_criteria(load_config(EXAMPLE), FsWorkspace(EXAMPLE))
    ac = got["AC-N-001"]
    assert ac.text.startswith("Given a title and a body") and ac.satisfies == ("REQ-FR-001",)


def test_each_requirement_comes_with_its_use_cases_criteria_and_tests():
    s = sheet()
    fr1 = next(f for f in s["functional"] if f["id"] == "REQ-FR-001")
    assert fr1["ucs"] == [{"id": "UC-N-001", "title": "Create note"}] and fr1["story"]
    assert [c["id"] for c in fr1["criteria"]] == ["AC-N-001", "AC-N-002"]
    covered = fr1["criteria"][0]
    assert covered["state"] == "covered" and covered["tests"][0]["ref"] == "TST-ACC-001"
    nfr2 = next(q for q in s["quality"] if q["id"] == "REQ-NFR-002")
    assert nfr2["criteria"][0]["id"] == "AC-N-003" and nfr2["measure"]
    assert s["requests"][0]["requirements"] == ["REQ-FR-001", "REQ-FR-002", "REQ-FR-003", "REQ-NFR-001", "REQ-NFR-002"]
    assert nfr2["satisfies"] == ["STK-REQ-001"]
    assert s["requests"][1]["requirements"] == []  # asked for, nothing derived from it yet


def test_several_problems_show_which_are_addressed_and_which_are_not():
    problems = {p["id"]: p for p in sheet()["problems"]}
    assert list(problems) == ["STK-PRB-001", "STK-PRB-002", "STK-PRB-003"]
    assert problems["STK-PRB-001"]["requests"] == ["STK-REQ-001"] and problems["STK-PRB-001"]["status"] == "ok"
    assert problems["STK-PRB-003"]["requests"] == [] and problems["STK-PRB-003"]["status"] == "warn"
    assert problems["STK-PRB-003"]["label"] == "No request yet" and problems["STK-PRB-003"]["cost"]


def test_a_problem_written_as_a_paragraph_in_an_older_doc_still_reads(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / ".vbench").mkdir()
    (tmp_path / ".vbench/config.toml").write_text("[vbench]\n")
    (tmp_path / "docs/00-requirements-engineering.md").write_text(
        "## 0. Problem definition\n\n> guidance\n\nNotes get lost.\n\n## 1. Stakeholders\n"
    )
    doc = read_requirements(load_config(tmp_path), FsWorkspace(tmp_path))
    assert [(p.id, p.text) for p in doc.problems] == [("", "Notes get lost.")]


def test_every_item_has_an_explanation_and_the_exports_carry_it():
    items, unplaced = build_v(load_config(EXAMPLE), FsWorkspace(EXAMPLE))
    assert all(i.description for i in [*items, *unplaced]), [i.id for i in items if not i.description]
    state = export_state(load_config(EXAMPLE), FsWorkspace(EXAMPLE), NoRepo())
    code = next(i for i in state["v"]["items"] if i["kind"] == "code" and i["title"] == "note.py")
    assert code["description"] == "The Note aggregate"
    test = next(i for i in state["v"]["items"] if i["kind"] == "test" and "has_an_id" in i["id"])
    assert test["description"] == "A saved note has an id and both timestamps"
    assert all(c["text"] for c in state["criteria"] if c["spec"].endswith(".md") and "_TEMPLATE" not in c["spec"])


def test_the_helpers_turn_names_into_words():
    assert humanise("test_a_saved_note_has_an_id") == "A saved note has an id"
    assert humanise("TestNotes.test_it_works") == "It works"
    assert humanise("src/notes/create.py") == "Create"
    assert first_line("Verifies UC-N-001 · unit rung.\n\nA real explanation.\n") == "A real explanation"
    assert module_summary("a.py", '"""Realises UC-N-001\n\nThe thing it does."""\n') == "The thing it does"
    assert (
        diagram_title("@startuml\ntitle UC-N-001 - Create note (Sequence)\n@enduml")
        == "UC-N-001 - Create note (Sequence)"
    )
