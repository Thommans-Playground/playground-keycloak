"""Verifies the vbench harness itself: init, the three gates, id allocation and status."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from vbench import __version__, cli
from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import find_root, load_config
from vbench.domain.checks import (
    check_acs,
    check_commits,
    check_diagrams,
    check_docs,
    check_links,
    check_refs,
    check_rungs,
)
from vbench.domain.errors import ConfigError
from vbench.ports import Origin


def ctx(proj: Path):
    """The (config, workspace) pair the checks take, read from the project on disk."""
    return load_config(proj), FsWorkspace(proj)


def write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text), encoding="utf-8")


def spec(proj: Path, uc: str, acs: list[str], planned: tuple[str, ...] = ()) -> None:
    rows = "\n".join(
        f"| **{a}** | Given x, when y, then z.{' (planned)' if a in planned else ''} | REQ-FR-001 |" for a in acs
    )
    write(
        proj / f"docs/usecase-diagrams/{uc}-thing.md",
        f"# {uc}\n\n## Acceptance criteria\n\n| AC id | Given / when / then | Satisfies |\n|---|---|---|\n{rows}\n",
    )


def test_init_is_idempotent_and_does_not_overwrite(proj: Path, capsys):
    cfg = proj / ".vbench/config.toml"
    cfg.write_text(cfg.read_text() + "\n# local edit\n")
    assert cli.main(["init", "--ci", "none"]) == 0
    assert "# local edit" in cfg.read_text()
    assert "kept" in capsys.readouterr().out


def test_init_writes_ci_for_both_hosts(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cli.main(["init", "--ci", "both"])
    assert (tmp_path / ".github/workflows/vbench.yml").is_file()
    assert (tmp_path / ".gitlab-ci.vbench.yml").is_file()


def test_missing_config_is_a_clear_error(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["check"]) == 2
    assert "vbench init" in capsys.readouterr().err
    with pytest.raises(ConfigError):
        find_root(tmp_path)


def test_fresh_project_passes_all_gates(proj: Path):
    assert cli.main(["check"]) == 0


def test_refs_flags_a_broken_link_and_a_code_spec_ref(proj: Path):
    write(proj / "docs/a.md", "see [x](missing.md) and `docs/gone.md`\n")
    write(proj / "src/app.py", '"""Realises UC-A-001 · Spec: docs/nope.md"""\n')
    res = check_refs(*ctx(proj))
    assert not res.ok
    text = res.render()
    assert "broken link -> missing.md" in text
    assert "inline path not found -> docs/gone.md" in text
    assert "Spec ref not found -> docs/nope.md" in text


def test_rung_open_then_closed(proj: Path):
    write(
        proj / "src/auth.py",
        '"""Realises UC-A-001 · Spec: docs/usecase-diagrams/UC-A-001-thing.md"""\n',
    )
    spec(proj, "UC-A-001", ["AC-A-003"])
    ctx_ = ctx(proj)
    res = check_rungs(*ctx_)
    assert not res.ok and "UC-A-001" in res.render()
    write(
        proj / "tests/test_auth.py",
        '"""Verifies UC-A-001 · unit rung."""\ndef test_x():\n    assert str(1) == "1"\n',
    )
    assert check_rungs(*ctx_).ok


def test_rung_ids_sort_naturally_in_matrix(proj: Path):
    for n in (10, 2):
        write(proj / f"src/m{n}.py", f'"""Realises UC-A-{n:03d}"""\n')
    lines = check_rungs(*ctx(proj), matrix=True).lines
    ids = [ln.split("|")[1].strip() for ln in lines[2:]]
    assert ids == ["UC-A-002", "UC-A-010"]


def test_ac_uncovered_orphan_and_planned(proj: Path):
    spec(proj, "UC-A-001", ["AC-A-003", "AC-A-004"], planned=("AC-A-004",))
    res = check_acs(*ctx(proj))
    assert not res.ok and "UNCOVERED AC-A-003" in res.render()
    assert "AC-A-004" not in res.render()  # planned: not enforced

    write(
        proj / "tests/test_a.py",
        'import pytest\n@pytest.mark.ac("AC-A-003", "AC-A-005")\ndef test_x():\n    assert str(1) == "1"\n',
    )
    res = check_acs(*ctx(proj))
    assert not res.ok and "ORPHAN AC-A-005" in res.render()
    assert "UNCOVERED" not in res.render()

    write(
        proj / "tests/test_a.py",
        'import pytest\n@pytest.mark.ac("AC-A-003")\ndef test_x():\n    assert str(1) == "1"\n',
    )
    assert check_acs(*ctx(proj)).ok


def test_custom_id_pattern_and_marker(proj: Path):
    cfgfile = proj / ".vbench/config.toml"
    cfgfile.write_text(
        cfgfile.read_text()
        .replace("'''UC-[A-Z]-\\d{3}'''", "'''US-\\d+'''")
        .replace("'''AC-[A-Z]-\\d{3}'''", "'''AC-\\d+'''")
        .replace('ac_marker = "pytest.mark.ac"', 'ac_marker = "acceptance"')
    )
    write(
        proj / "docs/usecase-diagrams/US-1-x.md",
        "| **AC-7** | Given a, when b, then c. | REQ-FR-001 |\n",
    )
    assert not check_acs(*ctx(proj)).ok
    write(proj / "tests/test_x.py", '@acceptance("AC-7")\ndef test_x():\n    assert str(1) == "1"\n')
    assert check_acs(*ctx(proj)).ok


def test_new_uc_allocates_next_free_number_and_never_reuses(proj: Path, capsys):
    assert cli.main(["new", "uc", "--area", "A", "--title", "Log in"]) == 0
    assert (proj / "docs/usecase-diagrams/UC-A-001-log-in.md").is_file()
    # A retired spec must not free its number: code still mentions UC-A-002.
    write(proj / "src/old.py", '"""Realises UC-A-002"""\n')
    assert cli.main(["new", "uc", "--area", "A", "--title", "Log out"]) == 0
    assert (proj / "docs/usecase-diagrams/UC-A-003-log-out.md").is_file()
    body = (proj / "docs/usecase-diagrams/UC-A-003-log-out.md").read_text()
    # the scaffold takes the next free criterion and task numbers too, never ones another spec already uses
    assert "UC-A-003" in body and "UC-X-nnn" not in body and "AC-X-nnn" not in body and "TSK-X-nnn" not in body
    assert "**AC-A-002**" in body and "**TSK-A-002**" in body


def test_new_uc_rejects_bad_area(proj: Path):
    assert cli.main(["new", "uc", "--area", "AB", "--title", "x"]) == 2


def test_status_reports_next_step(proj: Path, capsys):
    cli.main(["new", "uc", "--area", "A", "--title", "Log in"])
    capsys.readouterr()
    assert cli.main(["status"]) == 0
    out = capsys.readouterr().out
    assert "UC-A-001" in out and "gates:" in out


def test_release_versions_agree():
    import json
    import tomllib

    from vbench import __version__

    root = Path(__file__).resolve().parent.parent
    assert tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"] == __version__
    assert json.loads((root / "plugin/.claude-plugin/plugin.json").read_text())["version"] == __version__
    market = json.loads((root / ".claude-plugin/marketplace.json").read_text())
    assert market["plugins"][0]["version"] == __version__


GIT = Origin("https://example.com/org/vbench.git", is_git=True)


class FakeInfo:
    def __init__(self, origin: Origin | None = GIT) -> None:
        self._origin = origin

    def origin(self) -> Origin | None:
        return self._origin


class FakeReleases:
    def __init__(self, *tags: str) -> None:
        self._tags = list(tags)

    def tags(self, url: str) -> list[str]:
        return self._tags


class FakeInstaller:
    def __init__(self, available: bool = True) -> None:
        self.ok, self.installed = available, []

    def available(self) -> bool:
        return self.ok

    def install(self, source: str) -> None:
        self.installed.append(source)


def fakes(**kw) -> cli.Adapters:
    return cli.Adapters(
        **{
            "install_info": FakeInfo(),
            "releases": FakeReleases(),
            "installer": FakeInstaller(),
            **kw,
        }
    )


def test_init_pins_version_and_renders_ci_and_plugin_settings(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"], fakes()) == 0
    assert f'vbench_version = "{__version__}"' in (tmp_path / ".vbench/config.toml").read_text()
    ci = (tmp_path / ".github/workflows/vbench.yml").read_text()
    assert f"git+https://example.com/org/vbench.git@v{__version__}" in ci and "{{VBENCH" not in ci
    settings = json.loads((tmp_path / ".claude/settings.json").read_text())
    assert settings["enabledPlugins"] == {"vbench@vbench": True}
    assert settings["extraKnownMarketplaces"]["vbench"]["source"]["url"] == "https://example.com/org/vbench.git"


def test_init_without_a_git_install_leaves_placeholders_and_skips_plugin_settings(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init"], fakes(install_info=FakeInfo(None))) == 0
    assert "<host>/<org>" in (tmp_path / ".github/workflows/vbench.yml").read_text()
    settings = json.loads((tmp_path / ".claude/settings.json").read_text())
    assert "enabledPlugins" not in settings and "extraKnownMarketplaces" not in settings
    assert "Bash(vbench check:*)" in settings["permissions"]["allow"]


def test_init_keeps_existing_claude_settings(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/settings.json").write_text('{"permissions": {"allow": ["Bash(ls)"]}}')
    assert cli.main(["init", "--ci", "none"], fakes()) == 0
    settings = json.loads((tmp_path / ".claude/settings.json").read_text())
    assert (
        settings["permissions"]["allow"][0] == "Bash(ls)"
        and "Bash(vbench status:*)" in settings["permissions"]["allow"]
    )
    assert "vbench@vbench" in settings["enabledPlugins"]


def test_version_mismatch_warns_but_does_not_fail(proj: Path, capsys):
    cfg = proj / ".vbench/config.toml"
    cfg.write_text(cfg.read_text().replace('vbench_version = "', 'vbench_version = "9.'))
    assert cli.main(["check"]) == 0
    assert "pinned to 9." in capsys.readouterr().err


def test_update_picks_highest_semver_tag_and_installs(capsys):
    inst = FakeInstaller()
    ad = fakes(releases=FakeReleases("v0.2.0", "v0.10.0", "junk"), installer=inst)
    assert cli.main(["update", "--check"], ad) == 0
    assert f"{__version__} -> v0.10.0" in capsys.readouterr().out and not inst.installed
    assert cli.main(["update"], ad) == 0
    assert inst.installed == ["git+https://example.com/org/vbench.git@v0.10.0"]


def test_update_reports_up_to_date_and_honours_to(capsys):
    inst = FakeInstaller()
    ad = fakes(releases=FakeReleases(f"v{__version__}"), installer=inst)
    assert cli.main(["update"], ad) == 0
    assert "up to date" in capsys.readouterr().out and not inst.installed
    assert cli.main(["update", "--to", "v0.0.1"], ad) == 0
    assert inst.installed == ["git+https://example.com/org/vbench.git@v0.0.1"]


def test_update_errors_are_clear(capsys):
    assert cli.main(["update"], fakes(install_info=FakeInfo(None))) == 2
    assert "not installed from a Git URL" in capsys.readouterr().err
    assert cli.main(["update"], fakes(releases=FakeReleases("junk"))) == 2
    assert "no release tags" in capsys.readouterr().err
    assert (
        cli.main(
            ["update"],
            fakes(releases=FakeReleases("v9.0.0"), installer=FakeInstaller(False)),
        )
        == 2
    )
    assert "uv not found" in capsys.readouterr().err


class FakeRepo:
    def __init__(self, subjects: list[str], branch: str = "feat/uc-a-001-login") -> None:
        self.subjects, self._branch = subjects, branch

    def branch(self) -> str:
        return self._branch

    def commits(self, base: str) -> list[str]:
        return self.subjects


def task_spec(proj: Path) -> None:
    write(
        proj / "docs/usecase-diagrams/UC-A-001-login.md",
        """\
        # UC-A-001

        | AC id | Given / when / then | Satisfies |
        |---|---|---|
        | **AC-A-003** | Given x, when y, then z. | REQ-FR-001 |

        | Task id | Description | Closes ACs |
        |---|---|---|
        | **TSK-A-001** | login | AC-A-003 |
        """,
    )


def test_commit_convention_accepts_good_subjects_and_skips_merges(proj: Path):
    task_spec(proj)
    good = [
        "feat(UC-A-001/TSK-A-001): add login",
        "docs(UC-A-001): approve spec",
        "chore: bump ci",
        "Merge pull request #4 from x/y",
        'Revert "feat(UC-A-001/TSK-A-001): add login"',
    ]
    assert check_commits(*ctx(proj), good, "feat/uc-a-001-login").ok


@pytest.mark.parametrize(
    "subject, why",
    [
        ("fix the login", "does not match"),
        ("feat-TSK-A-001: x", "does not match"),
        ("feat: add login", "only chore may omit"),
        ("feat(UC-A-009/TSK-A-001): x", "no spec for UC-A-009"),
        ("feat(UC-A-001/TSK-A-007): x", "task table"),
        ("feat(UC-A-001/TSK-A-001):  ", "does not match"),
    ],
)
def test_commit_convention_rejects(proj: Path, subject: str, why: str):
    task_spec(proj)
    res = check_commits(*ctx(proj), [subject])
    assert not res.ok and why in res.render()


def test_branch_name_convention(proj: Path):
    task_spec(proj)
    for ok in ("main", "feat/uc-a-001-login", "release/0.4.x", "chore/bump-deps", ""):
        assert check_commits(*ctx(proj), [], ok).ok, ok
    for bad in ("feature/UC-A-001", "login", "feat/"):
        assert not check_commits(*ctx(proj), [], bad).ok, bad


def test_check_commits_command_uses_the_repo_and_exits_nonzero(proj: Path, capsys):
    task_spec(proj)
    ok = cli.Adapters(repo_for=lambda root: FakeRepo(["feat(UC-A-001/TSK-A-001): add login"]))
    assert cli.main(["check", "commits"], ok) == 0
    bad = cli.Adapters(repo_for=lambda root: FakeRepo(["oops"]))
    assert cli.main(["check", "commits"], bad) == 1
    assert "does not match" in capsys.readouterr().out
    assert cli.main(["check", "commits", "--matrix"], ok) == 2


def test_commit_patterns_are_configurable(proj: Path):
    task_spec(proj)
    cfg = proj / ".vbench/config.toml"
    cfg.write_text(
        cfg.read_text().replace(
            'commit_types = ["feat", "fix", "docs", "refactor", "perf", "test", "build", "ci", "chore"]',
            'commit_types = ["feature", "chore"]',
        )
    )
    assert check_commits(*ctx(proj), ["feature(UC-A-001): x"]).ok
    assert not check_commits(*ctx(proj), ["feat(UC-A-001): x"]).ok
    cfg.write_text(cfg.read_text().replace('["feature", "chore"]', '["FEATURE", "CHORE"]'))  # older configs shouted
    assert check_commits(*ctx(proj), ["feature(UC-A-001): x"]).ok


def test_status_counts_tasks_closed_by_covered_acs(proj: Path, capsys):
    task_spec(proj)
    cli.main(["status"])
    assert "| 0/1 |" in capsys.readouterr().out
    write(
        proj / "tests/test_a.py",
        'import pytest\n@pytest.mark.ac("AC-A-003")\ndef test_x():\n    assert str(1) == "1"\n',
    )
    cli.main(["status"])
    assert "| 1/1 |" in capsys.readouterr().out


def test_init_writes_contributing_and_review_templates(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--ci", "both"], fakes()) == 0
    for rel in (
        "CONTRIBUTING.md",
        ".github/pull_request_template.md",
        ".gitlab/merge_request_templates/Default.md",
    ):
        assert (tmp_path / rel).is_file(), rel
    assert cli.main(["check"]) == 0


DOCS_STRUCTURE = [
    "README.md",
    "00-engineering-methodology.md",
    "00-naming-conventions.md",
    "00-requirements-engineering.md",
    "01-backlog-epics-stories.md",
    "02-architecture-decision-record.md",
    "03-security-practices.md",
    "99-problems-encountered-and-learnings.md",
    "discovery/_TEMPLATE.md",
    "design-patterns/README.md",
    "usecase-diagrams/_TEMPLATE.md",
]


def test_init_creates_the_docs_structure(proj: Path):
    for rel in DOCS_STRUCTURE:
        assert (proj / "docs" / rel).is_file(), rel
    cfg = load_config(proj)
    for key in ("requirements", "backlog"):
        assert (proj / getattr(cfg, key)).is_file(), key
    assert (proj / cfg.discovery / "_TEMPLATE.md").is_file()


def test_docs_map_links_every_top_level_document(proj: Path):
    index = (proj / "docs/README.md").read_text()
    for md in sorted((proj / "docs").glob("*.md")):
        if md.name != "README.md":
            assert f"]({md.name})" in index, f"docs/README.md does not link {md.name}"


def test_permissions_are_idempotent_and_leave_risky_commands_to_the_prompt(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cli.main(["init", "--ci", "none"], fakes())
    cli.main(["init", "--ci", "none", "--force"], fakes())
    allow = json.loads((tmp_path / ".claude/settings.json").read_text())["permissions"]["allow"]
    assert len(allow) == len(set(allow))
    joined = " ".join(allow)
    assert "update" not in joined and "init" not in joined and "run_gates" not in joined


def uc_spec(
    proj: Path,
    uc: str,
    *,
    depends=(),
    acs=(),
    tasks=(),
    rigor="light",
    diagrams=(),
    actor=None,
    context=None,
    realises=(),
    lifecycle=None,
) -> None:
    """A spec with a `Depends on` row, AC rows (`(id, "TBD" | "")`) and task rows (`(n, [ac ids])`). Task numbers run
    per area, so a spec's tasks are numbered from ten times its own number: UC-A-002's first is TSK-A-011."""
    ac_rows = "\n".join(f"| **{a}** | {note} Given x, when y, then z. | REQ-FR-001 |" for a, note in acs)
    task_rows = "\n".join(
        f"| **TSK-{uc[3]}-{(int(uc[5:]) - 1) * 10 + n:03d}** | do it | {', '.join(ids)} |" for n, ids in tasks
    )
    write(
        proj / f"docs/usecase-diagrams/{uc}-thing.md",
        f"""\
        # {uc} - Thing {uc[3:]}

        | Field | Value |
        |---|---|
        | **Use Case ID** | {uc} |
        | **Primary actor** | {actor or "(actor)"} |
        | **Bounded context** | {context or "(context)"} |
        | **Realises** | {", ".join(realises) or "(REQ-FR-/REQ-NFR- ids)"} |
        | **Lifecycle** | {lifecycle or "(yes or none)"} |
        | **Depends on** | {", ".join(depends) or "-"} |
        | **Rigor** | {rigor} |
        | **Diagrams** | {", ".join(f"[{d}]({d})" for d in diagrams) or "-"} |

        | AC id | Given / when / then | Satisfies |
        |---|---|---|
        {ac_rows}

        | Task id | Description | Closes ACs |
        |---|---|---|
        {task_rows}
        """.replace("\n        ", "\n").lstrip(),
    )


def build(proj: Path, uc: str, ac: str) -> None:
    """Code and a marked test that make `uc` built."""
    write(proj / f"src/{uc.lower()}.py", f'"""Realises {uc}"""\n')
    write(
        proj / f"tests/test_{uc.lower()}.py",
        f'import pytest\n@pytest.mark.ac("{ac}")\ndef test_x():\n    """Verifies {uc} · unit rung."""\n    assert str(1) == "1"\n',  # noqa: E501
    )


def next_json(capsys) -> dict:
    capsys.readouterr()
    cli.main(["next", "--json"])
    return json.loads(capsys.readouterr().out)


def test_links_accept_a_valid_graph_and_flag_dangling_self_and_cycle(proj: Path):
    uc_spec(proj, "UC-A-001")
    uc_spec(proj, "UC-A-002", depends=["UC-A-001"])
    assert check_links(*ctx(proj)).ok
    uc_spec(proj, "UC-A-003", depends=["UC-A-009", "UC-A-003"])
    text = check_links(*ctx(proj)).render()
    assert "UC-A-009, which has no spec" in text and "UC-A-003: depends on itself" in text
    uc_spec(proj, "UC-A-003")
    uc_spec(proj, "UC-A-001", depends=["UC-A-002"])
    res = check_links(*ctx(proj))
    assert not res.ok and "dependency cycle: UC-A-001 -> UC-A-002 -> UC-A-001" in res.render()


def test_waves_and_enables_for_a_diamond(proj: Path):
    uc_spec(proj, "UC-A-001")
    uc_spec(proj, "UC-A-002", depends=["UC-A-001"])
    uc_spec(proj, "UC-A-003", depends=["UC-A-001"])
    uc_spec(proj, "UC-A-004", depends=["UC-A-002", "UC-A-003"])
    rows = [ln.split("|")[1:5] for ln in check_links(*ctx(proj), matrix=True).lines[2:]]
    got = {r[0].strip(): (r[1].strip(), r[3].strip()) for r in rows}
    assert got == {
        "UC-A-001": ("0", "UC-A-002, UC-A-003"),
        "UC-A-002": ("1", "UC-A-004"),
        "UC-A-003": ("1", "UC-A-004"),
        "UC-A-004": ("2", "-"),
    }


def test_new_use_case_scaffold_is_at_the_requirements_stage_and_passes_links(proj: Path, capsys):
    cli.main(["new", "uc", "--area", "A", "--title", "Log in"])
    assert check_links(*ctx(proj)).ok
    n = next_json(capsys)
    assert n["command"] == "/vbench:v-1-requirements UC-A-001" and "no acceptance criteria written" in n["why"]


def test_next_walks_one_use_case_through_every_stage(proj: Path, capsys):
    ok = "AC-A-003"
    uc_spec(proj, "UC-A-001", acs=[(ok, "TBD:")])
    assert next_json(capsys)["command"] == "/vbench:v-1-requirements UC-A-001"
    uc_spec(proj, "UC-A-001", acs=[(ok, "")])
    assert next_json(capsys)["command"] == "/vbench:v-2-design UC-A-001"
    uc_spec(proj, "UC-A-001", acs=[(ok, "")], tasks=[(1, [ok])])
    assert next_json(capsys)["command"] == "/vbench:v-3-code UC-A-001 TSK-A-001"
    write(
        proj / "tests/test_a.py",
        f'import pytest\n@pytest.mark.ac("{ok}")\ndef test_x():\n    assert str(1) == "1"\n',
    )
    n = next_json(capsys)
    assert n["command"] == "/vbench:v-3-code UC-A-001" and "no code is tagged Realises" in n["why"]
    build(proj, "UC-A-001", ok)
    assert next_json(capsys)["command"] == "/vbench:v-4-verify all"  # the only use case is built


def test_next_picks_the_first_open_task_and_skips_closed_ones(proj: Path, capsys):
    uc_spec(
        proj,
        "UC-A-001",
        acs=[("AC-A-006", ""), ("AC-A-007", "")],
        tasks=[(1, ["AC-A-006"]), (2, ["AC-A-007"])],
    )
    write(
        proj / "tests/test_a.py",
        'import pytest\n@pytest.mark.ac("AC-A-006")\ndef test_x():\n    assert str(1) == "1"\n',
    )
    assert next_json(capsys)["command"] == "/vbench:v-3-code UC-A-001 TSK-A-002"


def test_next_works_the_dependency_first_and_status_shows_the_blocker(proj: Path, capsys):
    uc_spec(
        proj,
        "UC-A-002",
        depends=["UC-A-001"],
        acs=[("AC-A-008", "")],
        tasks=[(1, ["AC-A-008"])],
    )
    uc_spec(proj, "UC-A-001", acs=[("AC-A-003", "")], tasks=[(1, ["AC-A-003"])])
    n = next_json(capsys)
    assert n["command"] == "/vbench:v-3-code UC-A-001 TSK-A-001" and n["blocked"] == {"UC-A-002": ["UC-A-001"]}
    cli.main(["status"])
    out = capsys.readouterr().out
    row = next(ln for ln in out.splitlines() if ln.startswith("| UC-A-002"))
    assert "| 1 |" in row and "| UC-A-001 |" in row
    build(proj, "UC-A-001", "AC-A-003")
    assert next_json(capsys)["command"] == "/vbench:v-3-code UC-A-002 TSK-A-011"


def test_next_with_no_use_cases_and_when_everything_is_blocked(proj: Path, capsys):
    n = next_json(capsys)
    assert n["command"] == "/vbench:discovery" and n["uc"] is None
    uc_spec(proj, "UC-A-001", depends=["UC-A-002"])
    uc_spec(proj, "UC-A-002", depends=["UC-A-001"])
    capsys.readouterr()
    assert cli.main(["next", "--json"]) == 1
    n = json.loads(capsys.readouterr().out)
    assert n["command"] is None and set(n["blocked"]) == {"UC-A-001", "UC-A-002"}
    assert cli.main(["check", "links"]) == 1


def test_next_text_output(proj: Path, capsys):
    cli.main(["new", "uc", "--area", "A", "--title", "Log in"])
    capsys.readouterr()
    assert cli.main(["next"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("next: /vbench:v-1-requirements UC-A-001") and "why:" in out


PUML = "@startuml X\n!include ../_style.puml\n@enduml\n"


def designed(proj: Path, rigor: str, diagrams=(), lifecycle: str = "none") -> None:
    uc_spec(
        proj,
        "UC-A-001",
        acs=[("AC-A-003", "")],
        tasks=[(1, ["AC-A-003"])],
        rigor=rigor,
        diagrams=diagrams,
        lifecycle=lifecycle,
    )


def test_diagrams_are_required_by_rigor_only_once_designed(proj: Path):
    uc_spec(proj, "UC-A-001", acs=[("AC-A-003", "")], rigor="full")  # no task plan yet: nothing is due
    cli.main(["sync"])
    assert check_diagrams(*ctx(proj)).ok
    designed(proj, "light")
    assert check_diagrams(*ctx(proj)).ok
    designed(proj, "standard")
    assert "requires a sequence diagram" in check_diagrams(*ctx(proj)).render()
    write(proj / "docs/usecase-diagrams/UC-A-001-thing-sequence.puml", PUML)
    designed(proj, "standard", ["UC-A-001-thing-sequence.puml"])
    assert check_diagrams(*ctx(proj)).ok
    designed(proj, "full", ["UC-A-001-thing-sequence.puml"])
    assert "requires a class diagram" in check_diagrams(*ctx(proj)).render()
    write(proj / "docs/usecase-diagrams/UC-A-001-thing-class.puml", PUML)
    designed(proj, "full", ["UC-A-001-thing-sequence.puml", "UC-A-001-thing-class.puml"])
    assert check_diagrams(*ctx(proj)).ok


def test_diagrams_must_be_linked_named_and_well_formed(proj: Path):
    d = proj / "docs/usecase-diagrams"
    designed(proj, "light")
    cli.main(["sync"])
    write(d / "UC-A-001-thing-state.puml", PUML)  # on disk but not in the Diagrams row
    assert "the Diagrams row does not link UC-A-001-thing-state.puml" in check_diagrams(*ctx(proj)).render()
    designed(proj, "light", ["UC-A-001-thing-state.puml"])
    assert check_diagrams(*ctx(proj)).ok
    write(d / "UC-A-001-thing-sequence.2.puml", PUML)  # a second flow is a valid name, but still has to be linked
    assert "does not link UC-A-001-thing-sequence.2.puml" in check_diagrams(*ctx(proj)).render()
    (d / "UC-A-001-thing-sequence.2.puml").unlink()
    write(d / "UC-A-001-thing-diagram.puml", PUML)  # wrong kind
    write(d / "UC-A-009-other-class.puml", PUML)  # no such spec
    write(d / "_style.puml", "skinparam shadowing false\n")  # a shared include is not a diagram
    out = check_diagrams(*ctx(proj)).render()
    assert (
        "UC-A-001-thing-diagram.puml: name fits no spec" in out
        and "UC-A-009-other-class.puml: name fits no spec" in out
    )
    assert "_style.puml" not in out
    (d / "UC-A-001-thing-diagram.puml").unlink()
    (d / "UC-A-009-other-class.puml").unlink()
    write(d / "UC-A-001-thing-state.puml", "@startuml X\n")
    assert "missing @startuml / @enduml" in check_diagrams(*ctx(proj)).render()


def test_a_missing_required_diagram_keeps_the_use_case_at_the_design_stage(proj: Path, capsys):
    designed(proj, "standard")
    assert next_json(capsys)["command"] == "/vbench:v-2-design UC-A-001"
    write(proj / "docs/usecase-diagrams/UC-A-001-thing-sequence.puml", PUML)
    designed(proj, "standard", ["UC-A-001-thing-sequence.puml"])
    assert next_json(capsys)["command"] == "/vbench:v-3-code UC-A-001 TSK-A-001"


def test_init_scaffolds_the_shared_puml_includes_and_a_new_use_case_passes_diagrams(
    proj: Path,
):
    for name in ("_style.puml", "_legend.puml"):
        assert not any(
            ln.startswith(("@startuml", "@enduml")) for ln in (proj / "docs" / name).read_text().splitlines()
        )
    cli.main(["new", "uc", "--area", "A", "--title", "Log in"])
    assert check_diagrams(*ctx(proj)).ok and cli.main(["check", "diagrams"]) == 0
    assert "| **Diagrams** |" in (proj / "docs/usecase-diagrams/UC-A-001-log-in.md").read_text()


def test_links_mermaid_prints_waves_and_arrows(proj: Path, capsys):
    uc_spec(proj, "UC-A-001")
    uc_spec(proj, "UC-A-002", depends=["UC-A-001"])
    capsys.readouterr()
    assert cli.main(["check", "links", "--mermaid"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("```mermaid\nflowchart LR") and out.rstrip().endswith("```")
    assert 'subgraph W0["Wave 0"]' in out and 'subgraph W1["Wave 1"]' in out and "UC_A_001 --> UC_A_002" in out
    assert cli.main(["check", "refs", "--mermaid"]) == 2


def test_usecase_map_is_generated_from_the_specs_and_goes_stale_when_they_change(proj: Path, capsys):
    uc_spec(proj, "UC-N-001", actor="Author", context="Notes")
    uc_spec(proj, "UC-N-002", depends=["UC-N-001"], actor="Author", context="Notes")
    uc_spec(proj, "UC-S-001", actor="Admin", context="Sharing")
    assert "08-usecase-diagrams.puml: missing; run `vbench sync`" in check_diagrams(*ctx(proj)).render()
    assert cli.main(["sync"]) == 0 and "updated docs/08-usecase-diagrams.puml" in capsys.readouterr().out
    body = (proj / "docs/08-usecase-diagrams.puml").read_text()
    assert body.startswith("' GENERATED by `vbench sync`") and "@startuml UseCases" in body
    for part in (
        'actor "Author" as ACT_Author',
        'actor "Admin" as ACT_Admin',
        'rectangle "Notes" as CTX_Notes',
        'rectangle "Sharing" as CTX_Sharing',
        'usecase "UC-N-001\\nThing N-001" as UC_N_001',
        "ACT_Author --> UC_N_002",
        "UC_N_002 ..> UC_N_001 : needs",
    ):
        assert part in body, part
    assert check_diagrams(*ctx(proj)).ok
    cli.main(["sync"])
    assert "already up to date" in capsys.readouterr().out
    uc_spec(proj, "UC-N-002", depends=[], actor="Author", context="Notes")  # a dependency was dropped
    assert "out of date with the specs; run `vbench sync`" in check_diagrams(*ctx(proj)).render()
    cli.main(["sync"])
    assert (
        check_diagrams(*ctx(proj)).ok
        and "UC_N_002 ..> UC_N_001" not in (proj / "docs/08-usecase-diagrams.puml").read_text()
    )


def test_usecase_map_ignores_placeholders_and_progress(proj: Path):
    cli.main(["new", "uc", "--area", "A", "--title", "Log in"])  # actor and context are still "(actor)" / "(context)"
    body = (proj / "docs/08-usecase-diagrams.puml").read_text()
    assert 'rectangle "Unassigned"' in body and "actor " not in body.replace("skinparam actorStyle", "")
    before = body
    build(proj, "UC-A-001", "AC-A-009")  # progress changes nothing in the diagram
    cli.main(["sync"])
    assert (proj / "docs/08-usecase-diagrams.puml").read_text() == before


def test_new_context_allocates_tiers_and_refuses_duplicates(proj: Path, capsys):
    assert cli.main(["new", "context", "--name", "Notes"]) == 0
    assert cli.main(["new", "context", "--name", "Tagging & Search"]) == 0
    assert (proj / "docs/10-notes-ddd.puml").is_file() and (proj / "docs/20-tagging-search-ddd.puml").is_file()
    body = (proj / "docs/10-notes-ddd.puml").read_text()
    assert "@startuml Notes_DDD" in body and 'package "«service»\\nNotes" as Notes' in body and "{{" not in body
    capsys.readouterr()
    assert cli.main(["new", "context", "--name", "notes"]) == 2
    assert "already has docs/10-notes-ddd.puml" in capsys.readouterr().err


def test_full_tier_use_case_owes_its_context_model_and_two_contexts_owe_a_map(proj: Path, capsys):
    uc_spec(
        proj,
        "UC-N-001",
        acs=[("AC-N-011", "")],
        tasks=[(1, ["AC-N-011"])],
        rigor="full",
        actor="Author",
        context="Notes",
        diagrams=["UC-N-001-thing-sequence.puml", "UC-N-001-thing-class.puml"],
        lifecycle="none",
    )
    write(proj / "docs/usecase-diagrams/UC-N-001-thing-sequence.puml", PUML)
    write(proj / "docs/usecase-diagrams/UC-N-001-thing-class.puml", PUML)
    cli.main(["sync"])
    assert "UC-N-001: still owes domain model for context Notes" in check_diagrams(*ctx(proj)).render()
    assert next_json(capsys)["command"] == "/vbench:v-2-design UC-N-001"
    cli.main(["new", "context", "--name", "Notes"])
    assert check_diagrams(*ctx(proj)).ok  # one context: no map needed
    uc_spec(
        proj,
        "UC-S-001",
        acs=[("AC-S-001", "")],
        tasks=[(1, ["AC-S-001"])],
        actor="Admin",
        context="Sharing",
    )
    cli.main(["sync"])
    assert "still owes context map" in check_diagrams(*ctx(proj)).render()
    assert cli.main(["new", "context-map"]) == 2  # needs two context models first
    cli.main(["new", "context", "--name", "Sharing"])
    assert cli.main(["new", "context-map"]) == 0
    assert check_diagrams(*ctx(proj)).ok
    cmap = proj / "docs/09-context-ddd.puml"
    assert 'package "Notes\\n«Supporting»" as Notes' in cmap.read_text()
    cmap.write_text(cmap.read_text().replace("Sharing", "Other"))
    assert "does not mention context Sharing" in check_diagrams(*ctx(proj)).render()
    assert cli.main(["new", "context-map"]) == 2  # authored: never overwritten


def functional_requirements(proj: Path, *ids: str) -> None:
    doc = proj / "docs/00-requirements-engineering.md"
    rows = "\n".join(f"| **{i}** | the system shall {i} | As a user, I want {i} | STK-REQ-001 | | ⚪ |" for i in ids)
    placeholder = (
        "| **REQ-FR-nnn** | (the system shall …) | (As a …, I want … so that …) | STK-REQ-nnn | UC-A-001 | ⚪ |"
    )
    doc.write_text(doc.read_text().replace(placeholder, rows))


def block(proj: Path, doc: str, name: str) -> str:
    text = (proj / "docs" / doc).read_text()
    return text.split(f"<!-- vbench:begin {name} -->\n", 1)[1].split(f"<!-- vbench:end {name} -->", 1)[0]


def test_generated_blocks_in_the_requirements_and_backlog_follow_the_specs(proj: Path):
    functional_requirements(proj, "REQ-FR-001", "REQ-FR-002")
    uc_spec(proj, "UC-N-001", actor="Author", context="Notes", realises=["REQ-FR-001"])
    uc_spec(
        proj,
        "UC-N-002",
        depends=["UC-N-001"],
        actor="Author",
        context="Notes",
        realises=["REQ-FR-001", "REQ-FR-009"],
    )
    assert not check_docs(*ctx(proj)).ok  # the template blocks still say "none yet"
    assert cli.main(["sync"]) == 0 and check_docs(*ctx(proj)).ok

    deps = block(proj, "01-backlog-epics-stories.md", "dependencies")
    assert (
        "| **UC-N-001** Thing N-001 | - | UC-N-002 |" in deps and "| **UC-N-002** Thing N-002 | UC-N-001 | - |" in deps
    )
    waves = block(proj, "01-backlog-epics-stories.md", "waves")
    assert "| **0** | UC-N-001 |" in waves and "| **1** | UC-N-002 |" in waves and "UC_N_001 --> UC_N_002" in waves
    cov = block(proj, "01-backlog-epics-stories.md", "coverage")
    assert "| REQ-FR-001 | UC-N-001, UC-N-002 |" in cov and "| REQ-FR-002 | **none** |" in cov
    assert "not in the requirements doc: REQ-FR-009" in cov
    frmap = block(proj, "00-requirements-engineering.md", "fr-map")
    row = "| **UC-N-002** Thing N-002 | REQ-FR-001, REQ-FR-009 |"
    assert row + " [UC-N-002-thing.md](usecase-diagrams/UC-N-002-thing.md) |" in frmap
    assert cli.main(["check", "refs"]) == 0  # the generated links resolve


def test_sync_rewrites_only_inside_the_markers_and_is_idempotent(proj: Path, capsys):
    uc_spec(proj, "UC-N-001", actor="Author", context="Notes")
    doc = proj / "docs/01-backlog-epics-stories.md"
    doc.write_text(doc.read_text().replace("## 5. Coverage", "## 5. Coverage\n\nMY HAND-WRITTEN NOTE.\n", 1))
    cli.main(["sync"])
    assert "MY HAND-WRITTEN NOTE." in doc.read_text()
    capsys.readouterr()
    cli.main(["sync"])
    assert "already up to date" in capsys.readouterr().out


def test_a_hand_edit_inside_a_block_is_flagged_and_then_overwritten(proj: Path):
    uc_spec(proj, "UC-N-001", actor="Author", context="Notes")
    cli.main(["sync"])
    doc = proj / "docs/01-backlog-epics-stories.md"
    doc.write_text(doc.read_text().replace("| - | - |", "| - | UC-XX |"))
    res = check_docs(*ctx(proj))
    assert not res.ok and "block `dependencies` is out of date" in res.render()
    assert cli.main(["check", "docs"]) == 1
    cli.main(["sync"])
    assert check_docs(*ctx(proj)).ok


def test_new_use_case_refreshes_the_generated_docs(proj: Path):
    cli.main(["new", "uc", "--area", "A", "--title", "Log in"])
    assert "**UC-A-001** Log in" in block(proj, "01-backlog-epics-stories.md", "dependencies")
    assert cli.main(["check", "docs"]) == 0


def brief(proj: Path, slug: str, status: str, title: str = "Notes") -> None:
    write(
        proj / f"docs/discovery/{slug}.md",
        f"""\
        # Discovery: {title}

        | Field | Value |
        |---|---|
        | **Status** | {status} |
        """.replace("\n        ", "\n").lstrip(),
    )


def test_an_empty_project_is_routed_through_discovery_before_requirements(proj: Path, capsys):
    n = next_json(capsys)
    assert n["command"] == "/vbench:discovery" and "no use cases and no discovery brief" in n["why"]
    brief(proj, "notes", "draft")
    n = next_json(capsys)
    assert n["command"] == "/vbench:discovery docs/discovery/notes.md" and "still a draft" in n["why"]
    brief(proj, "notes", "approved")
    n = next_json(capsys)
    assert n["command"] == "/vbench:v-1-requirements docs/discovery/notes.md" and "approved" in n["why"]
    uc_spec(proj, "UC-N-001", acs=[("AC-N-011", "TBD:")])  # once a use case exists the brief no longer steers
    assert next_json(capsys)["command"] == "/vbench:v-1-requirements UC-N-001"


def test_the_brief_template_is_not_mistaken_for_a_brief(proj: Path, capsys):
    assert (proj / "docs/discovery/_TEMPLATE.md").is_file()
    assert next_json(capsys)["command"] == "/vbench:discovery"  # only the template is there


def test_new_discovery_creates_a_draft_titled_brief_and_refuses_duplicates(proj: Path, capsys):
    assert cli.main(["new", "discovery", "--title", "A small notes app"]) == 0
    body = (proj / "docs/discovery/a-small-notes-app.md").read_text()
    assert body.startswith("# Discovery: A small notes app") and "| **Status** | draft" in body
    capsys.readouterr()
    assert cli.main(["new", "discovery", "--title", "a small Notes app"]) == 2
    assert "already exists" in capsys.readouterr().err
    assert next_json(capsys)["command"] == "/vbench:discovery docs/discovery/a-small-notes-app.md"


def test_every_step_says_why_it_exists(proj: Path, capsys):
    n = next_json(capsys)
    assert n["purpose"] and "scope" in n["purpose"]
    cli.main(["next"])
    assert "for:  " in capsys.readouterr().out
    uc_spec(proj, "UC-N-001", acs=[("AC-N-011", "TBD:")])
    assert "contract" in next_json(capsys)["purpose"]
    uc_spec(proj, "UC-N-001", acs=[("AC-N-011", "")], tasks=[(1, ["AC-N-011"])])
    assert "fail" in next_json(capsys)["purpose"]  # "Writing the test first proves it can fail ..."


def test_init_scaffolds_the_guide_and_glossary_and_points_a_newcomer_to_them(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--ci", "none"], fakes()) == 0
    out = capsys.readouterr().out
    assert "/vbench:next" in out and "docs/00-getting-started.md" in out and "docs/00-glossary.md" in out
    guide = (tmp_path / "docs/00-getting-started.md").read_text()
    for part in ("/vbench:next", "vbench status", "Level 0", "(00-glossary.md)", "Why:"):
        assert part in guide, part
    assert "(00-getting-started.md)" in (tmp_path / "docs/README.md").read_text()


def test_the_glossary_defines_every_gate_stage_and_step_the_tool_names(proj: Path):
    from vbench.domain.checks import CHECKS

    glossary = (proj / "docs/00-glossary.md").read_text().lower()
    for term in [
        *CHECKS,
        "commits",
        "wave",
        "stage",
        "rigor",
        "rung",
        "tag",
        "aggregate",
        "port",
        "context map",
        "generated block",
        "discovery",
        "approval gate",
        "task",
        "acceptance criterion",
        "tdd",
    ]:
        assert term in glossary, f"the glossary does not mention {term!r}"
    for level in ("| 0 |", "| 1 |", "| 2 |"):
        assert level in glossary


def test_a_failing_check_points_to_the_glossary_and_a_passing_one_does_not(proj: Path, capsys):
    capsys.readouterr()
    assert cli.main(["check"]) == 0
    assert "glossary" not in capsys.readouterr().out
    cli.main(["new", "uc", "--area", "A", "--title", "Log in"])  # the scaffold's TBD criterion has no test
    capsys.readouterr()
    assert cli.main(["check"]) == 1
    assert "Unsure what a term means? See docs/00-glossary.md." in capsys.readouterr().out


def test_the_failure_message_for_untested_code_uses_plain_words(proj: Path, capsys):
    write(proj / "src/auth.py", '"""Realises UC-A-001"""\n')
    capsys.readouterr()
    cli.main(["check", "rungs"])
    out = capsys.readouterr().out
    assert "use cases with code but no test that verifies them" in out and "Rung-closure" not in out


def test_a_yes_lifecycle_requires_the_state_diagram_at_any_tier(proj: Path):
    designed(proj, "light", lifecycle="yes")
    cli.main(["sync"])
    assert "requires a state diagram" in check_diagrams(*ctx(proj)).render()
    write(proj / "docs/usecase-diagrams/UC-A-001-thing-state.puml", PUML)
    designed(proj, "light", ["UC-A-001-thing-state.puml"], lifecycle="yes")
    assert check_diagrams(*ctx(proj)).ok


def test_a_none_lifecycle_needs_no_state_diagram_even_at_the_full_tier(proj: Path):
    for name in ("sequence", "class"):
        write(proj / f"docs/usecase-diagrams/UC-A-001-thing-{name}.puml", PUML)
    designed(proj, "full", ["UC-A-001-thing-sequence.puml", "UC-A-001-thing-class.puml"], lifecycle="none")
    cli.main(["sync"])
    assert "state" not in check_diagrams(*ctx(proj)).render() and check_diagrams(*ctx(proj)).ok


def test_the_full_tier_makes_the_lifecycle_decision_explicit(proj: Path, capsys):
    for name in ("sequence", "class"):
        write(proj / f"docs/usecase-diagrams/UC-A-001-thing-{name}.puml", PUML)
    uc_spec(proj, "UC-A-001", rigor="full", diagrams=["UC-A-001-thing-sequence.puml", "UC-A-001-thing-class.puml"])
    cli.main(["sync"])
    uc_spec(
        proj,
        "UC-A-001",
        acs=[("AC-A-003", "")],
        tasks=[(1, ["AC-A-003"])],
        rigor="full",
        diagrams=["UC-A-001-thing-sequence.puml", "UC-A-001-thing-class.puml"],
        context="Core",
    )
    cli.main(["new", "context", "--name", "Core"])
    res = check_diagrams(*ctx(proj))
    assert not res.ok and "the full tier needs a Lifecycle decision" in res.render()
    assert next_json(capsys)["command"] == "/vbench:v-2-design UC-A-001"  # design is not finished until it is decided
    # standard and light tiers do not force the decision
    uc_spec(
        proj,
        "UC-A-001",
        acs=[("AC-A-003", "")],
        tasks=[(1, ["AC-A-003"])],
        rigor="standard",
        diagrams=["UC-A-001-thing-sequence.puml"],
        context="Core",
    )
    assert "Lifecycle decision" not in check_diagrams(*ctx(proj)).render()


def test_a_missing_required_diagram_shows_in_the_v_view_where_it_belongs(proj: Path):
    from vbench.domain.vview import build_v

    write(proj / "docs/usecase-diagrams/UC-A-001-thing-sequence.puml", PUML)
    designed(proj, "full", ["UC-A-001-thing-sequence.puml"], lifecycle="yes")
    items, _ = build_v(*ctx(proj))
    missing = {(i.phase, i.kind): i for i in items if i.label == "Missing" and i.ucs == ("UC-A-001",)}
    assert ("architecture", "class diagram") in missing and ("module-design", "state diagram") in missing
    assert all(i.status == "risk" and i.file is None for i in missing.values())


def test_the_diagram_matrix_shows_the_lifecycle_decision(proj: Path):
    designed(proj, "light", lifecycle="yes")
    cli.main(["sync"])
    row = next(ln for ln in check_diagrams(*ctx(proj), matrix=True).lines if ln.startswith("| UC-A-001"))
    assert "| yes |" in row and "state" in row


def test_status_and_check_speak_json(tmp_path, capsys, monkeypatch):
    import json as _json

    from vbench import cli

    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--stack", "none", "--ci", "none"]) == 0
    capsys.readouterr()
    assert cli.main(["check", "--json"]) == 0
    gates = _json.loads(capsys.readouterr().out)
    assert gates and all({"name", "passing", "lines"} <= set(g) and g["passing"] for g in gates)
    assert cli.main(["status", "--json"]) == 0
    st = _json.loads(capsys.readouterr().out)
    assert {"branch", "specs", "useCases", "orphans", "gates"} <= set(st) and st["useCases"] == []


def test_id_is_a_command_of_its_own_and_new_id_still_works(tmp_path, capsys, monkeypatch):
    from vbench import cli

    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--stack", "none", "--ci", "none"]) == 0
    capsys.readouterr()
    assert cli.main(["id", "fr"]) == 0
    first = capsys.readouterr().out.strip()
    assert first.startswith("REQ-FR-") and cli.main(["new", "id", "fr"]) == 0
    assert capsys.readouterr().out.strip() == first  # the old spelling is the same command


def test_help_lists_what_a_cli_user_needs_and_leaves_out_dashboard_commands(capsys):
    import pytest

    from vbench import cli

    with pytest.raises(SystemExit):
        cli.main(["--help"])
    out = capsys.readouterr().out
    for shown in ("init", "check", "new", "id", "status", "next", "sync", "update"):
        assert shown in out
    for hidden in ("export", "serve", "mcp"):
        assert f"{hidden} " not in out.split("positional arguments:")[1]
    with pytest.raises(SystemExit):
        cli.main(["serve", "--help"])  # still there for the dashboard
    assert "dashboard" in capsys.readouterr().out


def test_an_unknown_use_case_is_an_error_not_an_empty_table(tmp_path, capsys, monkeypatch):
    from vbench import cli

    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--stack", "none", "--ci", "none"]) == 0
    capsys.readouterr()
    for extra in ([], ["--json"]):
        assert cli.main(["status", "UC-N-999", *extra]) != 0
        assert "no use case or area matches `UC-N-999`" in capsys.readouterr().err


def test_check_warns_when_a_configured_folder_does_not_exist(tmp_path, capsys, monkeypatch):
    from vbench import cli

    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--stack", "none", "--ci", "none", "--prod", "app"]) == 0
    capsys.readouterr()
    cli.main(["check"])
    assert "configured folder(s) not found: app" in capsys.readouterr().err


def test_short_command_names_do_the_same_as_the_long_ones(tmp_path, capsys, monkeypatch):
    from vbench import cli

    monkeypatch.chdir(tmp_path)
    assert cli.main(["init", "--stack", "none", "--ci", "none"]) == 0
    capsys.readouterr()
    for short, long in (("c", "check"), ("st", "status"), ("n", "next")):
        code_short = cli.main([short])
        out_short = capsys.readouterr().out
        code_long = cli.main([long])
        out_long = capsys.readouterr().out
        assert out_short and (code_short, out_short) == (code_long, out_long)  # the same command, the same answer
    assert cli.main(["c", "refs"]) == 0 and cli.main(["st", "--json"]) == 0
