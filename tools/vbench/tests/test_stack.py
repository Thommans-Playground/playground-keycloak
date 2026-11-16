"""The opinionated stack: what `vbench init` scaffolds, and the architecture contract derived from the contexts."""

from __future__ import annotations

import ast
import os
import re
import subprocess
import tomllib
from pathlib import Path

import pytest

from tests.test_vbench import cli, fakes
from vbench.adapters.fs import FsWorkspace
from vbench.adapters.toml_config import load_config
from vbench.domain.stack import (
    code_contexts,
    context_package,
    display_name,
    dist_name,
    importlinter_text,
    package_name,
)

UNRESOLVED = re.compile(r"\{\{[A-Z_]+\}\}")  # vbench placeholders; GitHub's own `${{ ... }}` has spaces and lowercase


def init(tmp_path: Path, monkeypatch, *args: str) -> int:
    monkeypatch.chdir(tmp_path)
    return cli.main(["init", *args], fakes())


def text_files(root: Path):
    return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix != ".lock"]


def test_names_are_valid_identifiers_and_distribution_names():
    assert package_name("My Notes App") == "my_notes_app" and package_name("2fast") == "app_2fast"
    assert package_name("???") == "app" and context_package("tagging-search") == "tagging_search"
    assert dist_name("My Notes App") == "my-notes-app" and dist_name("???") == "app"
    assert display_name('The "best" \\ app') == "The best  app"  # safe inside a quoted TOML or Python string


def test_init_scaffolds_the_whole_stack_by_default(tmp_path: Path, monkeypatch, capsys):
    assert init(tmp_path, monkeypatch, "--name", "Notes App") == 0
    for rel in (
        "pyproject.toml", ".python-version", ".env.example", ".gitignore", "Dockerfile", "docker-compose.yml",
        ".importlinter", "src/notes_app/main.py", "src/notes_app/config.py", "src/notes_app/infrastructure/database.py",
        "src/notes_app/shared_kernel/__init__.py", "tests/test_health.py", "docs/04-technology-stack.md",
    ):  # fmt: skip
        assert (tmp_path / rel).is_file(), rel
    assert "Stack: python-fastapi, package `notes_app`" in capsys.readouterr().out
    cfg = load_config(tmp_path)
    assert (cfg.stack, cfg.package) == ("python-fastapi", "notes_app")
    assert cfg.commands == {
        "test": "uv run pytest", "lint": "uv run ruff check .", "format": "uv run ruff format --check .",
        "types": "uv run mypy .", "boundaries": "uv run lint-imports",
    }  # fmt: skip


def test_the_scaffolded_files_are_valid_and_fully_rendered(tmp_path: Path, monkeypatch):
    init(tmp_path, monkeypatch, "--name", 'The "Notes" App')
    for p in text_files(tmp_path):
        assert not UNRESOLVED.search(p.read_text()), f"{p.relative_to(tmp_path)} has an unresolved placeholder"
    project = tomllib.loads((tmp_path / "pyproject.toml").read_text())["project"]
    assert project["name"] == "the-notes-app" and project["requires-python"] == ">=3.13"
    assert {"fastapi", "sqlalchemy", "alembic", "pydantic-settings"} <= {
        re.split(r"[\[><=]", d)[0] for d in project["dependencies"]
    }
    for p in (tmp_path / "src").rglob("*.py"):
        ast.parse(p.read_text())  # every scaffolded module is valid Python
    assert 'app_name: str = "The Notes App"' in (tmp_path / "src/the_notes_app/config.py").read_text()


def test_the_stack_ships_its_decisions_and_the_docs_map_links_the_stack_doc(tmp_path: Path, monkeypatch):
    init(tmp_path, monkeypatch, "--name", "Notes App")
    adr = (tmp_path / "docs/02-architecture-decision-record.md").read_text()
    for n, title in (
        (1, "uv"),
        (2, "FastAPI"),
        (3, "PostgreSQL"),
        (4, "Ports and adapters"),
        (5, "Ruff"),
        (7, "Optional modules"),
    ):
        assert f"### ADR-DEC-00{n}" in adr and title in adr
    assert adr.count("**Status:** accepted") >= 8
    stack = (tmp_path / "docs/04-technology-stack.md").read_text()
    for part in (
        "Ruff",
        "no separate formatter",
        "PostgreSQL",
        "FastAPI",
        "Celery with Redis",
        "Next.js",
        "lint-imports",
    ):
        assert part in stack, part
    assert "Black" not in stack.replace("There is no separate formatter", "")  # Ruff replaces Black
    assert "(04-technology-stack.md)" in (tmp_path / "docs/README.md").read_text()
    assert cli.main(["check"]) == 0  # the docs, with the extra document, still pass every gate


def test_stack_none_is_the_harness_alone(tmp_path: Path, monkeypatch):
    assert init(tmp_path, monkeypatch, "--stack", "none") == 0
    assert not (tmp_path / "pyproject.toml").exists() and not (tmp_path / "src").exists()
    assert not (tmp_path / "docs/04-technology-stack.md").exists()
    assert "04-technology-stack" not in (tmp_path / "docs/README.md").read_text()
    assert "Black" not in (tmp_path / "docs/02-architecture-decision-record.md").read_text()
    cfg = load_config(tmp_path)
    assert (
        (cfg.stack, cfg.package) == ("", "") and cfg.commands["lint"] == "ruff check ." and cfg.commands["format"] == ""
    )
    assert cli.main(["check"]) == 0


def test_an_existing_project_keeps_its_code_and_still_gets_the_harness(tmp_path: Path, monkeypatch, capsys):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "mine"\n')
    assert init(tmp_path, monkeypatch, "--name", "Mine") == 0
    assert (tmp_path / "pyproject.toml").read_text() == '[project]\nname = "mine"\n'
    assert not (tmp_path / "src").exists() and not (tmp_path / "Dockerfile").exists()
    assert (tmp_path / "docs/04-technology-stack.md").is_file() and (tmp_path / ".vbench/config.toml").is_file()
    assert "already has a pyproject.toml" in capsys.readouterr().out


def test_an_unknown_stack_is_rejected(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):  # argparse rejects it before any file is written
        cli.main(["init", "--stack", "django"], fakes())
    assert not (tmp_path / ".vbench").exists()


def test_ci_gets_an_app_job_with_postgres_and_every_gate(tmp_path: Path, monkeypatch):
    init(tmp_path, monkeypatch, "--name", "Notes App")
    gh = (tmp_path / ".github/workflows/vbench.yml").read_text()
    assert "jobs:\n  gates:" in gh and "\n  app:\n" in gh and "postgres:17-alpine" in gh
    for step in (
        "ruff check .",
        "ruff format --check .",
        "mypy .",
        "lint-imports",
        "pytest",
        "bandit -r src",
        "pip-audit",
    ):
        assert step in gh, step
    assert "continue-on-error: true" in gh.split("pip-audit")[1]  # the dependency audit is informational
    gl = (tmp_path / ".gitlab-ci.vbench.yml").read_text()
    assert "\napp:\n" in gl and "uv run lint-imports" in gl and "postgres:17-alpine" in gl


def test_compose_and_dockerfile_agree_on_the_app(tmp_path: Path, monkeypatch):
    init(tmp_path, monkeypatch, "--name", "Notes App")
    docker = (tmp_path / "Dockerfile").read_text()
    assert "notes_app.main:app" in docker and "--locked" in docker and "USER app" in docker
    assert '"uvicorn"' in docker and "uv run" not in docker.split("CMD")[1]  # no uv, and no cache dir, at runtime
    compose = (tmp_path / "docker-compose.yml").read_text()
    assert (
        "postgres:17-alpine" in compose and "condition: service_healthy" in compose and "127.0.0.1:5432:5432" in compose
    )


def test_the_contract_is_derived_from_the_contexts():
    base = importlinter_text("shop", [])
    assert "root_package = shop" in base and "shop.main" in base and "contract:orders" not in base
    one = importlinter_text("shop", ["orders"])
    assert "orders: adapters > application > domain" in one and "pure-core" in one and "independence" not in one
    two = importlinter_text("shop", ["billing", "orders"])
    assert two.count("type = layers") == 3 and "type = independence" in two
    assert "shop.** -> shop.billing.public" in two and "unmatched_ignore_imports_alerting = none" in two
    assert "fastapi" in two and "sqlalchemy" in two


def test_new_context_creates_the_code_package_and_rewrites_the_contract(tmp_path: Path, monkeypatch, capsys):
    init(tmp_path, monkeypatch, "--name", "Notes App")
    assert cli.main(["new", "context", "--name", "Notes"]) == 0
    assert "(.importlinter) now covers this context" in capsys.readouterr().out
    base = tmp_path / "src/notes_app/notes"
    for sub in (
        "",
        "domain",
        "application",
        "application/ports",
        "application/use_cases",
        "adapters/inbound",
        "adapters/outbound",
    ):
        assert (base / sub / "__init__.py").is_file(), sub
    assert (tmp_path / "docs/10-notes-ddd.puml").is_file()
    assert "notes_app.notes.domain" in (tmp_path / ".importlinter").read_text()
    (base / "domain/__init__.py").write_text('"""my own words"""\n')  # work in progress must survive the next context
    assert cli.main(["new", "context", "--name", "Tagging & Search"]) == 0
    assert (base / "domain/__init__.py").read_text() == '"""my own words"""\n'
    assert (tmp_path / "src/notes_app/tagging_search/adapters/outbound/__init__.py").is_file()
    contract = (tmp_path / ".importlinter").read_text()
    assert "notes_app.tagging_search.domain" in contract and "type = independence" in contract
    cfg = load_config(tmp_path)
    assert code_contexts(cfg, FsWorkspace(tmp_path)) == ["notes", "tagging_search"]


def test_shared_packages_are_not_contexts(tmp_path: Path, monkeypatch):
    init(tmp_path, monkeypatch, "--name", "Notes App")
    assert code_contexts(load_config(tmp_path), FsWorkspace(tmp_path)) == []  # shared_kernel and infrastructure only


def test_without_a_stack_a_new_context_is_only_the_diagram(proj: Path, capsys):
    assert cli.main(["new", "context", "--name", "Notes"]) == 0
    assert (proj / "docs/10-notes-ddd.puml").is_file() and not (proj / "src").exists()
    assert not (proj / ".importlinter").exists() and ".importlinter" not in capsys.readouterr().out


@pytest.mark.skipif(not os.environ.get("VBENCH_STACK_E2E"), reason="needs network and uv; set VBENCH_STACK_E2E=1")
def test_a_generated_project_passes_its_own_gates(tmp_path: Path, monkeypatch):
    """The real thing: install, then lint, format, types, architecture and tests, with two contexts."""
    init(tmp_path, monkeypatch, "--name", "Notes App")
    cli.main(["new", "context", "--name", "Notes"])
    cli.main(["new", "context", "--name", "Billing"])
    subprocess.run(["uv", "sync"], cwd=tmp_path, check=True, capture_output=True)
    for cmd in (
        ["ruff", "check", "."],
        ["ruff", "format", "--check", "."],
        ["mypy", "."],
        ["lint-imports"],
        ["pytest", "-q"],
    ):
        r = subprocess.run(["uv", "run", *cmd], cwd=tmp_path, capture_output=True, text=True)
        assert r.returncode == 0, f"{' '.join(cmd)}\n{r.stdout[-800:]}{r.stderr[-400:]}"
