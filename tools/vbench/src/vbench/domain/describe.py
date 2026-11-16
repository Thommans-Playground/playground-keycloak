"""Plain-language explanations for things a person would otherwise only see by name: a code file, a test, a diagram,
a context. Pure text handling; the callers read the files."""

from __future__ import annotations

import ast
import re

TAG_LINE = re.compile(r"^\s*(Realises|Verifies|Spec:)\b", re.IGNORECASE)
TITLE = re.compile(r"^\s*title\s+(.+?)\s*$", re.MULTILINE)


def humanise(name: str) -> str:
    """`test_a_saved_note_has_an_id` -> `A saved note has an id`; `create.py` -> `Create`; `Class.test_x` -> `X`."""
    stem = name.split(".")[-1] if "::" not in name and name.count(".") > 1 else name
    stem = re.sub(r"\.(py|js|ts|tsx|puml|md)$", "", stem.rsplit("/", 1)[-1])
    stem = re.sub(r"^test_?", "", stem.rsplit(".", 1)[-1])
    words = re.sub(r"[_\-]+", " ", stem).strip()
    return words[:1].upper() + words[1:] if words else name


def first_line(doc: str | None) -> str:
    """The first line of a docstring that explains something: not blank, not a `Realises`/`Verifies` tag."""
    for line in (doc or "").splitlines():
        line = line.strip()
        if line and not TAG_LINE.match(line):
            return line.rstrip(".") if len(line) > 1 else line
    return ""


def module_summary(path: str, text: str) -> str:
    """What a code file says about itself: the first explaining line of its module docstring (Python) or leading
    comment, or nothing when it says nothing."""
    if path.endswith(".py"):
        try:
            return first_line(ast.get_docstring(ast.parse(text)))
        except SyntaxError:
            return ""
    for line in text.splitlines()[:12]:
        stripped = line.strip().lstrip("/#*-").strip()
        if stripped and not TAG_LINE.match(stripped) and line.strip().startswith(("//", "#", "/*", "*")):
            return stripped
    return ""


def diagram_title(text: str) -> str:
    """The `title` line of a PlantUML diagram, if it has one."""
    m = TITLE.search(text)
    return m.group(1).strip() if m else ""
