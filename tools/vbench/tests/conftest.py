"""Fixtures shared by the test modules."""

from __future__ import annotations

from pathlib import Path

import pytest

from vbench import cli


@pytest.fixture
def proj(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A project with the harness only (no stack skeleton): docs, config and the gates, in a temp folder."""
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--ci", "none", "--stack", "none"]) == 0  # the stack has its own tests
    return tmp_path
