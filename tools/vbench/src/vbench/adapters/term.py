"""Terminal styling for the human-readable output: colour, bold, dim, italic, underline and strikethrough.

The printers ask for a *role* (`ok`, `fail`, `command`, ...) and never write an escape code themselves, so the look
lives in one table and a later theme changes one place. Meaning never rests on style alone: a failure still prints
`FAIL` and a planned step still prints `(planned)`, so output with the styles stripped (a pipe, `NO_COLOR`, CI logs,
`--json`, a terminal that ignores an attribute) says exactly the same thing.

Only the driving adapter (`cli.py`) uses this. The domain and the use cases return text and values.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TextIO

MODES = ("auto", "always", "never")

# role -> SGR parameters. 1 bold, 2 dim, 3 italic, 4 underline, 9 strikethrough; 31 red, 32 green, 33 yellow, 36 cyan.
ROLES = {
    "ok": "32",
    "fail": "1;31",
    "warn": "33",
    "muted": "2",
    "heading": "1",
    "command": "1;36",
    "id": "36",
    "path": "4",
    "reason": "3",
    "planned": "2;9",
}

_MARK = re.compile(
    r"(?P<path>(?<![\w/.-])(?:[\w.-]+/)+[\w.-]+\.\w+(?::\d+)?)"  # docs/x/UC-A-001-y.md, src/a.py:27
    r"|(?P<id>\b[A-Z]{2,4}-[A-Z]{1,5}-\d{3}\b)"  # UC-A-001, STP-N-002, REQ-FR-001
)


def wants_color(mode: str, stream: TextIO, env: Mapping[str, str] | None = None) -> bool:
    """`always` and `never` are absolute. `auto` follows the NO_COLOR / FORCE_COLOR conventions, then asks whether the
    stream is a terminal (so a pipe, a file and a CI log stay plain)."""
    env = os.environ if env is None else env
    if mode == "always":
        return True
    if mode == "never":
        return False
    if env.get("NO_COLOR"):
        return False
    force = env.get("FORCE_COLOR")
    if force:
        return force != "0"
    if env.get("TERM") == "dumb":
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(isatty and isatty())


@dataclass(frozen=True)
class Style:
    on: bool = False

    def __call__(self, role: str, text: str) -> str:
        """`text` in the style of `role`; the text itself when styling is off."""
        return f"\033[{ROLES[role]}m{text}\033[0m" if self.on and text else text

    def mark(self, line: str) -> str:
        """Underline the file paths in a line and colour the ids, leaving everything else as it was."""
        if not self.on:
            return line
        return _MARK.sub(lambda m: self("path" if m.group("path") else "id", m.group(0)), line)

    def result(self, ok: bool, lines: list[str]) -> list[str]:
        """A gate's lines. A pass gets its name in green; a failure gets its heading in bold red and the details
        marked, so the eye lands on what to fix."""
        if not self.on:
            return lines
        if ok:
            return [re.sub(r"^(\w+:)", lambda m: self("ok", m.group(1)), line, count=1) for line in lines]
        out, heading_done = [], False
        for line in lines:
            if not heading_done and line.strip():
                out.append(self("fail", line))
                heading_done = True
            else:
                out.append(self.mark(line))
        return out

    def trace(self, lines: list[str]) -> list[str]:
        """The reading tour: the step id and message stand out, a planned step is struck through, the field names
        recede, and an empty or docstring-only field is flagged."""
        if not self.on:
            return lines
        out = []
        planned = False
        for line in lines:
            if line.startswith("STP-"):
                planned = line.rstrip().endswith("(planned)")
                sid, _, rest = line.partition("  ")
                out.append(self("id", sid) + "  " + (self("planned", rest) if planned else self("heading", rest)))
                continue
            m = re.match(r"^(\s+)(diagram|task|code|test)(\s+)(.*)$", line)
            if m:
                lead, field_, gap, value = m.groups()
                value = self("muted" if planned else "warn", value) if value.startswith("-") else self.mark(value)
                out.append(lead + self("muted", field_) + gap + value)
            elif re.match(r"^UC-\S+:", line):
                out.append(self("heading", line))
            else:
                out.append(line)
        return out
