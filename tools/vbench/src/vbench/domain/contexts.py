"""System-level diagram files, named after MK3's scheme:

08-usecase-diagrams.puml    generated from the specs (actors, use cases by bounded context, dependencies)
09-context-ddd.puml         the context map: contexts, subdomain kinds, integration patterns (authored)
NN-<context>-ddd.puml       one tactical domain model per bounded context, NN = 10, 20, ... (authored)
"""

from __future__ import annotations

import posixpath
import re

from ..ports import Workspace
from .config import Config

USECASE_MAP = "08-usecase-diagrams.puml"
CONTEXT_MAP = "09-context-ddd.puml"
CONTEXT_FILE = re.compile(r"^(?P<n>\d{2})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)-ddd\.puml$")


def at(cfg: Config, name: str) -> str:
    return f"{cfg.docs.rstrip('/')}/{name}"


def context_files(cfg: Config, ws: Workspace) -> dict[str, str]:
    """slug -> path of each per-context domain model in the docs root (the context map is not one)."""
    out = {}
    for p in ws.files([cfg.docs], [".puml"]):
        name = posixpath.basename(p)
        m = CONTEXT_FILE.match(name)
        if m and posixpath.dirname(p) == cfg.docs.rstrip("/") and name != CONTEXT_MAP:
            out[m.group("slug")] = p
    return out


def next_context_number(cfg: Config, ws: Workspace) -> int:
    """10, 20, 30 ... one tier above the highest taken; 09 is the context map."""
    taken = [int(CONTEXT_FILE.match(posixpath.basename(p)).group("n")) for p in context_files(cfg, ws).values()]
    return max([n for n in taken if n >= 10], default=0) // 10 * 10 + 10
