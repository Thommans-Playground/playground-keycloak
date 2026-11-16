"""The pure part of `vbench commit`: reading a branch, tidying a summary, building a subject that satisfies the
convention, and guessing the type from the files."""

from __future__ import annotations

import pytest

from vbench.domain.commits import (
    MAX_SUBJECT,
    BranchInfo,
    build_subject,
    infer_type,
    normalise_summary,
    parse_branch,
)
from vbench.domain.config import Config
from vbench.domain.errors import UsageError

CFG = Config.from_raw({})


def test_a_branch_names_its_type_use_case_and_task():
    assert parse_branch(CFG, "feat/uc-a-001-login") == BranchInfo("feat", "UC-A-001", None)
    assert parse_branch(CFG, "fix/uc-b-012-tsk-b-003-null-title") == BranchInfo("fix", "UC-B-012", "TSK-B-003")
    assert parse_branch(CFG, "docs/glossary") == BranchInfo("docs", None, None)
    for none in ("main", "", "feature/uc-a-001-x", "release/1.0"):
        assert parse_branch(CFG, none).type is None


def test_a_summary_is_tidied_but_never_cut():
    assert normalise_summary("  Add the login form.  ") == "add the login form"
    assert normalise_summary("Add\nlogin\n\tform") == "add login form"
    assert normalise_summary("JWT tokens expire") == "JWT tokens expire"  # an acronym keeps its capitals
    assert normalise_summary("x") == "x"
    for empty in ("", "   ", ".", "\n"):
        with pytest.raises(UsageError, match="summary"):
            normalise_summary(empty)


def test_the_subject_follows_the_convention_the_gate_enforces():
    cases = [
        (("feat", "UC-A-001", "TSK-A-002", "Add login"), "feat(UC-A-001/TSK-A-002): add login"),
        (("fix", "UC-A-001", None, "Stop the crash"), "fix(UC-A-001): stop the crash"),
        (("chore", None, None, "Bump the lockfile"), "chore: bump the lockfile"),
    ]
    for args, expected in cases:
        subject = build_subject(CFG, *args)
        assert subject == expected and CFG.commit_re.match(subject)


def test_a_subject_that_would_break_the_convention_is_refused_not_repaired():
    for bad, why in [
        (("feat", None, None, "add login"), "use case"),  # only chore may omit the use case
        (("feat", None, "TSK-A-001", "add login"), "use case"),  # a task needs its use case
        (("WIP", "UC-A-001", None, "add login"), "type"),
        (("feat", "uc-1", None, "add login"), "UC"),
        (("feat", "UC-A-001", None, "x" * MAX_SUBJECT), "characters"),
    ]:
        with pytest.raises(UsageError, match=why):
            build_subject(CFG, *bad)


def test_the_type_comes_from_the_flag_then_the_branch_then_the_files():
    tests, prod, docs = ["tests/test_a.py"], ["src/a.py"], ["docs/x.md"]
    assert infer_type(CFG, tests, None) == "test"
    assert infer_type(CFG, docs, None) == "docs"
    assert infer_type(CFG, prod + tests, None) == "feat"  # a finished cycle: behaviour and the test that drove it
    assert infer_type(CFG, prod, None) == "refactor"  # code moved with no test change
    assert infer_type(CFG, prod + tests + docs, None) == "feat"  # documents do not change the answer
    assert infer_type(CFG, prod + tests, "fix") == "fix"
    assert infer_type(CFG, prod, "fix") == "fix"
    assert infer_type(CFG, tests, "fix") == "test"  # a branch never makes a tests-only commit a fix or a feature
    assert infer_type(CFG, docs, "feat") == "docs"


def test_conventional_commits_shape_and_a_breaking_change():
    from vbench.domain.commits import build_subject

    assert build_subject(CFG, "feat", "UC-A-001", "TSK-A-002", "add login") == "feat(UC-A-001/TSK-A-002): add login"
    assert build_subject(CFG, "feat", "UC-A-001", None, "drop v1", breaking=True) == "feat(UC-A-001)!: drop v1"
    for good in ("feat(UC-A-001)!: x", "perf(UC-A-001/TSK-A-001): x", "ci: pin the action", "build: bump uv"):
        assert CFG.commit_re.match(good), good
    for old in ("FEAT-UC-A-001: x", "feat-UC-A-001: x", "Feat(UC-A-001): x", "feat(UC-A-001) x", "feat(uc-a-001): x"):
        assert not CFG.commit_re.match(old), old
