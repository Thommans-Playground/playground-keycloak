"""`vbench doctor`: what has drifted in the working copy, found from facts and never fixed on its own."""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.config import Config
from ..ports import Repo, Workspace
from .status import project_status


@dataclass(frozen=True)
class Finding:
    level: str  # "problem" | "note"
    text: str
    fix: str


def diagnose(cfg: Config, ws: Workspace, repo: Repo) -> list[Finding]:
    found: list[Finding] = []
    branch = repo.branch()
    if not branch:
        found.append(
            Finding("problem", "HEAD is detached, so commits would belong to no branch.", "git switch -c <type>/<slug>")
        )
    elif branch != cfg.base_branch:
        behind = repo.behind(cfg.base_branch)
        if behind:
            found.append(
                Finding(
                    "problem",
                    f"The branch `{branch}` is {behind} commit(s) behind `{cfg.base_branch}`; "
                    "merging it could overwrite newer work.",
                    f"git merge {cfg.base_branch}  (or rebase)",
                )
            )
        elif behind is None:
            found.append(
                Finding("note", f"Could not compare with `{cfg.base_branch}` (no such branch or remote).", "git fetch")
            )
        age = repo.branch_age_days(cfg.base_branch)
        if age is not None and age > cfg.branch_max_days:
            found.append(
                Finding(
                    "note",
                    f"The branch `{branch}` is {age} days old (the limit is {cfg.branch_max_days}); "
                    "trunk-based branches are short-lived.",
                    "merge what is finished, or split the rest into its own branch",
                )
            )
        if not cfg.branch_re.match(branch) and not branch.startswith("release/"):
            found.append(
                Finding(
                    "note",
                    f"The branch `{branch}` does not follow `<type>/<slug>`; `vbench check commits` will flag it.",
                    f"git branch -m {cfg.commit_types[0]}/<use-case-id>-<slug>",
                )
            )
    for path in repo.stale_worktrees():
        found.append(Finding("problem", f"The worktree {path} no longer exists on disk.", "git worktree prune"))
    if n := len(repo.unstaged()):
        found.append(
            Finding("note", f"{n} changed file(s) are not staged.", "git add <files>, or leave them out on purpose")
        )
    for g in project_status(cfg, ws, repo).report.gates:
        if not g.ok:
            found.append(Finding("problem", f"The `{g.name}` gate is failing.", f"vbench check {g.name}"))
    return found
