"""The text of a new use-case spec, from the template. One place makes it, so `vbench new uc` and the dashboard's
*Add use case* give the same file."""

from __future__ import annotations

import re
from collections.abc import Sequence

from .config import Config
from .mdtable import upsert_row

TEMPLATE = "docs/usecase-diagrams/_TEMPLATE.md"
REALISES_ROW = re.compile(r"^(\|\s*\*\*Realises\*\*\s*\|)[^|\n]*(\|)[ \t]*$", re.MULTILINE)


def ac_table(header: list[str]) -> bool:
    """The acceptance-criteria table of a spec: `| AC id | Given / when / then | Satisfies |`."""
    return any(h.startswith("given") for h in header) and "satisfies" in header


def spec_text(cfg: Config, template: str, uc: str, title: str, ac: str, task: str, realises: Sequence[str] = ()) -> str:
    """The template with the use case's ids, title and rigor filled in. When it realises requirements, the Realises row
    names them and so does the scaffold criterion, which is the one a person is meant to write next."""
    body = (
        template.replace("UC-X-nnn", uc)
        .replace("<Title>", title)
        .replace("AC-X-nnn", ac)
        .replace("TSK-X-nnn", task)
        .replace("<rigor>", cfg.rigor_default)
    )
    if realises:
        ids = ", ".join(realises)
        body = REALISES_ROW.sub(lambda m: f"{m.group(1)} {ids} {m.group(2)}", body)
        body = upsert_row(body, ac_table, ac, {"satisfies": ids})
    return body
