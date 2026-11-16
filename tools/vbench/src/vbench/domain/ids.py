"""Id shapes and allocation. Every id has three parts, `<KIND>-<SCOPE>-<NNN>`, and ids are append-only: a retired
artifact never frees its number.

    STK-PRB-001   a problem someone has              STK-REQ-001  a stakeholder's raw request
    REQ-FR-001    a functional requirement
    REQ-NFR-001   a non-functional requirement       UC-A-001     a use case (A = the area letter)
    AC-A-001      an acceptance criterion            TSK-A-001    a delivery task
    STP-A-001     a step of a use case's sequence diagram, tagged in code beside `Realises UC-…`
    SYS-CTX-001, ARC-DOM-001, MOD-SEQ-001, COD-SRC-001, TST-UNT-001 ...   discovered artifacts (see `registry`)

The area letter and the number are the only authored parts; a criterion or task belongs to the use case whose spec
declares it, not to the one its number suggests.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..ports import Workspace
from .config import Config

PROBLEM_ID = r"STK-PRB-\d{3}"
REQUEST_ID = r"STK-REQ-\d{3}"
FR_ID = r"REQ-FR-\d{3}"
NFR_ID = r"REQ-NFR-\d{3}"
STAKEHOLDER_ID = r"STK-PER-\d{3}"
REQ_ID = re.compile(rf"\b(?:{REQUEST_ID}|{FR_ID}|{NFR_ID})\b")

# what `vbench id` can allocate: kind -> (prefix, needs an area letter)
ALLOCATABLE: dict[str, tuple[str, bool]] = {
    "problem": ("STK-PRB", False),
    "request": ("STK-REQ", False),
    "stakeholder": ("STK-PER", False),
    "fr": ("REQ-FR", False),
    "nfr": ("REQ-NFR", False),
    "ac": ("AC", True),
    "task": ("TSK", True),
    "step": ("STP", True),
}


def next_number(prefix: str, texts: Iterable[str]) -> int:
    """One above the highest `<prefix>-<NNN>` that any text already mentions."""
    used = [int(n) for text in texts for n in re.findall(rf"\b{re.escape(prefix)}-(\d+)\b", text)]
    return max(used, default=0) + 1


def next_ids(kind: str, area: str, texts: Iterable[str], count: int = 1) -> list[str]:
    """The next `count` free ids of a kind, e.g. `["AC-A-004", "AC-A-005"]`."""
    prefix, scoped = ALLOCATABLE[kind]
    stem = f"{prefix}-{area}" if scoped else prefix
    first = next_number(stem, texts)
    return [f"{stem}-{first + i:03d}" for i in range(count)]


def next_uc_id(area: str, spec_names: Iterable[str], texts: Iterable[str]) -> str:
    """`UC-<area>-<NNN>`, one above every number a spec name, production file or test already uses."""
    return f"UC-{area}-{next_number(f'UC-{area}', [*spec_names, *texts]):03d}"


def collect_id_texts(cfg: Config, ws: Workspace) -> list[str]:
    """Everything an id can already be written in: the specs, the requirements doc, the code and the tests."""
    paths = [
        *ws.files([cfg.specs], [".md", ".puml"]),
        *ws.files(cfg.prod, cfg.prod_ext),
        *ws.files(cfg.tests, cfg.test_ext),
    ]
    return [ws.read(p) for p in paths] + ([ws.read(cfg.requirements)] if ws.exists(cfg.requirements) else [])
