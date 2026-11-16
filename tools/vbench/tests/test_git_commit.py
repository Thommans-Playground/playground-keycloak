"""The git adapter commits exactly the files it is given, whatever else is staged."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from vbench.adapters.git import GitRepo
from vbench.domain.errors import UsageError


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "feat/x")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "T")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/a.md").write_text("a\n")
    (tmp_path / "other.txt").write_text("o\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "chore: start")
    return tmp_path


def test_it_commits_only_the_named_paths(repo: Path):
    (repo / "docs/a.md").write_text("changed\n")
    (repo / "other.txt").write_text("also changed\n")
    git(repo, "add", "other.txt")  # staged by someone else, and not ours to commit
    short = GitRepo(repo).commit(["docs/a.md"], "chore: update a")
    assert short == git(repo, "rev-parse", "--short", "HEAD")
    assert git(repo, "show", "--name-only", "--format=%s", "HEAD").split("\n") == ["chore: update a", "", "docs/a.md"]
    assert git(repo, "status", "--short") == "M  other.txt"


def test_a_new_file_is_added_and_committed(repo: Path):
    (repo / "docs/b.md").write_text("b\n")
    GitRepo(repo).commit(["docs/b.md"], "chore: add b")
    assert "docs/b.md" in git(repo, "show", "--name-only", "--format=", "HEAD")


def test_git_refusing_is_reported_not_swallowed(repo: Path):
    with pytest.raises(UsageError, match="git"):
        GitRepo(repo).commit(["docs/missing.md"], "chore: nothing")
