"""Building a commit subject that follows the convention, from what is known about the work.

The convention is Conventional Commits with the ids as the scope,
`<type>[(<UC>[/<TSK>])][!]: <description>` (`Config.commit_re`), and `vbench check commits` is what
enforces it afterwards. This module is the same rule used the other way round: it makes the subject, and refuses
rather than repairs when the facts do not fit. Pure: no files, no git.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass

from .config import Config
from .errors import UsageError

MAX_SUBJECT = 72  # characters in the whole subject; a longer one is refused, never cut
PAST_TENSE = ("added", "fixed", "updated", "removed", "changed", "implemented", "created", "renamed")
DOC_SUFFIXES = (".md", ".puml", ".rst", ".txt")


@dataclass(frozen=True)
class BranchInfo:
    type: str | None
    uc: str | None
    task: str | None


def parse_branch(cfg: Config, branch: str) -> BranchInfo:
    """What a branch name says: `feat/uc-a-001-tsk-a-002-login` is feat, UC-A-001, TSK-A-002."""
    prefix, _, slug = branch.partition("/")
    kind = prefix if slug and prefix in cfg.commit_types else None
    if kind is None:
        return BranchInfo(None, None, None)
    uc = re.search(cfg.uc_pattern, slug, re.IGNORECASE)
    task = re.search(cfg.task_pattern, slug, re.IGNORECASE)
    return BranchInfo(kind, uc.group(0).upper() if uc else None, task.group(0).upper() if task else None)


def normalise_summary(summary: str) -> str:
    """One line, no trailing full stop, first letter lower case unless it starts an acronym (`JWT tokens`)."""
    text = re.sub(r"\s+", " ", summary).strip().rstrip(".").strip()
    if not text:
        raise UsageError("The commit needs a summary: say what the change does, in a few words (-m).")
    if not text[1:2].isupper():
        text = text[0].lower() + text[1:]
    return text


def build_subject(
    cfg: Config, type_: str, uc: str | None, task: str | None, summary: str, breaking: bool = False
) -> str:
    kind = type_.lower()
    if kind not in cfg.commit_types:
        raise UsageError(f"`{type_}` is not a commit type here. Use one of {', '.join(cfg.commit_types)}.")
    if task and not uc:
        raise UsageError(f"{task} belongs to a use case; name it with --uc.")
    if kind != "chore" and not uc:
        raise UsageError(f"A {kind} commit must name its use case (--uc UC-A-001); only chore may leave it out.")
    if uc and not re.fullmatch(cfg.uc_pattern, uc):
        raise UsageError(f"`{uc}` is not a use case id (expected like UC-A-001).")
    if task and not re.fullmatch(cfg.task_pattern, task):
        raise UsageError(f"`{task}` is not a task id (expected like TSK-A-001).")
    scope = f"({uc}{f'/{task}' if task else ''})" if uc else ""
    subject = f"{kind}{scope}{'!' if breaking else ''}: {normalise_summary(summary)}"
    if len(subject) > MAX_SUBJECT:
        raise UsageError(
            f"The subject is {len(subject)} characters; the limit is {MAX_SUBJECT}. Shorten the summary "
            f"(`{subject}`) and put the detail in --body."
        )
    if not cfg.commit_re.match(subject):  # a project's own commit_pattern may be stricter than the default shape
        raise UsageError(f"`{subject}` does not match this project's commit pattern.")
    return subject


def is_past_tense(summary: str) -> bool:
    first = summary.strip().split(" ", 1)[0].lower()
    return first in PAST_TENSE


def classify(cfg: Config, paths: list[str]) -> tuple[list[str], list[str], list[str]]:
    """(tests, docs, code) among the given project-relative paths."""
    tests, docs, code = [], [], []
    for p in paths:
        under_tests = any(p == t.rstrip("/") or p.startswith(t.rstrip("/") + "/") for t in cfg.tests)
        if under_tests and p.endswith(cfg.test_ext):
            tests.append(p)
        elif posixpath.splitext(p)[1] in DOC_SUFFIXES:
            docs.append(p)
        else:
            code.append(p)
    return tests, docs, code


def infer_type(cfg: Config, paths: list[str], branch_type: str | None) -> str:
    """From the files: only documents is docs, only tests is test, tests with code is feat, code alone is refactor.
    When code is staged the branch's type (feat, fix, refactor) decides instead, because the files cannot tell a
    feature from a fix. A branch never turns a tests-only or documents-only commit into a feature."""
    tests, docs, code = classify(cfg, paths)
    if code:
        return branch_type or ("feat" if tests else "refactor")
    if tests:
        return "test"
    return "docs" if docs else "chore"
