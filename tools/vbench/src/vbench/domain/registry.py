"""The id registry: a standard id for every artifact that is discovered rather than written.

Requirements, use cases, criteria and tasks carry their id in the document that declares them. A context, a domain
model, a diagram, a code file and a test do not, so each is given one here: `SYS-CTX-001`, `ARC-DOM-001`,
`MOD-SEQ-001`, `COD-SRC-001`, `TST-UNT-001`. The registry is a table in `<docs>/00-id-registry.md` that
`vbench sync` only ever extends: a row is never rewritten or renumbered, and a number is never reused, so an id keeps
meaning the same artifact (its alias) after files are added, moved or deleted. Renaming a file or a test is a new
alias, so it gets a new id and the old row stays as a record.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..ports import Workspace
from .config import Config
from .model import natural_key
from .vview import VItem, build_v

REGISTRY_DOC = "00-id-registry.md"
ROW = re.compile(r"^\|\s*([A-Z]{3}-[A-Z]{3}-\d{3})\s*\|\s*`?([^`|\n]+?)`?\s*\|", re.MULTILINE)
AUTHORED = ("problem", "request", "FR", "NFR", "task")  # their id is written in the document that declares them
DIAGRAM_PREFIX = {"sequence": "MOD-SEQ", "state": "MOD-STA", "class": "ARC-CLS"}
TEST_PREFIX = {"unit": "TST-UNT", "integration": "TST-INT", "system": "TST-SYS", "acceptance": "TST-ACC"}
HEADER = "| Id | Alias | Kind |\n|---|---|---|\n"
EMPTY = "_Nothing to register yet._\n"


def registry_path(cfg: Config) -> str:
    return f"{cfg.docs.rstrip('/')}/{REGISTRY_DOC}"


def prefix_of(item: VItem) -> str | None:
    """The `<AREA>-<KIND>` an item is registered under, or None when its id is already written in a document."""
    if item.kind in AUTHORED:
        return None
    if item.kind == "context":
        return "SYS-CTX"
    if item.kind == "domain model":
        return "ARC-DOM"
    if item.kind.endswith(" diagram"):
        return DIAGRAM_PREFIX[item.kind.split()[0]]
    if item.kind == "code":
        return "COD-SRC"
    return TEST_PREFIX.get(item.phase, "TST-UNP")


def alias_of(item: VItem) -> str:
    """What the artifact is called in the repo. A diagram is its use case and kind (`UC-A-001:sequence`, then
    `:sequence.2` for a second one), so a missing diagram and the file that later replaces it are the same artifact."""
    if item.kind.endswith(" diagram"):
        n = re.search(r"\.(\d+)\.puml$", item.file or "")
        return f"{item.ucs[0]}:{item.kind.split()[0]}" + (f".{n.group(1)}" if n else "")
    return item.id


def read_registry(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2).strip()) for m in ROW.finditer(text)]


def _kind_word(id_: str) -> str:
    return id_.rsplit("-", 1)[0]


def merge(existing: list[tuple[str, str]], items: Iterable[VItem]) -> list[tuple[str, str]]:
    """The existing rows, untouched, plus a new row for each artifact not registered yet."""
    rows = list(existing)
    known = {(_kind_word(i), a) for i, a in rows}
    top: dict[str, int] = {}
    for i, _ in rows:
        stem, n = i.rsplit("-", 1)
        top[stem] = max(top.get(stem, 0), int(n))
    wanted = {(p, alias_of(it)) for it in items if (p := prefix_of(it))}
    for prefix, alias in sorted(wanted - known, key=lambda w: (w[0], natural_key(w[1]))):
        top[prefix] = top.get(prefix, 0) + 1
        rows.append((f"{prefix}-{top[prefix]:03d}", alias))
    return rows


def render_rows(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return EMPTY
    return HEADER + "".join(f"| {i} | `{a}` | {i.rsplit('-', 1)[0]} |\n" for i, a in rows)


def current_rows(cfg: Config, ws: Workspace, doc: str | None = None) -> list[tuple[str, str]]:
    path = doc or registry_path(cfg)
    return read_registry(ws.read(path)) if ws.exists(path) else []


def render_registry(cfg: Config, ws: Workspace, doc: str) -> str:
    items, unplaced = build_v(cfg, ws)
    return render_rows(merge(current_rows(cfg, ws, doc), [*items, *unplaced]))


def refs_for(cfg: Config, ws: Workspace, items: list[VItem], unplaced: list[VItem]) -> dict[tuple[str, str], str]:
    """(phase, id) -> the standard id shown for every item, from the registry as `vbench sync` would extend it."""
    rows = merge(current_rows(cfg, ws), [*items, *unplaced])
    by_alias = {(_kind_word(i), a): i for i, a in rows}
    out: dict[tuple[str, str], str] = {}
    for it in [*items, *unplaced]:
        p = prefix_of(it)
        out[(it.phase, it.id)] = it.id if p is None else by_alias[(p, alias_of(it))]
    return out
