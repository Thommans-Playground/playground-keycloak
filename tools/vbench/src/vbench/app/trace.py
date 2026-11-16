"""Use case: read a use case's chain back out of the project, step by step (`vbench trace`)."""

from __future__ import annotations

from typing import Any

from ..domain.checks import spec_files, step_rows_of
from ..domain.config import Config
from ..domain.errors import UsageError
from ..domain.steps import render_tour
from ..ports import Workspace


def _known(cfg: Config, ws: Workspace, uc: str) -> str:
    uc = uc.upper()
    specs = spec_files(cfg, ws)
    if uc not in specs:
        raise UsageError(f"no spec for {uc} under {cfg.specs}; known: {', '.join(sorted(specs)) or 'none yet'}.")
    return uc


def trace_text(cfg: Config, ws: Workspace, uc: str) -> list[str]:
    """The use case's steps in diagram order, each with its task, code and test."""
    uc = _known(cfg, ws, uc)
    return render_tour(uc, step_rows_of(cfg, ws, uc))


def trace_json(cfg: Config, ws: Workspace, uc: str) -> dict[str, Any]:
    """The same chain as data, for the dashboard and for skills."""
    uc = _known(cfg, ws, uc)
    return {
        "uc": uc,
        "steps": [
            {
                "id": r.step.id,
                "message": r.step.label,
                "planned": r.step.planned,
                "diagram": {"file": r.step.path, "line": r.step.line},
                "tasks": r.tasks,
                "code": [{"file": f, "line": n} for f, n in r.code],
                "tests": r.tests,
                "hollowTests": r.hollow,
            }
            for r in step_rows_of(cfg, ws, uc)
        ],
    }
