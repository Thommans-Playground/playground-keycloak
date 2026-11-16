"""Use case: write the project's ontology in the formats people and tools read (`vbench ontology`)."""

from __future__ import annotations

from ..domain.config import Config
from ..domain.errors import UsageError
from ..domain.ontology import FORMATS, build_ontology, file_name, render
from ..ports import Workspace


def render_ontology(cfg: Config, ws: Workspace, fmt: str) -> str:
    if fmt not in FORMATS:
        raise UsageError(f"unknown ontology format `{fmt}`; choose one of {', '.join(FORMATS)}.")
    return render(build_ontology(cfg, ws), fmt)


def write_ontology(cfg: Config, ws: Workspace, formats: tuple[str, ...] = FORMATS) -> list[str]:
    """Write the files under the `ontology` folder; return the paths that changed."""
    ontology, changed = build_ontology(cfg, ws), []
    for fmt in formats:
        path, body = f"{cfg.ontology}/{file_name(fmt)}", render(ontology, fmt)
        if not (ws.exists(path) and ws.read(path) == body):
            ws.write(path, body)
            changed.append(path)
    return changed


def refresh_ontology(cfg: Config, ws: Workspace) -> list[str]:
    """Rewrite only the generated files that already exist, so `vbench sync` keeps them current without creating any."""
    present = tuple(f for f in FORMATS if ws.exists(f"{cfg.ontology}/{file_name(f)}"))
    return write_ontology(cfg, ws, present) if present else []
