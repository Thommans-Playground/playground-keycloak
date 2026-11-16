"""`GitRepo.staged`, `unstaged` and `commit_staged` against a real repository."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from vbench.adapters.git import GitRepo
from vbench.domain.errors import UsageError


def git(root: Path, *args: str) -> str:
    env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True, env={**__import__("os").environ, **env}
    ).stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "feat/x")
    (tmp_path / "a.txt").write_text("a")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "chore: first")
    return tmp_path


def test_staged_and_unstaged_are_told_apart_and_names_survive_spaces(repo: Path):
    (repo / "a.txt").write_text("changed")
    (repo / "with space.txt").write_text("x")
    (repo / "b.txt").write_text("b")
    git(repo, "add", "b.txt", "with space.txt")
    (repo / "c.txt").write_text("untracked")
    r = GitRepo(repo)
    assert r.staged() == ["b.txt", "with space.txt"]
    assert r.unstaged() == ["a.txt", "c.txt"]


def test_paths_are_relative_to_the_project_even_inside_a_repository_subfolder(repo: Path):
    (repo / "proj").mkdir()
    (repo / "proj" / "f.txt").write_text("x")
    (repo / "outside.txt").write_text("y")
    git(repo, "add", "-A")
    assert GitRepo(repo / "proj").staged() == ["f.txt"]  # --relative: only this folder, named from here


def test_commit_staged_records_only_what_is_staged(repo: Path):
    (repo / "a.txt").write_text("changed but not staged")
    (repo / "b.txt").write_text("b")
    git(repo, "add", "b.txt")
    sha = GitRepo(repo).commit_staged("feat(UC-A-001): add b")
    assert sha and git(repo, "log", "-1", "--format=%s").strip() == "feat(UC-A-001): add b"
    assert git(repo, "show", "--name-only", "--format=", "HEAD").split() == ["b.txt"]
    assert GitRepo(repo).unstaged() == ["a.txt"]  # the other edit is still there, untouched


def test_nothing_staged_is_an_error_that_says_why(repo: Path):
    with pytest.raises(UsageError, match="git commit failed"):
        GitRepo(repo).commit_staged("chore: nothing")


def test_behind_counts_the_commits_the_base_has_that_the_branch_lacks(repo: Path):
    git(repo, "branch", "main")
    r = GitRepo(repo)
    assert r.behind("main") == 0
    git(repo, "checkout", "-q", "main")
    (repo / "m.txt").write_text("m")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "chore: on main")
    git(repo, "checkout", "-q", "feat/x")
    assert r.behind("main") == 1
    assert r.behind("no-such-branch") is None


def test_branch_age_counts_days_since_the_oldest_commit_off_the_base(repo: Path):
    git(repo, "branch", "main")
    r = GitRepo(repo)
    assert r.branch_age_days("main") is None  # nothing on the branch yet
    (repo / "b.txt").write_text("b")
    git(repo, "add", "-A")
    env = {"GIT_AUTHOR_DATE": "2020-01-01T00:00:00", "GIT_COMMITTER_DATE": "2020-01-01T00:00:00"}
    subprocess.run(
        ["git", "commit", "-qm", "chore: old"],
        cwd=repo,
        env={
            **__import__("os").environ,
            **env,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
        },
        check=True,
    )
    assert r.branch_age_days("main") > 365 * 5
    assert r.branch_age_days("no-such-branch") is None


def test_stale_worktrees_lists_a_linked_worktree_whose_folder_is_gone(repo: Path, tmp_path: Path):
    wt = tmp_path.parent / (tmp_path.name + "-wt")
    git(repo, "worktree", "add", "-q", "-b", "feat/y", str(wt))
    r = GitRepo(repo)
    assert r.stale_worktrees() == []
    import shutil

    shutil.rmtree(wt)
    assert [Path(p).name for p in r.stale_worktrees()] == [wt.name]
