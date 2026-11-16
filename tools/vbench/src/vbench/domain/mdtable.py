"""Reading and editing one row of a markdown table, leaving everything around it as it was.

A table is found by its header (a predicate over the lower-cased header cells), a row by the id in its first cell
(`**REQ-FR-001**`). Cells hold one line each: a newline becomes a space and a `|` is escaped, so a value can never
break the table. Columns are named by their header text, exactly or by its start, so a table that gained a column
since a doc was written still edits correctly.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

SEPARATOR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
Header = Callable[[list[str]], bool]


class TableError(Exception):
    """The table or the row is not there, or the column does not exist."""


@dataclass(frozen=True)
class Table:
    header: list[str]  # lower-cased
    head_line: int
    rows: list[tuple[int, list[str]]]  # (line index, cells)

    @property
    def last_line(self) -> int:
        return self.rows[-1][0] if self.rows else self.head_line + 1


def split_cells(line: str) -> list[str]:
    """The cells of a table row, on the pipes that are not escaped."""
    inner = line.strip()
    inner = inner[1:] if inner.startswith("|") else inner
    inner = inner[:-1] if inner.endswith("|") and not inner.endswith("\\|") else inner
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", inner)]


def cell_text(value: object) -> str:
    """A value as one safe table cell."""
    return re.sub(r"\s+", " ", str(value)).strip().replace("|", "\\|")


def row_id(cells: list[str]) -> str:
    return cells[0].strip().strip("*").strip() if cells else ""


def tables(text: str) -> list[Table]:
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and SEPARATOR.match(lines[i + 1]):
            head, rows, j = i, [], i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append((j, split_cells(lines[j])))
                j += 1
            out.append(Table([c.lower() for c in split_cells(lines[head])], head, rows))
            i = j
        else:
            i += 1
    return out


def locate(text: str, wants: Header) -> Table:
    for t in tables(text):
        if wants(t.header):
            return t
    raise TableError("the table is not in the document")


def column(header: list[str], name: str) -> int:
    """The index of the column called `name`: an exact match on the header text first, then a match on its start."""
    for i, h in enumerate(header):
        if h == name:
            return i
    for i, h in enumerate(header):
        if h.startswith(name):
            return i
    raise TableError(f"the table has no `{name}` column")


def _placeholder(cells: list[str]) -> bool:
    return "nnn" in row_id(cells) or (len(cells) > 1 and cells[1].startswith("("))


def _render(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def row_values(text: str, wants: Header, id_: str) -> dict[str, str] | None:
    """The cells of the row `id_`, keyed by lower-cased header text, or None when the row is not there."""
    t = locate(text, wants)
    for _, cells in t.rows:
        if row_id(cells) == id_:
            return dict(zip(t.header, cells, strict=False))
    return None


def upsert_row(text: str, wants: Header, id_: str, values: dict[str, str]) -> str:
    """Set the named cells of the row `id_`, or add the row (replacing the template's placeholder row when that is
    all the table holds). Columns not named keep what they had."""
    t = locate(text, wants)
    lines = text.split("\n")
    index = {k: column(t.header, k) for k in values}
    for line_no, cells in t.rows:
        if row_id(cells) == id_:
            cells = cells + [""] * (len(t.header) - len(cells))
            for k, v in values.items():
                cells[index[k]] = cell_text(v)
            lines[line_no] = _render(cells)
            return "\n".join(lines)
    cells = [""] * len(t.header)
    cells[0] = f"**{id_}**"
    for k, v in values.items():
        cells[index[k]] = cell_text(v)
    fresh = _render(cells)
    if len(t.rows) == 1 and _placeholder(t.rows[0][1]):
        lines[t.rows[0][0]] = fresh
    else:
        lines.insert(t.last_line + 1, fresh)
    return "\n".join(lines)


def delete_row(text: str, wants: Header, id_: str) -> str:
    t = locate(text, wants)
    lines = text.split("\n")
    for line_no, cells in t.rows:
        if row_id(cells) == id_:
            del lines[line_no]
            return "\n".join(lines)
    raise TableError(f"{id_} is not in the table")
