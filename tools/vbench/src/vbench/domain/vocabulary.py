"""The project's vocabulary: the terms of the requirements doc's "Vocabulary (ubiquitous language)" table, read as data.

    | Term | Definition | Context | Not to be confused with |

A term is named by its words, so there is no id to keep. The last column lists near-synonyms that mean something else;
`names_in_diagram` and `confusions` use it to catch a diagram that draws the wrong word. Existence, never meaning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..ports import Workspace
from .config import Config
from .requirements_doc import tables


@dataclass(frozen=True)
class Term:
    name: str
    definition: str
    context: str
    confusable: tuple[str, ...]  # words the table says this term is not


def slug_of(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _cell(row: list[str], col: dict[str, int], key: str) -> str:
    return row[col[key]].strip() if key in col and col[key] < len(row) else ""


def read_terms(cfg: Config, ws: Workspace) -> list[Term]:
    """The terms of the vocabulary table, in the order written. A row still holding a `(placeholder)` is skipped."""
    if not ws.exists(cfg.requirements):
        return []
    out: list[Term] = []
    for header, rows in tables(ws.read(cfg.requirements)):
        if not (header and header[0].startswith("term") and any(h.startswith("definition") for h in header)):
            continue
        col = {h.split()[0]: i for i, h in reversed(list(enumerate(header)))}
        for row in rows:
            name = _cell(row, col, "term").strip("*` ")
            if not name or name.startswith("(") or slug_of(name) in {t.name for t in out}:
                continue
            words = tuple(w.strip(" `*") for w in re.split(r"[,;]", _cell(row, col, "not")) if w.strip(" `*()"))
            out.append(Term(name, _cell(row, col, "definition"), _cell(row, col, "context"), words))
    return out


DECL = re.compile(
    r"^\s*(?:abstract\s+class|participant|actor|boundary|control|entity|database|collections|queue|class|interface|"
    r'enum|component)\s+("([^"]+)"|[\w.]+)',
    re.MULTILINE,
)


def _words(name: str) -> list[str]:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", name)
    return [w.lower() for w in re.split(r"[^A-Za-z0-9]+", spaced) if w]


def names_in_diagram(text: str) -> list[str]:
    """The names a PlantUML file declares (participants, classes, actors ...), without stereotypes or line breaks."""
    out = []
    for m in DECL.finditer(text):
        raw = m.group(2) or m.group(1)
        raw = re.sub(r"«[^»]*»|<<[^>]*>>", " ", raw.replace("\\n", " "))
        name = raw.strip()
        if name and name not in out:
            out.append(name)
    return out


def _singular(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def confusions(terms: list[Term], names: list[str]) -> list[tuple[str, str, str]]:
    """(drawn name, the word it contains, the term that word is not): a diagram name that uses a word the vocabulary
    says is not the project's term. A confusable word that is itself a defined term is a different concept: ignored."""
    defined = {_singular(w) for t in terms for w in _words(t.name)} | {slug_of(t.name) for t in terms}
    out = []
    for name in names:
        have = [_singular(w) for w in _words(name)]
        phrase = " ".join(have)
        for t in terms:
            for bad in t.confusable:
                b = " ".join(_singular(w) for w in _words(bad))
                if not b or b in defined or slug_of(bad) in defined:
                    continue
                if b == phrase or (" " not in b and b in have) or (" " in b and f" {b} " in f" {phrase} "):
                    out.append((name, bad, t.name))
    return out
