"""The logical view of the V-cycle: every item placed on one of nine phases, each naming its use cases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.test_vbench import ctx, uc_spec, write
from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.app.export import export_state
from vbench.domain.vview import PHASES, build_v, collect_test_cases

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "notes-app"


class NoRepo:
    def branch(self) -> str:
        return ""

    def commits(self, base: str) -> list[str]:
        return []


def example_items():
    cfg, ws = load_config(EXAMPLE), FsWorkspace(EXAMPLE)
    items, unplaced = build_v(cfg, ws)
    by: dict[str, list] = {k: [] for k, *_ in PHASES}
    for i in items:
        by[i.phase].append(i)
    return by, unplaced


def test_the_nine_phases_pair_each_specification_with_the_test_that_proves_it():
    keys = {k: (arm, pair) for k, _, arm, pair in PHASES}
    assert [k for k, *_ in PHASES] == [
        "requirements",
        "system-design",
        "architecture",
        "module-design",
        "code",
        "unit",
        "integration",
        "system",
        "acceptance",
    ]
    for left, right in (
        ("requirements", "acceptance"),
        ("system-design", "system"),
        ("architecture", "integration"),
        ("module-design", "unit"),
    ):
        assert keys[left] == ("left", right) and keys[right] == ("right", left)
    assert keys["code"] == ("vertex", None)


def test_the_example_places_every_kind_of_item_on_its_phase():
    by, unplaced = example_items()
    assert {i.id: i.ucs for i in by["requirements"]}["REQ-FR-001"] == ("UC-N-001",)
    assert {i.id for i in by["requirements"]} == {
        "STK-PRB-001",
        "STK-PRB-002",
        "STK-PRB-003",
        "STK-REQ-001",
        "STK-REQ-002",
        "REQ-FR-001",
        "REQ-FR-002",
        "REQ-FR-003",
        "REQ-NFR-001",
        "REQ-NFR-002",
    }
    assert [(i.title, i.ucs) for i in by["system-design"]] == [("Notes", ("UC-N-001", "UC-N-002", "UC-N-003"))]
    assert {i.kind for i in by["architecture"]} == {"domain model"} and by["architecture"][0].file.endswith(
        "10-notes-ddd.puml"
    )
    assert {i.kind for i in by["module-design"]} == {"task", "sequence diagram", "state diagram"}
    assert sorted(i.id for i in by["module-design"] if i.kind == "task") == [
        "TSK-N-001",
        "TSK-N-002",
        "TSK-N-003",
    ]
    assert sorted(i.title for i in by["code"]) == ["create.py", "note.py"]
    assert len(by["unit"]) == 2 and len(by["acceptance"]) == 1 and by["integration"] == [] and by["system"] == []
    assert unplaced == []


def test_the_view_surfaces_a_requirement_no_use_case_realises():
    by, _ = example_items()
    nfr1 = next(i for i in by["requirements"] if i.id == "REQ-NFR-001")
    assert nfr1.ucs == () and nfr1.status == "warn" and nfr1.label == "No use case yet"
    assert next(i for i in by["requirements"] if i.id == "REQ-NFR-002").status == "ok"


def test_tests_are_indexed_per_function_with_their_use_case_rung_and_criteria():
    by, _ = example_items()
    unit = {i.title: i for i in by["unit"]}
    empty = next(v for k, v in unit.items() if "empty_or_blank" in k)
    assert (
        empty.ucs == ("UC-N-001",) and empty.acs == ("AC-N-002",) and empty.line and empty.label == "Covers 1 criterion"
    )
    acc = by["acceptance"][0]
    assert acc.kind == "test" and acc.acs == ("AC-N-001",) and acc.file.endswith("test_create_note.py")


def test_tasks_say_whether_they_are_closed_and_placeholders_are_skipped():
    by, _ = example_items()
    status = {i.id: i.label for i in by["module-design"] if i.kind == "task"}
    assert status == {
        "TSK-N-001": "Closed",
        "TSK-N-002": "Closed",
        "TSK-N-003": "Open",
    }  # UC-N-003's row is a placeholder


def test_a_test_inherits_its_module_docstring_and_a_missing_level_is_unplaced(proj: Path):
    write(
        proj / "tests/test_a.py",
        '''\
        """Verifies UC-A-001 · unit rung."""
        import pytest

        @pytest.mark.ac("AC-A-003")
        def test_inherits_the_module_tag():
            pass

        def test_names_its_own_level():
            """Verifies UC-A-001 · integration rung."""

        class TestGroup:
            @pytest.mark.ac("AC-A-010")
            def test_in_a_class(self):
                pass
        ''',
    )
    write(
        proj / "tests/test_b.py",
        """\
        def test_names_nothing():
            pass
        """,
    )
    write(proj / "tests/test_c.py", '"""Verifies UC-A-001 · unit rung."""\ndef test_x():\n    pass\n\n\ndef broken(:\n')
    cfg, ws = ctx(proj)
    found = {t.name: t for t in collect_test_cases(cfg, ws)}
    assert found["test_inherits_the_module_tag"].rung == "unit" and found["test_inherits_the_module_tag"].acs == (
        "AC-A-003",
    )
    assert found["test_names_its_own_level"].rung == "integration"
    assert found["TestGroup.test_in_a_class"].ucs == ("UC-A-001",) and found["TestGroup.test_in_a_class"].acs == (
        "AC-A-010",
    )
    assert (
        found["test_names_nothing"].ucs == () and found["test_names_nothing"].rung is None
    )  # indexed, but part of no V
    assert (
        found["test_c.py"].file.endswith("test_c.py") and found["test_c.py"].line is None
    )  # a syntax error falls back to the file
    items, unplaced = build_v(cfg, ws)
    assert {i.title for i in items if i.phase == "unit"} == {
        "test_inherits_the_module_tag",
        "TestGroup.test_in_a_class",
        "test_c.py",
    }
    assert [u.title for u in unplaced] == ["test_names_nothing"]  # an untagged test is listed, not silently ignored


def test_tests_without_a_use_case_or_level_are_listed_as_unplaced(proj: Path):
    write(
        proj / "tests/test_d.py",
        'import pytest\n\n@pytest.mark.ac("AC-A-003")\ndef test_has_a_marker_only():\n    pass\n',
    )
    write(proj / "tests/test_e.py", '"""Verifies UC-A-001."""\n\ndef test_has_no_level():\n    pass\n')
    cfg, ws = ctx(proj)
    items, unplaced = build_v(cfg, ws)
    assert not [i for i in items if i.kind == "test"]
    assert {u.title: u.label for u in unplaced} == {
        "test_has_a_marker_only": "Names no use case",
        "test_has_no_level": "Names no level (unit, integration, system or acceptance)",
    }


def test_a_use_case_with_a_full_tier_and_no_domain_model_shows_it_as_missing(proj: Path):
    uc_spec(proj, "UC-N-001", rigor="full", context="Notes", acs=[("AC-N-011", "")], tasks=[(1, ["AC-N-011"])])
    cfg, ws = ctx(proj)
    items, _ = build_v(cfg, ws)
    model = next(i for i in items if i.kind == "domain model")
    assert (model.status, model.label, model.file) == ("risk", "Missing", None)


def test_the_export_carries_the_phases_items_and_the_headline_numbers():
    state = export_state(load_config(EXAMPLE), FsWorkspace(EXAMPLE), NoRepo())
    json.dumps(state)
    v = state["v"]
    assert v["phases"][0]["key"] == "requirements" and v["phases"][0]["pairs"] == "acceptance"
    assert v["stats"] == {
        "useCases": {"built": 1, "total": 3},
        "criteria": {"covered": 3, "total": 6},
        "tasks": {"closed": 2, "total": 4},
        "requirements": {"realised": 4, "total": 5},
        "tests": {"unit": 2, "integration": 0, "system": 0, "acceptance": 1, "unplaced": 0},
        "gates": {"passing": 5, "total": 6},
    }
    assert all(
        {"id", "ref", "phase", "kind", "title", "ucs", "file", "line", "status", "label", "acs"} <= set(i)
        for i in v["items"]
    )


@pytest.mark.parametrize("phase", [k for k, *_ in PHASES])
def test_every_item_names_a_known_phase(phase):
    by, _ = example_items()
    assert all(i.phase == phase for i in by[phase])


def test_the_ui_knows_every_phase_the_backend_defines():
    """The UI keeps its own icons, copy and V positions per phase; they must name exactly the backend's nine phases."""
    import re

    ui = Path(__file__).resolve().parent.parent / "src" / "vbench" / "ui" / "src"
    keys = [k for k, *_ in PHASES]
    phases_ui = (ui / "lib" / "phases.tsx").read_text()
    copy = re.findall(r'^  "?([\w-]+)"?: \{\n    icon:', phases_ui, re.MULTILINE)
    assert copy == keys, "src/vbench/ui/src/lib/phases.tsx must define copy for each phase, in V order"
    diagram = (ui / "components" / "VDiagram.tsx").read_text()
    pos = re.search(r"const POS: Record<string, \[number, number\]> = \{(.*?)\n\}", diagram, re.DOTALL).group(1)
    assert sorted(re.findall(r'"?([\w-]+)"?: \[', pos)) == sorted(keys), "VDiagram's POS must place each phase"
