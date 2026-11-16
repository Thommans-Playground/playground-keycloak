"""`vbench doctor`: drift found from facts, with a fix named for each."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vbench import cli
from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.app.doctor import diagnose


class FakeRepo:
    def __init__(self, branch="feat/x", behind=0, stale=(), unstaged=()):
        self._b, self._behind, self._stale, self._unstaged = branch, behind, list(stale), list(unstaged)

    def branch(self):
        return self._b

    def behind(self, base):
        return self._behind

    age = None

    def branch_age_days(self, base):
        return self.age

    def stale_worktrees(self):
        return list(self._stale)

    def unstaged(self):
        return list(self._unstaged)

    def staged(self):
        return []

    def commits(self, base):
        return []


@pytest.fixture
def proj(tmp_path: Path, monkeypatch) -> Path:
    root = tmp_path / "fresh"
    root.mkdir()
    monkeypatch.chdir(root)
    assert cli.main(["init", "--stack", "none"]) == 0
    return root


def run(proj: Path, repo: FakeRepo):
    return diagnose(load_config(proj), FsWorkspace(proj), repo)


def test_a_clean_working_copy_has_nothing_to_report(proj: Path):
    assert run(proj, FakeRepo()) == []


def test_a_stale_branch_a_dead_worktree_and_a_detached_head_are_problems_with_a_fix(proj: Path):
    found = run(proj, FakeRepo(behind=4, stale=["/tmp/wt"]))
    texts = [f.text for f in found]
    assert any("4 commit(s) behind" in t for t in texts) and any("/tmp/wt" in t for t in texts)
    assert all(f.level == "problem" and f.fix for f in found)
    assert any("detached" in f.text for f in run(proj, FakeRepo(branch="")))


def test_unstaged_files_and_an_unknown_base_are_notes_not_problems(proj: Path):
    found = run(proj, FakeRepo(behind=None, unstaged=["a.py"]))
    assert {f.level for f in found} == {"note"}


def test_the_command_exits_one_on_a_problem_and_prints_json(proj: Path, monkeypatch, capsys):
    monkeypatch.chdir(proj)
    bad = cli.Adapters(repo_for=lambda root: FakeRepo(behind=2))
    assert cli.main(["doctor", "--json"], bad) == 1
    assert json.loads(capsys.readouterr().out)[0]["level"] == "problem"
    assert cli.main(["doctor"], cli.Adapters(repo_for=lambda root: FakeRepo())) == 0
    assert "nothing has drifted" in capsys.readouterr().out


def test_a_branch_older_than_the_limit_or_badly_named_is_a_note(proj: Path):
    old = FakeRepo()
    old.age = 9
    assert any("9 days old" in f.text and f.level == "note" for f in run(proj, old))
    young = FakeRepo()
    young.age = 2
    assert run(proj, young) == []
    assert any("does not follow" in f.text for f in run(proj, FakeRepo(branch="my-stuff")))
    assert not any("does not follow" in f.text for f in run(proj, FakeRepo(branch="release/1.2")))
