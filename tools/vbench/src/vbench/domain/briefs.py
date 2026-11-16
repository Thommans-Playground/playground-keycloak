"""Discovery briefs: the analysis done before any requirement exists.

A brief is `<discovery folder>/<slug>.md` with a `Status` row (`draft` until the human approves it, then `approved`).
`vbench next` uses them to route an empty project: no brief means start discovery, a draft means finish and approve
it, an approved one means turn it into requirements.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass

from ..ports import Workspace
from .config import Config
from .specs import row

H1 = re.compile(r"^#\s+(?:Discovery:\s*)?(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Brief:
    path: str
    title: str
    status: str  # "draft" or "approved"


def read_briefs(cfg: Config, ws: Workspace) -> list[Brief]:
    out = []
    for path in ws.files([cfg.discovery], [".md"]):
        name = posixpath.basename(path)
        if name.startswith("_"):  # the template
            continue
        text = ws.read(path)
        t = H1.search(text)
        status = re.split(r"[\s/,]+", (row(text, "Status") or "draft").lower())[0]
        out.append(Brief(path, t.group(1) if t else name[:-3], "approved" if status == "approved" else "draft"))
    return out
