"""The hexagon holds. Verifies AC-36 (NFR-3): no domain file imports an adapter, a framework or an outside library.

Each bounded context is a package under app/ with a domain/ folder. The rules, for every context:
  - domain/ imports the standard library and itself, nothing else
  - ports.py imports the standard library and the domain
  - service.py imports the standard library, the domain and the ports (never an adapter or a framework)
  - only app/main.py (the composition root) imports an adapter
  - a context never imports another context: they talk through ports
"""

import ast
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
STDLIB = set(sys.stdlib_module_names)


def imports_of(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"{path.name}: use absolute imports, so the rules below can be checked"
            found.add(node.module or "")
    return found


def contexts() -> list[str]:
    return sorted(p.name for p in APP.iterdir() if (p / "domain").is_dir())


def outside(path: Path, allowed_prefixes: list[str]) -> list[str]:
    """Imports that are neither the standard library nor one of the allowed app packages."""
    bad = []
    for mod in imports_of(path):
        top = mod.split(".")[0]
        if top in STDLIB:
            continue
        if any(mod == p or mod.startswith(p + ".") for p in allowed_prefixes):
            continue
        bad.append(mod)
    return sorted(bad)


def test_there_is_at_least_the_access_context():
    assert "access" in contexts()


def test_the_domain_imports_only_itself_and_the_standard_library():
    for c in contexts():
        for f in (APP / c / "domain").glob("*.py"):
            assert outside(f, [f"app.{c}.domain"]) == [], f"{c}/domain/{f.name} reaches outside the domain"


def test_ports_import_only_the_domain():
    for c in contexts():
        assert outside(APP / c / "ports.py", [f"app.{c}.domain"]) == []


def test_use_cases_know_ports_and_the_domain_never_adapters():
    for c in contexts():
        assert outside(APP / c / "service.py", [f"app.{c}.domain", f"app.{c}.ports"]) == []


def test_only_the_composition_root_imports_an_adapter():
    for f in APP.rglob("*.py"):
        if f.name == "main.py" and f.parent == APP:
            continue
        for mod in imports_of(f):
            if ".adapters" in mod:
                parts = mod.split(".")
                owner = parts[1] if len(parts) > 1 else ""
                inside_own_adapters = f.is_relative_to(APP / owner / "adapters") if owner else False
                assert inside_own_adapters, f"{f.relative_to(APP)} imports {mod}"


def test_contexts_do_not_import_each_other():
    cs = contexts()
    for c in cs:
        for f in (APP / c).rglob("*.py"):
            for mod in imports_of(f):
                for other in cs:
                    assert other == c or not mod.startswith(f"app.{other}"), f"{f.relative_to(APP)} imports {mod}"
