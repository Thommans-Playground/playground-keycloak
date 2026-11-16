"""What a use-case spec's header says, read once: its title, actor, bounded context and rigor tier."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass

from ..ports import Workspace
from .config import Config

TITLE = re.compile(r"^#\s+UC-\S+\s*[-:–—]\s*(.+?)\s*$", re.MULTILINE)


def slug(name: str) -> str:
    """`Notes & Tags` -> `notes-tags`. The file-name form of a bounded context."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def row(text: str, label: str) -> str | None:
    """The value cell of `| **<label>** | value |`, or None when absent or still a placeholder like `(actor)`."""
    m = re.search(rf"^\|\s*\*\*{re.escape(label)}\*\*\s*\|(.*)\|\s*$", text, re.MULTILINE)
    value = m.group(1).strip() if m else ""
    return None if not value or value == "-" or value.startswith("(") else value


@dataclass(frozen=True)
class SpecInfo:
    uc: str
    stem: str
    path: str
    title: str
    actor: str | None
    context: str | None
    rigor: str
    lifecycle: str = ""  # "yes" (draw a state diagram), "none" (declared: no lifecycle), "" (undecided)


YES, NONE = {"yes", "y", "true"}, {"none", "no", "n", "false"}


def lifecycle_of(text: str) -> str:
    """The spec's `Lifecycle` row as "yes", "none" or "" (still a placeholder, so undecided)."""
    words = (row(text, "Lifecycle") or "").split()
    word = words[0].lower().strip(".,;:") if words else ""
    return "yes" if word in YES else "none" if word in NONE else ""


def read_specs(cfg: Config, ws: Workspace) -> list[SpecInfo]:
    out = []
    for path in ws.files([cfg.specs], [".md"]):
        name = posixpath.basename(path)
        m = cfg.uc_re.match(name) if name.startswith("UC-") else None
        if not m:
            continue
        text = ws.read(path)
        t = TITLE.search(text)
        title = t.group(1) if t else name[len(m.group(0)) + 1 : -3].replace("-", " ").capitalize()
        rigor = (row(text, "Rigor") or cfg.rigor_default).split()[0].lower()
        out.append(
            SpecInfo(
                m.group(0),
                name[:-3],
                path,
                title,
                row(text, "Primary actor"),
                row(text, "Bounded context"),
                rigor,
                lifecycle_of(text),
            )
        )
    return out
