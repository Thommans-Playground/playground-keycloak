"""Use case: regenerate what is derived from the specs, so it cannot drift."""

from __future__ import annotations

from ..domain.config import Config
from ..domain.contexts import USECASE_MAP, at
from ..domain.docsgen import docs_with_blocks, regenerate
from ..domain.specs import read_specs
from ..domain.usecase_map import render_usecase_map
from ..ports import Workspace
from .ontology import refresh_ontology


def sync(cfg: Config, ws: Workspace) -> list[str]:
    """Write every derived artifact; return the paths that changed. With no specs there is nothing to draw."""
    changed: list[str] = []
    if read_specs(cfg, ws):
        path, body = at(cfg, USECASE_MAP), render_usecase_map(cfg, ws)
        if not (ws.exists(path) and ws.read(path) == body):
            ws.write(path, body)
            changed.append(path)
    for doc, names in docs_with_blocks(cfg, ws):  # generated blocks inside the authored requirements and backlog docs
        text = ws.read(doc)
        fresh = regenerate(text, names, cfg, ws, doc)
        if fresh != text:
            ws.write(doc, fresh)
            changed.append(doc)
    changed += refresh_ontology(cfg, ws)
    return changed
