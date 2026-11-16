"""Use case: run the gates."""

from __future__ import annotations

from ..domain.checks import CHECKS, check_commits
from ..domain.config import Config
from ..domain.errors import UsageError
from ..domain.graph import read_links, to_mermaid
from ..domain.model import Result
from ..ports import Repo, Workspace


def run_checks(cfg: Config, ws: Workspace, which: str = "all", matrix: bool = False) -> list[Result]:
    if matrix and which == "refs":
        raise UsageError("--matrix applies to rungs, acs, links and diagrams only.")
    names = list(CHECKS) if which == "all" else [which]
    if matrix:
        return [CHECKS[n](cfg, ws, matrix=True) for n in names if n != "refs"]
    return [CHECKS[n](cfg, ws) for n in names]


def run_commit_check(
    cfg: Config, ws: Workspace, repo: Repo, base: str | None = None, branch: str | None = None
) -> Result:
    """The convention gate for a branch: its commits since `base` and its name. Needs git, so it is explicit."""
    return check_commits(cfg, ws, repo.commits(base or cfg.base_branch), repo.branch() if branch is None else branch)


def links_mermaid(cfg: Config, ws: Workspace) -> str:
    """The use-case build order as a fenced Mermaid block, ready to paste into the backlog."""
    return "```mermaid\n" + to_mermaid(read_links(cfg, ws)) + "\n```"
