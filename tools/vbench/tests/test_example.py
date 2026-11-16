"""The notes-app example is what the dashboard shows when pointed at it. It must keep telling its story."""

from __future__ import annotations

from pathlib import Path

from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.app.export import export_state
from vbench.domain.checks import check_diagrams, check_docs, check_links, check_refs, check_rungs

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "notes-app"


class NoRepo:
    def branch(self) -> str:
        return ""

    def commits(self, base: str) -> list[str]:
        return []


def test_the_example_is_one_built_one_in_code_and_one_not_started():
    state = export_state(load_config(EXAMPLE), FsWorkspace(EXAMPLE), NoRepo())
    by = {u["id"]: u for u in state["useCases"]}
    assert {u: by[u]["stage"] for u in by} == {"UC-N-001": "verify", "UC-N-002": "code", "UC-N-003": "requirements"}
    assert by["UC-N-003"]["blockedBy"] == ["UC-N-002"] and by["UC-N-002"]["blockedBy"] == []
    assert state["next"]["command"] == "/vbench:v-3-code UC-N-002 TSK-N-003"


def test_only_the_acs_gate_fails_and_it_is_the_deliberate_one():
    cfg, ws = load_config(EXAMPLE), FsWorkspace(EXAMPLE)
    for check in (check_refs, check_rungs, check_links, check_diagrams, check_docs):
        assert check(cfg, ws).ok, check.__name__
    gates = {g["name"]: g["ok"] for g in export_state(cfg, ws, NoRepo())["gates"]}
    assert gates == {"refs": True, "rungs": True, "acs": False, "links": True, "diagrams": True, "docs": True}
