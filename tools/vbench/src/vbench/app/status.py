"""Use case: where is each use case on the V, and what is the next step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..domain.checks import collect_realised, collect_verified
from ..domain.config import Config
from ..domain.model import Result, StatusReport
from ..domain.status import derive_status
from ..ports import Repo, Workspace


@dataclass
class ProjectStatus:
    branch: str
    report: StatusReport


def project_status(cfg: Config, ws: Workspace, repo: Repo, narrow: str | None = None) -> ProjectStatus:
    return ProjectStatus(repo.branch(), derive_status(cfg, ws, narrow))


def status_json(cfg: Config, ws: Workspace, repo: Repo, narrow: str | None = None) -> dict[str, Any]:
    """`vbench status --json` and the MCP `status` tool: the table as data, with where each use case is realised and
    which tests verify it, so a skill reads fields instead of parsing text."""
    st = project_status(cfg, ws, repo, narrow)
    realised, verified = collect_realised(cfg, ws), collect_verified(cfg, ws)
    return {
        "branch": st.branch,
        "specs": len(st.report.rows),
        "useCases": [
            {
                "uc": r.uc,
                "wave": r.wave,
                "stage": r.stage,
                "acs": r.acs,
                "covered": r.covered,
                "enforced": r.enforced,
                "tasks": r.tasks,
                "tasksClosed": r.tasks_closed,
                "code": r.code,
                "tested": r.tested,
                "blockedBy": list(r.blocked_by),
                "next": r.next,
                "realisedIn": sorted(realised.get(r.uc, ())),
                "verifiedBy": [{"file": f, "rung": rung} for f, rung in sorted(verified.get(r.uc, ()))],
            }
            for r in st.report.rows
        ],
        "orphans": st.report.orphans,
        "gates": results_json(st.report.gates),
    }


def results_json(results: list[Result]) -> list[dict[str, Any]]:
    return [{"name": r.name, "passing": r.ok, "lines": r.lines} for r in results]
