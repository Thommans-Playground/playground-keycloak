"""Use case: write the commit message for a finished piece of work, and commit it.

A commit here records one finished TDD cycle (red, green, refactor, each approved), so the checks are about
"finished": the task's criteria all have a test, the gates pass, and the person says the project's own tests pass
(`--green`; vbench never runs the project's toolchain). A half-done cycle is refused, not recorded as WIP. The message
comes from the same rule `vbench check commits` applies later, so it cannot fail that check. Only what is already
staged is committed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.checks import (
    collect_declared,
    collect_realised,
    collect_referenced,
    collect_tasks,
    collect_unspecified,
    collect_verified,
    spec_files,
)
from ..domain.commits import build_subject, infer_type, is_past_tense, normalise_summary, parse_branch
from ..domain.config import Config
from ..domain.errors import AmbiguousError, RefusedError, UsageError
from ..domain.paths import branch_block
from ..ports import Committer, Repo, Runner, Workspace
from .check import run_checks

CODE_TYPES = (
    "feat",
    "fix",
    "refactor",
    "perf",
)  # these change behaviour or structure, so they must be a finished cycle


@dataclass
class CommitPlan:
    message: str
    type: str
    uc: str | None
    task: str | None
    paths: list[str]
    branch: str
    acs: list[str] = field(default_factory=list)  # the criteria the task closes
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)  # why this cannot be committed yet


def _staged_use_cases(cfg: Config, ws: Workspace, paths: list[str]) -> list[str]:
    """Use cases the staged files belong to: a spec's own name, or a `Realises`/`Verifies` tag in the file."""
    staged = set(paths)
    found = {uc for uc, p in spec_files(cfg, ws).items() if p in staged}
    found |= {uc for uc, files in collect_realised(cfg, ws).items() if staged & set(files)}
    found |= {uc for uc, hits in collect_verified(cfg, ws).items() if staged & {f for f, _ in hits}}
    return sorted(found)


def _staged_tasks(cfg: Config, ws: Workspace, uc: str, paths: list[str]) -> list[str]:
    """Tasks of this use case whose criteria the staged files mark."""
    staged, spec = set(paths), spec_files(cfg, ws).get(uc)
    marked = {ac for ac, files in collect_referenced(cfg, ws).items() if staged & set(files)}
    return sorted(t for t, (path, acs) in collect_tasks(cfg, ws).items() if path == spec and marked & set(acs))


def plan_commit(
    cfg: Config,
    ws: Workspace,
    repo: Repo,
    *,
    summary: str,
    type_: str | None = None,
    uc: str | None = None,
    task: str | None = None,
    body: str = "",
    breaking: bool = False,
) -> CommitPlan:
    paths = repo.staged()
    if not paths:
        raise UsageError("Nothing is staged. `git add` the files of the finished task, then run this again.")
    branch = repo.branch()
    info = parse_branch(cfg, branch)
    kind = (type_ or infer_type(cfg, paths, info.type)).lower()

    uc = uc or info.uc
    if not uc and kind != "chore":
        found = _staged_use_cases(cfg, ws, paths)
        if len(found) > 1:
            raise AmbiguousError(
                f"The staged files belong to more than one use case ({', '.join(found)}). Commit them one use case "
                "at a time (unstage some), or name one with --uc."
            )
        uc = found[0] if found else None

    task = task or info.task
    if uc and not task and kind in (*CODE_TYPES, "test"):
        candidates = _staged_tasks(cfg, ws, uc, paths)
        if len(candidates) > 1:
            raise AmbiguousError(
                f"The staged tests close more than one task of {uc} ({', '.join(candidates)}). A commit is one "
                "finished task: unstage the other task's files, or name this one with --task."
            )
        task = candidates[0] if candidates else None

    subject = build_subject(cfg, kind, uc, task, summary, breaking)
    plan = CommitPlan(subject, kind, uc, task, paths, branch)

    tasks = collect_tasks(cfg, ws)
    if task:
        owner = spec_files(cfg, ws).get(uc or "")
        if task not in tasks or tasks[task][0] != owner:
            raise UsageError(f"{task} is not in {uc}'s task table; add the row to the spec first.")
        plan.acs = list(tasks[task][1])
    if kind in CODE_TYPES:
        _check_finished(cfg, ws, plan)

    unstaged = repo.unstaged()
    if unstaged:
        shown = ", ".join(unstaged[:5]) + (f" and {len(unstaged) - 5} more" if len(unstaged) > 5 else "")
        plan.warnings.append(f"{len(unstaged)} changed file(s) are not staged and stay out of this commit: {shown}.")
    behind = repo.behind(cfg.base_branch) if branch and branch != cfg.base_branch else None
    if behind:
        plan.warnings.append(
            f"The branch is {behind} commit(s) behind `{cfg.base_branch}`; merge or rebase it first so this "
            "work does not overwrite a newer change."
        )
    if is_past_tense(normalise_summary(summary)):
        plan.warnings.append("Write the summary in the imperative (`add login`, not `added login`).")
    if branch and branch != cfg.base_branch and not cfg.branch_re.match(branch) and not branch.startswith("release/"):
        plan.warnings.append(
            f"The branch `{branch}` does not follow `<type>/<slug>`; `vbench check commits` will flag it."
        )

    lines = []
    if plan.acs and kind in ("feat", "fix"):
        lines.append(f"Closes: {', '.join(plan.acs)}")
    if breaking and "BREAKING CHANGE" not in body:
        lines.append(f"BREAKING CHANGE: {normalise_summary(summary)}")
    if body.strip():
        lines.append(body.strip())
    if lines:
        plan.message = subject + "\n\n" + "\n\n".join(lines)
    return plan


def _check_finished(cfg: Config, ws: Workspace, plan: CommitPlan) -> None:
    """A code commit is a finished cycle: every criterion of its task has a test, and the gates pass."""
    if plan.task:
        declared, planned = collect_declared(cfg, ws)
        enforced = set(declared) - planned - collect_unspecified(cfg, ws)
        referenced = collect_referenced(cfg, ws)
        open_acs = [ac for ac in plan.acs if ac in enforced and ac not in referenced]
        if open_acs:
            plan.blockers.append(
                f"{plan.task} is not finished: no test marks {', '.join(open_acs)}. Complete the red-green-refactor "
                "cycle, then commit."
            )
    else:
        plan.warnings.append("No task is named, so whether the cycle is finished was not checked (--task TSK-…).")
    # Another use case may still be open: that is its own V. Only a failure that names this use case or one of the
    # staged files blocks the commit; the rest is reported.
    mine = [x for x in (plan.uc, *plan.paths) if x]
    ours, elsewhere = [], []
    for r in run_checks(cfg, ws):
        if r.ok:
            continue
        # Other tasks of this use case are not started yet, so their criteria are rightly uncovered; this task's own
        # criteria were checked above.
        lines = [x for x in r.lines if not (r.name == "acs" and "UNCOVERED" in x)]
        (ours if any(m in line for line in lines for m in mine) else elsewhere).append(r.name)
    if ours:
        plan.blockers.append(
            f"These gates fail for this work: {', '.join(ours)}. Run `vbench check` and fix them first."
        )
    if elsewhere:
        plan.warnings.append(f"Gates failing elsewhere in the project (not this work): {', '.join(elsewhere)}.")


def make_commit(
    cfg: Config,
    repo: Repo,
    committer: Committer,
    plan: CommitPlan,
    *,
    green: bool = False,
    allow_default_branch: bool = False,
    runner: Runner | None = None,
) -> str:
    if plan.blockers:
        raise RefusedError(" ".join(plan.blockers))
    if why := branch_block(repo.branch(), cfg.base_branch, allow_default_branch):
        raise RefusedError(why)
    if repo.staged() != plan.paths:
        raise RefusedError("The staged files changed since the message was made. Run it again.")
    message = plan.message
    if plan.type in CODE_TYPES:
        message += ("\n" if "\n\n" in message else "\n\n") + _test_evidence(cfg, runner, green)
    return committer.commit_staged(message)


def _test_evidence(cfg: Config, runner: Runner | None, green: bool) -> str:
    """Prove the tests pass by running them, or (with no test command configured) take the committer's word.

    Returns the trailer line for the commit, so the history says which it was."""
    command = cfg.commands.get("test", "").strip()
    if command and runner:
        result = runner.run(command)
        if result.code:
            raise RefusedError(
                f"`{command}` failed (exit {result.code}); a code commit needs the tests green.\n{result.tail}"
            )
        return f"Tested: `{command}` passed (run by vbench)"
    if not green:
        raise RefusedError(
            "No test command is set under [commands] in .vbench/config.toml, so vbench cannot run the tests. "
            'Set `test = "..."` there (vbench then runs it and no flag is needed), '
            "or run them yourself and add --green."
        )
    return "Tested: reported green by the committer (vbench did not run it)"


__all__ = ["CODE_TYPES", "CommitPlan", "make_commit", "plan_commit"]
