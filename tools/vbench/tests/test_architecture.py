"""The dependency rule of the hexagon: the core never imports an adapter, a framework or the outside world."""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src" / "vbench"
# Modules that mean I/O or a delivery mechanism. The core talks to them only through `ports`.
OUTSIDE = {"subprocess", "argparse", "shutil", "tomllib", "json", "importlib", "os", "sys", "pathlib"}
ALLOWED_IN_DOMAIN = {("pathlib", "PurePosixPath")}


def imports(path: Path) -> list[tuple[str, str, int]]:
    out = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            out += [(a.name, "", node.lineno) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mod = ("." * node.level) + (node.module or "")
            out += [(mod, a.name, node.lineno) for a in node.names]
    return out


def violations(layer: str, forbid_outside: set[str], forbid_local: tuple[str, ...]) -> list[str]:
    bad = []
    for path in sorted((SRC / layer).rglob("*.py")):
        for mod, name, line in imports(path):
            top = mod.lstrip(".").split(".")[0]
            local = mod.lstrip(".")
            if top in forbid_outside and (top, name) not in ALLOWED_IN_DOMAIN:
                bad.append(f"{path.relative_to(SRC)}:{line} imports {mod}")
            if mod.startswith(".") and any(
                local.split(".")[0] == f or local.endswith(f) or f in local.split(".") for f in forbid_local
            ):
                bad.append(f"{path.relative_to(SRC)}:{line} imports {mod}")
    return bad


def test_domain_is_pure():
    assert violations("domain", OUTSIDE, ("adapters", "cli", "app")) == []


def test_use_cases_depend_on_ports_not_adapters():
    # app/ may use json (it renders the settings file) but never an adapter or the cli.
    assert violations("app", OUTSIDE - {"json"}, ("adapters", "cli")) == []
