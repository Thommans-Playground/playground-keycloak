"""Every artifact has a three-part id. Authored ones carry it in their document; discovered ones (contexts, models,
diagrams, code files, tests) get it from the append-only registry that `vbench sync` extends."""

from __future__ import annotations

import re
from pathlib import Path

from vbench import cli
from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.domain.checks import check_docs
from vbench.domain.registry import current_rows, refs_for
from vbench.domain.vview import build_v

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "notes-app"
THREE_PARTS = re.compile(
    r"^[A-Z]{2,4}-[A-Z]{2,4}-\d{3}$|^UC-[A-Z]-\d{3}-TSK-[A-Z]-\d{3}$|^(TSK|AC|UC|EPC)-[A-Z]-\d{3}$"
)


def example_refs() -> dict[tuple[str, str], str]:
    cfg, ws = load_config(EXAMPLE), FsWorkspace(EXAMPLE)
    items, unplaced = build_v(cfg, ws)
    return refs_for(cfg, ws, items, unplaced)


def test_every_item_in_the_example_has_a_unique_three_part_id():
    refs = example_refs()
    assert refs and len(set(refs.values())) == len(refs)
    assert all(THREE_PARTS.match(r) for r in refs.values()), sorted(refs.values())


def test_the_example_gets_the_documented_ids():
    got = set(example_refs().values())
    assert {
        "STK-REQ-001",
        "REQ-FR-001",
        "REQ-NFR-002",
        "TSK-N-001",
        "SYS-CTX-001",
        "ARC-DOM-001",
        "MOD-SEQ-001",
        "MOD-STA-001",
        "COD-SRC-001",
        "TST-ACC-001",
        "TST-UNT-001",
    } <= got


def test_the_registry_in_the_example_is_up_to_date():
    cfg, ws = load_config(EXAMPLE), FsWorkspace(EXAMPLE)
    assert check_docs(cfg, ws).ok
    assert {a for _, a in current_rows(cfg, ws)} >= {"notes", "src/notes/create.py", "UC-N-001:sequence"}


def test_the_registry_only_ever_grows(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--stack", "none", "--ci", "none"]) == 0
    (tmp_path / "docs/usecase-diagrams").mkdir(exist_ok=True)
    assert cli.main(["new", "uc", "--area", "A", "--title", "Log in"]) == 0
    for name in ("one.py", "two.py"):
        (tmp_path / "src").mkdir(exist_ok=True)
        (tmp_path / f"src/{name}").write_text('"""Realises UC-A-001"""\n')
    assert not check_docs(load_config(tmp_path), FsWorkspace(tmp_path)).ok  # two new code files, not registered yet
    assert cli.main(["sync"]) == 0
    first = current_rows(load_config(tmp_path), FsWorkspace(tmp_path))
    assert ("COD-SRC-001", "src/one.py") in first and ("COD-SRC-002", "src/two.py") in first

    (tmp_path / "src/one.py").rename(tmp_path / "src/uno.py")  # a renamed file is a new alias with a new id ...
    (tmp_path / "src/three.py").write_text('"""Realises UC-A-001"""\n')
    assert cli.main(["sync"]) == 0
    after = current_rows(load_config(tmp_path), FsWorkspace(tmp_path))
    assert after[: len(first)] == first  # ... and no row was rewritten, dropped or renumbered
    assert ("COD-SRC-003", "src/three.py") in after and ("COD-SRC-004", "src/uno.py") in after
    assert check_docs(load_config(tmp_path), FsWorkspace(tmp_path)).ok


def test_new_id_prints_the_next_free_ids_and_writes_nothing(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--stack", "none", "--ci", "none"]) == 0
    assert cli.main(["new", "uc", "--area", "A", "--title", "Log in"]) == 0
    capsys.readouterr()
    assert cli.main(["new", "id", "ac", "--area", "a", "--count", "2"]) == 0
    assert capsys.readouterr().out.split() == ["AC-A-002", "AC-A-003"]  # the scaffold already holds AC-A-001
    assert cli.main(["new", "id", "task", "--area", "A"]) == 0
    assert capsys.readouterr().out.split() == ["TSK-A-002"]
    assert cli.main(["new", "id", "fr"]) == 0
    assert capsys.readouterr().out.split() == ["REQ-FR-001"]
    assert cli.main(["new", "id", "request"]) == 0
    assert capsys.readouterr().out.split() == ["STK-REQ-001"]
