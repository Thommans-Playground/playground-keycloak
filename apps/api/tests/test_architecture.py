"""The hexagon holds. Verifies AC-36 (NFR-3): no domain file imports an adapter, a framework or an outside library.

The layout is the one in ADR 0010 (ports and adapters, as in "Architecture Patterns with Python").
Each bounded context is a package under app/ with a domain/ folder, and always has the same shape:

    <context>/domain/               rules, pure: standard library and itself only
    <context>/application/          use cases and the ports they need: domain and itself
    <context>/adapters/inbound/     drives the app (HTTP): application, domain, web libraries
    <context>/adapters/outbound/    driven by the app (database, Keycloak, JWT): ports, domain, infrastructure libraries

Outside the contexts only these exist: main.py (the entry point), composition/ (the composition root, the only
place that sees every adapter) and infrastructure/ (settings and the database base, which belong to no context).
Every rule names its reason, so a failure teaches.
"""

import ast
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
STDLIB = set(sys.stdlib_module_names)

SHARED_PACKAGES = {"composition", "infrastructure"}
LAYERS = {"domain", "application", "adapters"}
ADAPTER_SIDES = {"inbound", "outbound"}
WEB_LIBS = {"fastapi", "starlette", "pydantic"}
OUTBOUND_LIBS = {"sqlalchemy", "httpx", "jwt"}
INFRASTRUCTURE_LIBS = {"sqlalchemy", "pydantic_settings", "pydantic"}


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


def py_files(folder: Path) -> list[Path]:
    return sorted(f for f in folder.rglob("*.py") if "__pycache__" not in f.parts)


def folders(path: Path) -> set[str]:
    return {p.name for p in path.iterdir() if p.is_dir() and p.name != "__pycache__"}


def outside(path: Path, allowed_prefixes: list[str], libraries: set[str] = frozenset()) -> list[str]:
    """Imports that are neither the standard library, an allowed library, nor one of the allowed app packages."""
    bad = []
    for mod in imports_of(path):
        top = mod.split(".")[0]
        if top in STDLIB or top in libraries:
            continue
        if any(mod == p or mod.startswith(p + ".") for p in allowed_prefixes):
            continue
        bad.append(mod)
    return sorted(bad)


def test_there_is_at_least_the_access_context():
    assert "access" in contexts()


def test_only_known_packages_sit_next_to_the_contexts():
    # A package nobody named is outside every rule below. Add it to the ADR and to SHARED_PACKAGES on purpose.
    top = folders(APP)
    assert top <= set(contexts()) | SHARED_PACKAGES, f"unknown top level packages: {sorted(top - set(contexts()) - SHARED_PACKAGES)}"


def test_no_loose_files_at_the_top_but_the_entry_point():
    loose = sorted(f.name for f in APP.glob("*.py") if f.name not in {"__init__.py", "main.py"})
    assert loose == [], f"loose files {loose}: settings go in infrastructure/, wiring in composition/, the rest in a context"


def test_every_context_has_the_same_shape():
    for c in contexts():
        assert folders(APP / c) == LAYERS, f"{c}/ must hold exactly {sorted(LAYERS)}, found {sorted(folders(APP / c))}"
        stray = [f.name for f in (APP / c).glob("*.py") if f.name != "__init__.py"]
        assert stray == [], f"{c}/ holds loose files {stray}: they belong in a layer"
        assert folders(APP / c / "adapters") == ADAPTER_SIDES, f"{c}/adapters must hold exactly {sorted(ADAPTER_SIDES)}"


def test_the_domain_imports_only_itself_and_the_standard_library():
    for c in contexts():
        for f in py_files(APP / c / "domain"):
            assert outside(f, [f"app.{c}.domain"]) == [], f"{f.relative_to(APP)} reaches outside the domain"


def test_the_application_knows_the_domain_and_its_own_ports_never_a_framework_or_an_adapter():
    for c in contexts():
        for f in py_files(APP / c / "application"):
            bad = outside(f, [f"app.{c}.domain", f"app.{c}.application"])
            assert bad == [], f"{f.relative_to(APP)} imports {bad}: use cases talk to ports, not to adapters or frameworks"


def test_inbound_adapters_call_the_application_and_use_only_web_libraries():
    for c in contexts():
        for f in py_files(APP / c / "adapters" / "inbound"):
            bad = outside(f, [f"app.{c}.domain", f"app.{c}.application", f"app.{c}.adapters.inbound"], WEB_LIBS)
            assert bad == [], f"{f.relative_to(APP)} imports {bad}: an inbound adapter only translates HTTP into use cases"


def test_outbound_adapters_implement_ports_and_use_infrastructure_libraries():
    for c in contexts():
        for f in py_files(APP / c / "adapters" / "outbound"):
            bad = outside(
                f,
                [f"app.{c}.domain", f"app.{c}.application", f"app.{c}.adapters.outbound", "app.infrastructure"],
                OUTBOUND_LIBS,
            )
            assert bad == [], f"{f.relative_to(APP)} imports {bad}: an outbound adapter never reaches the web side"


def test_infrastructure_belongs_to_no_context():
    for f in py_files(APP / "infrastructure"):
        bad = outside(f, ["app.infrastructure"], INFRASTRUCTURE_LIBS)
        assert bad == [], f"{f.relative_to(APP)} imports {bad}: infrastructure must not know a context"


def test_only_the_composition_root_imports_an_adapter():
    for f in py_files(APP):
        rel = f.relative_to(APP)
        if rel.parts[0] == "composition":
            continue
        for mod in imports_of(f):
            if ".adapters" not in mod:
                continue
            owner = mod.split(".")[1]
            assert f.is_relative_to(APP / owner / "adapters"), f"{rel} imports {mod}: only composition/ wires adapters"


def test_the_entry_point_only_calls_the_composition_root():
    bad = outside(APP / "main.py", ["app.composition"])
    assert bad == [], f"main.py imports {bad}: keep it a one line entry point"


def test_contexts_do_not_import_each_other():
    cs = contexts()
    for c in cs:
        for f in py_files(APP / c):
            for mod in imports_of(f):
                for other in cs:
                    assert other == c or not mod.startswith(f"app.{other}"), f"{f.relative_to(APP)} imports {mod}"
