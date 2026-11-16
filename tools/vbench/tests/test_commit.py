"""`vbench commit` as a use case: the message it builds, and the cases where it refuses to commit."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.app.commit import make_commit, plan_commit
from vbench.domain.errors import AmbiguousError, RefusedError, UsageError

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "notes-app"
TEST_FILE = "tests/test_create_note.py"  # marks AC-N-001, AC-N-002 and AC-N-003: two tasks of UC-N-001
PROD = ["src/notes/create.py", "src/notes/note.py"]


class FakeRepo:
    def __init__(self, staged, branch="feat/uc-n-001-create-note", unstaged=()):
        self._staged, self._branch, self._unstaged = list(staged), branch, list(unstaged)
        self.committed: list[str] = []

    def branch(self):
        return self._branch

    def commits(self, base):
        return []

    def staged(self):
        return list(self._staged)

    def unstaged(self):
        return list(self._unstaged)

    behind_by: int | None = 0

    def branch_age_days(self, base):
        return None

    def stale_worktrees(self):
        return []

    def behind(self, base):
        return self.behind_by

    def commit_staged(self, message):
        self.committed.append(message)
        return "abc1234"


@pytest.fixture
def proj(tmp_path: Path) -> Path:
    root = tmp_path / "notes"
    shutil.copytree(EXAMPLE, root, ignore=shutil.ignore_patterns(".vbench/ui", "node_modules", ".git"))
    return root


def plan(proj: Path, repo: FakeRepo, **kw):
    kw.setdefault("summary", "Add the note rules")
    return plan_commit(load_config(proj), FsWorkspace(proj), repo, **kw)


def test_the_message_comes_from_the_branch_the_staged_task_and_the_summary(proj: Path):
    p = plan(proj, FakeRepo([TEST_FILE, *PROD]), task="TSK-N-002")
    assert p.message == "feat(UC-N-001/TSK-N-002): add the note rules\n\nCloses: AC-N-001"
    assert (p.type, p.uc, p.task, p.blockers) == ("feat", "UC-N-001", "TSK-N-002", [])
    assert load_config(proj).commit_re.match(p.message.splitlines()[0])


def test_a_commit_is_one_task_so_two_tasks_in_the_stage_is_ambiguous_not_guessed(proj: Path):
    with pytest.raises(AmbiguousError, match="TSK-N-001, TSK-N-002"):
        plan(proj, FakeRepo([TEST_FILE, *PROD]))


def test_the_use_case_is_found_from_tags_when_the_branch_does_not_say(proj: Path):
    p = plan(proj, FakeRepo([TEST_FILE, *PROD], branch="feat/notes"), task="TSK-N-002")
    assert p.uc == "UC-N-001"
    with pytest.raises(UsageError, match="use case"):
        plan(proj, FakeRepo(["README.md"], branch="feat/notes"), type_="docs")  # only chore may omit it


def test_nothing_staged_and_a_foreign_task_are_errors(proj: Path):
    with pytest.raises(UsageError, match="Nothing is staged"):
        plan(proj, FakeRepo([]))
    with pytest.raises(UsageError, match="not in UC-N-001's task table"):
        plan(proj, FakeRepo([TEST_FILE, *PROD]), task="TSK-N-099")


def test_unstaged_work_and_a_past_tense_summary_are_warned_about(proj: Path):
    p = plan(proj, FakeRepo([TEST_FILE, *PROD], unstaged=["notes.txt"]), task="TSK-N-002", summary="Added rules")
    assert any("not staged" in w and "notes.txt" in w for w in p.warnings)
    assert any("imperative" in w for w in p.warnings)


def test_a_branch_behind_the_default_branch_is_warned_about(proj: Path):
    repo = FakeRepo([TEST_FILE, *PROD])
    repo.behind_by = 3
    p = plan(proj, repo, task="TSK-N-002")
    assert any("3 commit(s) behind `main`" in w for w in p.warnings) and p.blockers == []
    repo.behind_by = None  # not knowing is not a warning
    assert not any("behind" in w for w in plan(proj, repo, task="TSK-N-002").warnings)


def test_a_task_whose_criterion_has_no_test_is_not_finished_and_is_refused(proj: Path):
    (proj / TEST_FILE).write_text((proj / TEST_FILE).read_text().replace('"AC-N-001"', '"AC-N-099"'))
    p = plan(proj, FakeRepo([TEST_FILE, *PROD]), task="TSK-N-002")
    assert any("TSK-N-002 is not finished" in b and "AC-N-001" in b for b in p.blockers)
    repo = FakeRepo([TEST_FILE, *PROD])
    with pytest.raises(RefusedError, match="not finished"):
        make_commit(load_config(proj), repo, repo, p, green=True)
    assert repo.committed == []


def test_a_gate_failing_for_another_use_case_is_a_warning_not_a_blocker(proj: Path):
    p = plan(proj, FakeRepo([TEST_FILE, *PROD]), task="TSK-N-002")  # UC-N-002 and UC-N-003 have untested criteria
    assert p.blockers == [] and any("elsewhere" in w and "acs" in w for w in p.warnings)


def test_a_failing_gate_blocks_a_code_commit_but_not_a_docs_one(proj: Path):
    (proj / "src/notes/orphan.py").write_text('"""Realises UC-N-099."""\n')  # a code tag with no spec
    stray = plan(proj, FakeRepo([TEST_FILE, *PROD]), task="TSK-N-002")  # the orphan is not part of this commit
    assert stray.blockers == []
    code = plan(proj, FakeRepo([TEST_FILE, *PROD, "src/notes/orphan.py"]), task="TSK-N-002")  # now it is
    assert any("gates fail for this work" in b for b in code.blockers)
    docs = plan(proj, FakeRepo(["docs/00-glossary.md"]), type_="docs", uc="UC-N-001", summary="Explain the glossary")
    assert docs.blockers == [] and docs.message == "docs(UC-N-001): explain the glossary"


def test_committing_needs_green_a_branch_and_an_unchanged_stage(proj: Path):
    cfg = load_config(proj)
    repo = FakeRepo([TEST_FILE, *PROD])
    p = plan(proj, repo, task="TSK-N-002")
    with pytest.raises(RefusedError, match="--green"):
        make_commit(cfg, repo, repo, p)
    repo._branch = "main"
    with pytest.raises(RefusedError, match="default branch"):
        make_commit(cfg, repo, repo, p, green=True)
    repo._branch = ""
    with pytest.raises(RefusedError, match="not on a branch"):
        make_commit(cfg, repo, repo, p, green=True)
    repo._branch = "feat/uc-n-001-create-note"
    repo._staged.append("src/notes/extra.py")
    with pytest.raises(RefusedError, match="changed since"):
        make_commit(cfg, repo, repo, p, green=True)
    repo._staged.pop()
    assert (
        make_commit(cfg, repo, repo, p, green=True) == "abc1234"
        and repo.committed[0].startswith(p.message)
        and "Tested:" in repo.committed[0]
    )


def test_a_docs_commit_needs_no_green_and_the_default_branch_can_be_allowed(proj: Path):
    cfg = load_config(proj)
    repo = FakeRepo(["docs/00-glossary.md"], branch="main")
    p = plan(proj, repo, type_="chore", summary="Tidy the glossary")
    assert p.message == "chore: tidy the glossary"
    assert make_commit(cfg, repo, repo, p, allow_default_branch=True) == "abc1234"


def test_every_generated_subject_passes_the_commit_gate(proj: Path):
    from vbench.domain.checks import check_commits

    cfg, ws = load_config(proj), FsWorkspace(proj)
    subjects = [
        plan(proj, FakeRepo([TEST_FILE, *PROD]), task="TSK-N-002").message.splitlines()[0],
        plan(proj, FakeRepo(["docs/00-glossary.md"]), type_="chore", summary="Tidy").message.splitlines()[0],
        plan(
            proj, FakeRepo([TEST_FILE]), task="TSK-N-001", type_="test", summary="Cover the limits"
        ).message.splitlines()[0],
    ]
    assert check_commits(cfg, ws, subjects, "feat/uc-n-001-create-note").ok


# ---------------------------------------------------------------------------------------- the command, end to end
def _sh(root: Path, *args: str) -> str:
    import os
    import subprocess

    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True, env=env).stdout


@pytest.fixture
def repo_proj(proj: Path, monkeypatch) -> Path:
    _sh(proj, "init", "-q", "-b", "main")
    _sh(proj, "add", "-A")
    _sh(proj, "commit", "-qm", "chore: start")
    _sh(proj, "checkout", "-qb", "feat/uc-n-001-create-note")
    # one finished task: a test file that marks only AC-N-001 (TSK-N-002), and the code it drove
    (proj / "tests/test_create_note.py").write_text(
        (proj / "tests/test_create_note.py")
        .read_text()
        .replace('"AC-N-002"', '"AC-N-001"')
        .replace('"AC-N-003"', '"AC-N-001"')
    )
    monkeypatch.chdir(proj)
    return proj


def test_the_command_commits_only_what_is_staged_with_a_message_the_gate_accepts(repo_proj: Path, capsys):
    from vbench import cli

    _sh(repo_proj, "add", TEST_FILE)
    (repo_proj / "src/notes/note.py").write_text((repo_proj / "src/notes/note.py").read_text() + "\n# tweak\n")
    assert cli.main(["commit", "-m", "Add the note rules", "--dry-run", "--json", "--task", "TSK-N-002"]) == 0
    dry = __import__("json").loads(capsys.readouterr().out)
    assert dry["committed"] is None and dry["message"].startswith("test(UC-N-001/TSK-N-002): add the note rules")
    assert cli.main(["commit", "-m", "Add the note rules", "--task", "TSK-N-002"]) == 0
    assert _sh(repo_proj, "log", "-1", "--format=%s").strip() == "test(UC-N-001/TSK-N-002): add the note rules"
    assert "note.py" in _sh(repo_proj, "status", "--short")  # the unstaged edit was left alone
    assert cli.main(["check", "commits"]) == 0


def test_a_code_commit_without_green_is_refused_with_exit_1_and_ambiguity_exits_2(repo_proj: Path, capsys):
    from vbench import cli

    config = repo_proj / ".vbench/config.toml"
    config.write_text(config.read_text().replace('test = "pytest"', 'test = ""'))  # no test command: the flag is needed
    (repo_proj / "src/notes/note.py").write_text((repo_proj / "src/notes/note.py").read_text() + "\n# done\n")
    _sh(repo_proj, "add", TEST_FILE, "src/notes/note.py")
    assert cli.main(["commit", "-m", "Add the note rules", "--task", "TSK-N-002"]) == 1
    assert "--green" in capsys.readouterr().err
    assert cli.main(["commit", "-m", "Add the note rules", "--task", "TSK-N-002", "--green"]) == 0
    assert "reported green by the committer (vbench did not run it)" in _sh(repo_proj, "log", "-1", "--format=%B")
    assert _sh(repo_proj, "log", "-1", "--format=%s").startswith("feat(UC-N-001/TSK-N-002):")
    (repo_proj / "tests/test_create_note.py").write_text(
        (repo_proj / "tests/test_create_note.py").read_text()
        + '\n@pytest.mark.ac("AC-N-002")\ndef test_x():\n    assert str(1) == "1"\n'
    )
    _sh(repo_proj, "add", "-A")
    assert cli.main(["commit", "-m", "Both", "--dry-run"]) == 2  # two tasks: ambiguous, not guessed
    assert "more than one task" in capsys.readouterr().err


def test_message_only_and_the_default_branch(repo_proj: Path, capsys):
    from vbench import cli

    _sh(repo_proj, "add", TEST_FILE)
    assert cli.main(["commit", "-m", "Cover it.", "--message-only", "-t", "chore"]) == 0
    assert capsys.readouterr().out.strip() == "chore(UC-N-001): cover it"  # the branch names the use case
    _sh(repo_proj, "checkout", "-q", "main")
    assert cli.main(["commit", "-m", "Cover it", "-t", "chore"]) == 1
    assert "default branch" in capsys.readouterr().err


class FakeRunner:
    def __init__(self, code: int, tail: str = "") -> None:
        self.code, self.tail, self.ran = code, tail, []

    def run(self, command):
        from vbench.ports import RunResult

        self.ran.append(command)
        return RunResult(self.code, self.tail)


def _stage_a_code_commit(repo_proj: Path) -> None:
    (repo_proj / "src/notes/note.py").write_text((repo_proj / "src/notes/note.py").read_text() + "\n# done\n")
    _sh(repo_proj, "add", TEST_FILE, "src/notes/note.py")


def test_vbench_runs_the_test_command_and_a_failing_run_stops_the_commit(repo_proj: Path, capsys):
    from vbench import cli

    _stage_a_code_commit(repo_proj)
    failing = FakeRunner(1, "FAILED tests/test_x.py::test_y - assert 1 == 2")
    argv = ["commit", "-m", "Add the note rules", "--task", "TSK-N-002", "--green"]  # --green cannot override a red run
    assert cli.main(argv, cli.Adapters(runner_for=lambda root: failing)) == 1
    assert failing.ran == ["pytest"] and "FAILED tests/test_x.py::test_y" in capsys.readouterr().err
    assert _sh(repo_proj, "log", "-1", "--format=%s").strip() == "chore: start"  # nothing was committed


def test_a_passing_run_commits_without_the_flag_and_records_the_evidence(repo_proj: Path):
    from vbench import cli

    _stage_a_code_commit(repo_proj)
    passing = FakeRunner(0)
    assert (
        cli.main(
            ["commit", "-m", "Add the note rules", "--task", "TSK-N-002"], cli.Adapters(runner_for=lambda r: passing)
        )
        == 0
    )
    body = _sh(repo_proj, "log", "-1", "--format=%B")
    assert "Closes: AC-N-001" in body and "Tested: `pytest` passed (run by vbench)" in body
    assert cli.main(["check", "commits"]) == 0


def test_a_docs_commit_does_not_run_the_tests(repo_proj: Path):
    from vbench import cli

    (repo_proj / "docs/00-glossary.md").write_text((repo_proj / "docs/00-glossary.md").read_text() + "\n")
    _sh(repo_proj, "add", "docs/00-glossary.md")
    runner = FakeRunner(1)
    argv = ["commit", "-m", "Tidy the glossary", "-t", "chore"]
    assert cli.main(argv, cli.Adapters(runner_for=lambda r: runner)) == 0 and runner.ran == []


def test_the_shell_runner_reports_exit_codes_and_a_command_that_cannot_start(tmp_path: Path):
    import sys

    from vbench.adapters.shell import ShellRunner

    r = ShellRunner(tmp_path)
    assert r.run(f'{sys.executable} -c "print(1)"').code == 0
    bad = r.run(f"{sys.executable} -c \"import sys; print('boom'); sys.exit(3)\"")
    assert bad.code == 3 and "boom" in bad.tail
    missing = r.run("no-such-binary-xyz --flag")
    assert missing.code == 127 and "could not start" in missing.tail
