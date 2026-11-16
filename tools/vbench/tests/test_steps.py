"""Verifies the step ids: a sequence diagram's messages, cited by tasks, tagged in code and driven by tests."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from vbench import cli
from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.domain.checks import check_steps, step_rows_of
from vbench.domain.next import ready_steps

REAL = 'def test_it():\n    assert str(1) == "1"\n'


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text), encoding="utf-8")


def ctx(proj: Path):
    return load_config(proj), FsWorkspace(proj)


def design(proj: Path, n: int = 1, steps=("STP-A-001", "STP-A-002"), tasks=None, depends: str = "-", planned=()):
    """A designed use case UC-A-00<n>: a sequence diagram with `steps`, and one task per entry of `tasks`."""
    uc = f"UC-A-{n:03d}"
    msgs = "\n".join(f"A -> B : {s} do it{' (planned)' if s in planned else ''}" for s in steps)
    write(proj / f"docs/usecase-diagrams/{uc}-thing-sequence.puml", f"@startuml\n{msgs}\n@enduml\n")
    rows = "\n".join(
        f"| **TSK-A-{n:03d}** | does it | AC-A-{n:03d} | {', '.join(tasks) if tasks else ''} |".split("\n")
    )
    ac = f"| **AC-A-{n:03d}** | Given x, when y, then z. | REQ-FR-001 |"
    write(
        proj / f"docs/usecase-diagrams/{uc}-thing.md",
        f"# {uc}\n\n| **Rigor** | standard |\n| **Depends on** | {depends} |\n\n"
        f"## Acceptance criteria\n\n| AC id | G/W/T | Satisfies |\n|---|---|---|\n{ac}\n\n"
        f"## Delivery tasks\n\n| Task id | Description | Closes ACs | Steps |\n|---|---|---|---|\n{rows}\n",
    )
    return uc


def build(proj: Path, uc: str, tags: dict[str, str], tested: dict[str, str]):
    """Code with `Realises <uc> · <step>` per tag line and a real test per entry (docstring clause -> step list)."""
    lines = "\n".join(f"x = 1  # Realises {uc} · {s}" for s in tags)
    write(proj / "src/thing.py", f'"""Realises {uc}"""\n{lines}\n')
    body = "\n".join(
        f'def test_{i}():\n    """Verifies {uc} · {s} · unit rung."""\n    assert str({i}) == "{i}"\n'
        for i, s in enumerate(tested)
    )
    write(proj / "tests/test_thing.py", body)


def test_a_fresh_project_and_an_unnumbered_diagram_pass_the_step_gate(proj: Path):
    assert check_steps(*ctx(proj)).ok
    write(proj / "docs/usecase-diagrams/UC-A-001-thing-sequence.puml", "@startuml\nA -> B : 1.1 do it\n@enduml\n")
    assert check_steps(*ctx(proj)).ok  # numbering is how a diagram opts in


def test_every_step_of_a_designed_use_case_must_be_cited_by_a_task(proj: Path):
    design(proj, tasks=["STP-A-001"])
    res = check_steps(*ctx(proj))
    assert not res.ok and "STP-A-002 (UC-A-001): no task row cites it" in res.render()
    assert "STP-A-001 (UC-A-001): no task" not in res.render()
    design(proj, tasks=["STP-A-001", "STP-A-002"])
    assert check_steps(*ctx(proj)).ok  # no code yet, so no code or test is owed


def test_a_use_case_with_code_owes_each_step_a_tag_and_a_real_test(proj: Path):
    uc = design(proj, tasks=["STP-A-001", "STP-A-002"])
    build(proj, uc, tags={"STP-A-001": ""}, tested={"STP-A-001": ""})
    text = check_steps(*ctx(proj)).render()
    assert "STP-A-002 (UC-A-001): the use case has code, but nothing says `Realises UC-A-001 · STP-A-002`" in text
    assert "STP-A-002 (UC-A-001): no test says `Verifies UC-A-001 · STP-A-002" in text
    assert "STP-A-001 (UC-A-001)" not in text
    build(proj, uc, tags={"STP-A-001": "", "STP-A-002": ""}, tested={"STP-A-001": "", "STP-A-002": ""})
    assert check_steps(*ctx(proj)).ok


def test_a_tag_in_a_docstring_with_no_real_test_does_not_drive_a_step(proj: Path):
    uc = design(proj, steps=("STP-A-001",), tasks=["STP-A-001"])
    write(proj / "src/thing.py", f'"""Realises {uc}"""\nx = 1  # Realises {uc} · STP-A-001\n')
    write(proj / "tests/test_thing.py", f'def test_it():\n    """Verifies {uc} · STP-A-001 · unit rung."""\n    pass\n')
    res = check_steps(*ctx(proj))
    assert not res.ok and "no real test stands behind the docstring" in res.render()


def test_a_planned_step_owes_no_task_code_or_test(proj: Path):
    uc = design(proj, tasks=["STP-A-001"], planned=("STP-A-002",))
    build(proj, uc, tags={"STP-A-001": ""}, tested={"STP-A-001": ""})
    assert check_steps(*ctx(proj)).ok


def test_citing_a_step_that_does_not_exist_or_belongs_to_another_use_case_fails(proj: Path):
    uc = design(proj, tasks=["STP-A-001", "STP-A-002"])
    other = design(proj, n=2, steps=("STP-A-003",), tasks=["STP-A-003"])
    write(
        proj / "src/thing.py",
        f'"""Realises {uc}"""\nx = 1  # Realises {uc} · STP-A-009\ny = 2  # Realises {uc} · STP-A-003\n',
    )
    text = check_steps(*ctx(proj)).render()
    assert "STP-A-009 is in no sequence diagram" in text
    assert f"STP-A-003 belongs to {other}, not {uc}" in text


def test_a_step_id_is_unique_across_use_cases(proj: Path):
    design(proj, tasks=["STP-A-001", "STP-A-002"])
    design(proj, n=2, steps=("STP-A-002",), tasks=["STP-A-002"])
    assert "a step id is unique" in check_steps(*ctx(proj)).render()


def test_trace_reads_the_chain_back_in_diagram_order(proj: Path, capsys):
    uc = design(proj, tasks=["STP-A-001", "STP-A-002"])
    build(proj, uc, tags={"STP-A-001": "", "STP-A-002": ""}, tested={"STP-A-001": "", "STP-A-002": ""})
    rows = step_rows_of(*ctx(proj), uc)
    assert [r.step.id for r in rows] == ["STP-A-001", "STP-A-002"]
    assert (
        rows[0].tasks == ["TSK-A-001"]
        and rows[0].code == [("src/thing.py", 2)]
        and rows[0].tests == ["tests/test_thing.py"]
    )
    assert cli.main(["trace", uc]) == 0
    assert "STP-A-001  do it" in capsys.readouterr().out
    assert cli.main(["trace", uc, "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["steps"][1]["id"] == "STP-A-002" and data["steps"][1]["code"] == [{"file": "src/thing.py", "line": 3}]
    assert cli.main(["trace", "UC-A-099"]) == 2  # no such spec


def test_vbench_id_step_skips_ids_already_drawn_in_a_diagram(proj: Path, capsys):
    design(proj, steps=("STP-A-001", "STP-A-004"), tasks=["STP-A-001", "STP-A-004"])
    assert cli.main(["id", "step", "--area", "A", "--count", "2"]) == 0
    assert capsys.readouterr().out.split() == ["STP-A-005", "STP-A-006"]


def test_next_ready_lists_every_unblocked_use_case_and_default_next_is_unchanged(proj: Path, capsys):
    design(proj, n=1, steps=("STP-A-001",), tasks=["STP-A-001"])
    design(proj, n=2, steps=("STP-A-002",), tasks=["STP-A-002"])
    design(proj, n=3, steps=("STP-A-003",), tasks=["STP-A-003"], depends="UC-A-001")
    assert cli.main(["next", "--ready", "--json"]) == 0
    ready = json.loads(capsys.readouterr().out)["ready"]
    assert [r["uc"] for r in ready] == ["UC-A-001", "UC-A-002"]  # UC-A-003 waits for UC-A-001
    assert cli.main(["next", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["uc"] == "UC-A-001"
    cfg, ws = ctx(proj)
    from vbench.domain.status import derive_status

    assert len(ready_steps(derive_status(cfg, ws).rows)) == 2
