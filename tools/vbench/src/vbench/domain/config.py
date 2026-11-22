"""Per-project settings (the contents of `.vbench/config.toml`), as plain values.

Everything that was hard-coded in the original check scripts (where the docs, specs, production code and
tests live; what an id looks like; how a test marks an acceptance criterion) is a setting here, so the
same checks run on any repo. Paths are relative to the project root, in POSIX form; the `Workspace` port
resolves them. Parsing the TOML file is an adapter's job (`adapters/toml_config.py`).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any

from .errors import ConfigError

CONFIG_PATH = ".vbench/config.toml"

DEFAULTS: dict[str, Any] = {
    "docs": "docs",
    "specs": "docs/usecase-diagrams",
    "requirements": "docs/00-requirements-engineering.md",
    "backlog": "docs/01-backlog-epics-stories.md",
    "discovery": "docs/discovery",
    "prod": ["src"],
    "tests": ["tests"],
    "prod_ext": [".py"],
    "test_ext": [".py"],
    "results": "",  # a JUnit XML file of the last test run: with it, a test counts only if it passed there
    "untagged_ok": [],  # production files allowed to realise no use case (`__init__.py` always is)
    "uc_pattern": r"UC-[A-Z]-\d{3}",
    "ac_pattern": r"AC-[A-Z]-\d{3}",
    "task_pattern": r"TSK-[A-Z]-\d{3}",
    "step_pattern": r"STP-[A-Z]-\d{3}",
    "ac_marker": "pytest.mark.ac",
    "rigor_default": "light",
    "vbench_version": "",
    "stack": "",
    "package": "",
    "base_branch": "main",
    "commit_types": ["feat", "fix", "docs", "refactor", "perf", "test", "build", "ci", "chore"],
    "commit_pattern": "",  # empty = derive from commit_types and uc_pattern
    "branch_pattern": "",  # empty = `<type>/<slug>` with the commit types
    "ontology": "docs/ontology",  # where `vbench ontology --write` puts the generated files
    "ontology_iri": "urn:vbench:project:",  # the namespace of this project's individuals
    "branch_max_days": 5,  # a branch older than this is a note in `vbench doctor` (trunk-based: keep branches short)
}


def bounded(pattern: str) -> re.Pattern[str]:
    """An id pattern that must stand alone: `UC-A-0021` is not `UC-A-002`, and `XUC-A-002` is not `UC-A-002`."""
    return re.compile(rf"(?<![A-Za-z0-9])(?:{pattern})(?![A-Za-z0-9])")


def _as_list(v: Any) -> list[str]:
    return [v] if isinstance(v, str) else list(v)


@dataclass
class Config:
    docs: str
    specs: str
    requirements: str
    backlog: str
    discovery: str
    prod: list[str]
    tests: list[str]
    prod_ext: tuple[str, ...]
    test_ext: tuple[str, ...]
    uc_pattern: str
    ac_pattern: str
    task_pattern: str
    ac_marker: str
    rigor_default: str
    vbench_version: str = ""
    stack: str = ""  # the scaffolded stack, e.g. python-fastapi; empty = harness only
    package: str = ""  # the Python package under the prod folder, for the stack's code
    base_branch: str = "main"
    commit_types: tuple[str, ...] = ("feat", "fix", "docs", "refactor", "perf", "test", "build", "ci", "chore")
    commit_pattern: str = ""
    branch_pattern: str = ""
    branch_max_days: int = 5
    ontology: str = "docs/ontology"
    ontology_iri: str = "urn:vbench:project:"
    step_pattern: str = r"STP-[A-Z]-\d{3}"  # a step of a use case's sequence diagram
    results: str = ""
    untagged_ok: list[str] = field(default_factory=list)  # globs of production files that may realise nothing
    commands: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> Config:
        s = {**DEFAULTS, **raw.get("vbench", {})}
        try:
            for pat in (
                s["uc_pattern"],
                s["ac_pattern"],
                s["task_pattern"],
                s["step_pattern"],
                s["commit_pattern"],
                s["branch_pattern"],
            ):
                re.compile(pat)
        except re.error as e:
            raise ConfigError(f"Invalid id pattern in config: {e}") from e
        return cls(
            docs=s["docs"],
            specs=s["specs"],
            requirements=s["requirements"],
            backlog=s["backlog"],
            discovery=s["discovery"],
            prod=_as_list(s["prod"]),
            tests=_as_list(s["tests"]),
            prod_ext=tuple(_as_list(s["prod_ext"])),
            test_ext=tuple(_as_list(s["test_ext"])),
            results=str(s["results"]),
            untagged_ok=_as_list(s["untagged_ok"]),
            uc_pattern=s["uc_pattern"],
            ac_pattern=s["ac_pattern"],
            task_pattern=s["task_pattern"],
            step_pattern=s["step_pattern"],
            ontology=s["ontology"],
            ontology_iri=s["ontology_iri"],
            ac_marker=s["ac_marker"],
            rigor_default=s["rigor_default"],
            vbench_version=str(s["vbench_version"]),
            stack=str(s["stack"]),
            package=str(s["package"]),
            base_branch=s["base_branch"],
            commit_types=tuple(t.lower() for t in _as_list(s["commit_types"])),  # older configs said FEAT
            commit_pattern=s["commit_pattern"],
            branch_pattern=s["branch_pattern"],
            branch_max_days=int(s["branch_max_days"]),
            commands=dict(raw.get("commands", {})),
        )

    # --- compiled patterns -------------------------------------------------
    @property
    def uc_re(self) -> re.Pattern[str]:
        return bounded(self.uc_pattern)

    @property
    def ac_re(self) -> re.Pattern[str]:
        return bounded(self.ac_pattern)

    @property
    def step_re(self) -> re.Pattern[str]:
        return bounded(self.step_pattern)

    @property
    def ac_decl_re(self) -> re.Pattern[str]:
        """A declaring row in a spec's AC table: the id is the bolded first cell."""
        return re.compile(rf"^\|\s*\*\*({self.ac_pattern})\*\*(.*)$", re.MULTILINE)

    @property
    def task_decl_re(self) -> re.Pattern[str]:
        """A declaring row in a spec's task table: the id (`TSK-A-002`) is the bolded first cell."""
        return re.compile(rf"^\|\s*\*\*({self.task_pattern})\*\*(.*)$", re.MULTILINE)

    @property
    def commit_re(self) -> re.Pattern[str]:
        """Conventional Commits, `<type>[(<UC>[/<TSK>])][!]: <description>`; groups type, uc, task, breaking, desc."""
        if self.commit_pattern:
            return re.compile(self.commit_pattern)
        types = "|".join(re.escape(t) for t in self.commit_types)
        return re.compile(
            rf"^(?P<type>{types})(?:\((?P<uc>{self.uc_pattern})(?:/(?P<task>{self.task_pattern}))?\))?"
            r"(?P<breaking>!)?: (?P<desc>\S.*)$"
        )

    @property
    def branch_re(self) -> re.Pattern[str]:
        if self.branch_pattern:
            return re.compile(self.branch_pattern)
        types = "|".join(re.escape(t) for t in self.commit_types)
        return re.compile(rf"^(?:{types})/[a-z0-9][a-z0-9._-]*$")

    @property
    def ac_mark_re(self) -> re.Pattern[str]:
        return re.compile(re.escape(self.ac_marker) + r"\(([^)]*)\)")

    @property
    def docs_ref_re(self) -> re.Pattern[str]:
        """Literal `<docs>/….md|.puml` paths, as written in code docstrings and prose."""
        return re.compile(re.escape(PurePosixPath(self.docs).name) + r"/[\w./-]+\.(?:md|puml)")
