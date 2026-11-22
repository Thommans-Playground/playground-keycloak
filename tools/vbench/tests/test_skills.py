"""The plugin's skills as artifacts: well-formed, fully linked, and their scripts do what they say."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parent.parent / "plugin" / "skills"
NAMES = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
MAX_LINES = 150  # SKILL.md is the workflow; depth goes in references/
LINK = re.compile(r"(?<![\w-]/)(?:references|scripts)/[\w./-]+")  # not ../<other-skill>/scripts/…


def frontmatter(skill: str) -> tuple[dict[str, str], str]:
    text = (SKILLS / skill / "SKILL.md").read_text()
    head, body = text.split("---\n", 2)[1:]
    return dict(line.split(": ", 1) for line in head.strip().splitlines() if ": " in line), body


@pytest.mark.parametrize("skill", NAMES)
def test_frontmatter_is_valid(skill: str):
    meta, body = frontmatter(skill)
    assert meta["name"] == skill and re.fullmatch(r"[a-z0-9-]+", skill)
    assert 20 <= len(meta["description"]) <= 1024
    assert len((SKILLS / skill / "SKILL.md").read_text().splitlines()) <= MAX_LINES
    assert body.lstrip().startswith("#")


@pytest.mark.parametrize("skill", NAMES)
def test_every_linked_file_exists_and_every_file_is_linked(skill: str):
    text = (SKILLS / skill / "SKILL.md").read_text()
    linked = {m.rstrip(".,;:)`") for m in LINK.findall(text)}
    for rel in linked:
        assert (SKILLS / skill / rel).is_file(), f"{skill}: links {rel} which does not exist"
    for sub in ("references", "scripts"):
        for f in (SKILLS / skill / sub).glob("*") if (SKILLS / skill / sub).is_dir() else []:
            assert f"{sub}/{f.name}" in linked, f"{skill}: {sub}/{f.name} is not mentioned in SKILL.md"


def test_cross_skill_script_paths_resolve():
    for skill in NAMES:
        for rel in re.findall(
            r"\.\./([\w-]+/(?:scripts|references)/[\w.-]+)", (SKILLS / skill / "SKILL.md").read_text()
        ):
            assert (SKILLS / rel).is_file(), f"{skill}: ../{rel} does not exist"


@pytest.mark.parametrize(
    "script", sorted(SKILLS.glob("*/scripts/*.py")), ids=lambda p: f"{p.parent.parent.name}/{p.name}"
)
def test_scripts_are_executable_and_document_themselves(script: Path):
    assert os.access(script, os.X_OK)
    r = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert r.returncode == 0 and "usage:" in r.stdout


# --------------------------------------------------------------------------- behaviour
@pytest.fixture
def env(monkeypatch) -> dict[str, str]:
    """`vbench` from this checkout on PATH, like an installed tool."""
    return {**os.environ, "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}"}


@pytest.fixture
def repo(tmp_path: Path, env) -> Path:
    def sh(*cmd: str) -> None:
        subprocess.run(cmd, cwd=tmp_path, env=env, check=True, capture_output=True)

    sh("git", "init", "-q", "-b", "main")
    sh("vbench", "init", "--ci", "none", "--stack", "none")
    cfg = tmp_path / ".vbench/config.toml"
    cfg.write_text(
        cfg.read_text()
        .replace('test = "pytest"', 'test = "python -c \\"print(1)\\""')
        .replace('lint = "ruff check ."', 'lint = "python -c \\"import sys; print(\'bad style\'); sys.exit(1)\\""')
        .replace('types = "mypy ."', 'types = ""')
    )
    sh("vbench", "new", "uc", "--area", "A", "--title", "Log in")
    sh("git", "add", "-A")
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "chore: scaffold")
    sh("git", "checkout", "-qb", "feat/uc-a1-login")
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src/login.py").write_text('"""Realises UC-A-001"""\n')
    sh("git", "add", "-A")
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "docs(UC-A-001): start")
    return tmp_path


def script(skill: str, name: str, *args: str, cwd: Path, env) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILLS / skill / "scripts" / name), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )


def test_run_gates_reports_each_gate_and_fails_on_a_failing_one(repo: Path, env):
    r = script("v-3-code", "run_gates.py", cwd=repo, env=env)
    assert r.returncode == 1
    assert "| test | PASS |" in r.stdout and "| lint | FAIL |" in r.stdout
    assert "| types | skipped |" in r.stdout and "bad style" in r.stdout


def test_run_gates_only_selects_and_rejects_unknown(repo: Path, env):
    assert script("v-3-code", "run_gates.py", "--only", "test", cwd=repo, env=env).returncode == 0
    r = script("v-3-code", "run_gates.py", "--only", "nope", cwd=repo, env=env)
    assert r.returncode != 0 and "unknown gate" in r.stderr


def test_run_gates_without_a_project_says_what_to_do(tmp_path: Path, env):
    r = script("v-3-code", "run_gates.py", cwd=tmp_path, env=env)
    assert r.returncode != 0 and "vbench init" in r.stderr


def test_branch_ucs_finds_use_cases_from_files_tags_and_commits(repo: Path, env):
    r = script("v-4-verify", "branch_ucs.py", "--json", cwd=repo, env=env)
    assert r.returncode == 0
    ucs = json.loads(r.stdout)["ucs"]
    assert list(ucs) == ["UC-A-001"] and {"tag", "commit `docs(UC-A-001): start`"} <= set(ucs["UC-A-001"])


def test_branch_ucs_on_the_base_branch_is_empty(repo: Path, env):
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    assert "No use cases touched" in script("v-4-verify", "branch_ucs.py", cwd=repo, env=env).stdout


def test_pr_draft_builds_the_traceability_row(repo: Path, env):
    out = script("v-5-ship", "pr_draft.py", cwd=repo, env=env).stdout
    assert "| UC-A-001 | 0/1 | 0/1 | src/login.py | **OPEN: no test** |" in out


def test_snapshot_combines_status_git_and_commit_check(repo: Path, env):
    out = script("v-status", "snapshot.py", cwd=repo, env=env).stdout
    for part in (
        "## vbench status",
        "UC-A-001",
        "branch: feat/uc-a1-login",
        "commits ahead of",
        "commit convention",
        "commits: 1 commit(s) and the branch follow the convention.",
    ):
        assert part in out, part


def fake_plantuml(tmp_path: Path, env) -> dict[str, str]:
    """A `plantuml` that writes `<name>.svg` into the -o folder, like the real one."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    exe = bin_dir / "plantuml"
    exe.write_text(
        "#!/bin/sh\nout=\nfmt=svg\nwhile [ $# -gt 0 ]; do case $1 in -o) out=$2; shift;; -t*) fmt=${1#-t};; "
        '*.puml) n=$(basename $1 .puml); echo x > "$out/$n.$fmt";; esac; shift; done\n'
    )
    exe.chmod(0o755)
    return {**env, "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}"}


def test_render_diagrams_renders_diagrams_but_not_includes(repo: Path, tmp_path: Path, env):
    d = repo / "docs/usecase-diagrams"
    (d / "UC-A-001-log-in-sequence.puml").write_text("@startuml X\n@enduml\n")
    r = script("v-2-design", "render_diagrams.py", cwd=repo, env=fake_plantuml(tmp_path, env))
    assert r.returncode == 0 and "Rendered 2 diagram(s) to docs/diagrams" in r.stdout
    assert sorted(p.name for p in (repo / "docs/diagrams").iterdir()) == [
        "08-usecase-diagrams.svg",
        "UC-A-001-log-in-sequence.svg",
    ]
    png = (
        script("v-2-design", "render_diagrams.py", "--format", "png", cwd=repo, env=fake_plantuml(tmp_path / "p", env))
        if (tmp_path / "p").mkdir() is None
        else None
    )
    assert png.returncode == 0 and (repo / "docs/diagrams/UC-A-001-log-in-sequence.png").is_file()


def test_render_diagrams_without_plantuml_says_how_to_get_it(repo: Path, env):
    (repo / "docs/usecase-diagrams/UC-A-001-log-in-class.puml").write_text("@startuml X\n@enduml\n")
    bare = {**env, "PATH": str(Path(sys.executable).parent) + os.pathsep + "/usr/bin" + os.pathsep + "/bin"}
    r = script("v-2-design", "render_diagrams.py", cwd=repo, env=bare)
    assert r.returncode == 3 and "plantuml" in r.stderr and "still validates" in r.stderr


def test_every_skill_says_why_the_step_exists():
    for skill in NAMES:
        _, body = frontmatter(skill)
        assert "**Why this step:**" in body, f"{skill} has no one-line reason for the step"


def test_discovery_replaced_grill_and_owns_the_shared_interview_technique():
    assert "grill" not in NAMES and "discovery" in NAMES
    assert (SKILLS / "discovery/references/interview-technique.md").is_file()
    root = Path(__file__).resolve().parent.parent
    leftovers = [
        str(p.relative_to(root))
        for base in ("plugin", "src", "README.md", "CLAUDE.md")
        for p in ([root / base] if (root / base).is_file() else (root / base).rglob("*"))
        if p.is_file()
        and p.suffix in {".md", ".py", ".tsx", ".ts", ".toml", ".yml", ".json"}
        and "grill" in p.read_text(errors="ignore").lower()
    ]
    assert leftovers == []


def test_help_lists_every_skill():
    text = (SKILLS / "help" / "SKILL.md").read_text()
    for (
        name
    ) in NAMES:  # the commands a person types; requirements-engineering is a background skill Claude loads itself
        if name != "help" and frontmatter(name)[0].get("disable-model-invocation") == "true":
            assert f"/vbench:{name}" in text, f"/vbench:help does not list {name}"


def test_every_agent_names_a_model_and_a_reviewer_cannot_write():
    agents = sorted((Path(__file__).resolve().parent.parent / "plugin" / "agents").glob("*.md"))
    assert {a.stem for a in agents} >= {"vbench-trace-checker", "vbench-uc-scaffolder", "vbench-spec-challenger"}
    for a in agents:
        head = a.read_text().split("---")[1]
        fields = dict(line.split(": ", 1) for line in head.strip().splitlines() if ": " in line)
        assert fields["name"] == a.stem and fields["description"] and fields["model"] in {"haiku", "sonnet", "opus"}
        if a.stem in {"vbench-trace-checker", "vbench-spec-challenger"}:
            assert not {"Write", "Edit"} & set(fields["tools"].replace(" ", "").split(",")), a.stem


def test_design_cuts_tasks_as_slices_through_the_sequence_steps():
    plugin = SKILLS.parent
    design = (plugin / "skills/v-2-design/SKILL.md").read_text().lower()
    challenger = (plugin / "agents/vbench-spec-challenger.md").read_text().lower()
    assert "thin slice" in design and "step" in design and "slice" in challenger and "step" in challenger


def test_code_pauses_for_review_after_each_red_green_and_refactor_of_a_step():
    code = (SKILLS / "v-3-code/SKILL.md").read_text().lower()
    assert "stop for review at each step" in code
    for stage in ("after red", "after green", "after refactor"):
        assert stage in code
    assert "run to the end of the task" in code  # the person can drop the pauses


RUNS = re.compile(
    r"\bRun `/vbench:([\w-]+)"
)  # an order to Claude; "run `/vbench:next`" in a hand-over is for the person


@pytest.mark.parametrize("skill", NAMES)
def test_a_skill_never_tells_claude_to_run_one_only_the_user_may_invoke(skill: str):
    """`disable-model-invocation: true` keeps a skill out of Claude's hands, so an instruction to *run* it cannot be
    followed. The way to reuse its workflow is the one the short forms use: read its SKILL.md and follow it."""
    _, body = frontmatter(skill)
    for target in RUNS.findall(body):
        if target in NAMES:
            meta, _ = frontmatter(target)
            assert meta.get("disable-model-invocation") != "true", (
                f"{skill} says to run /vbench:{target}, which only the user can invoke: "
                f"say `Read ../{target}/SKILL.md and follow it` instead"
            )
