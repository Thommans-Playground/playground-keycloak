"""The requirements doc and the use-case specs, read as data: the problem, the requests, each functional
requirement with its user story, each quality requirement as a six-part scenario, and each acceptance criterion with
its Given/When/Then text. Tables are read by their header names, so a doc written before a column was added still
reads. Template placeholder rows, whose text starts with `(`, are skipped."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..ports import Workspace
from .config import Config
from .ids import FR_ID, NFR_ID, PROBLEM_ID, REQ_ID, REQUEST_ID
from .mdtable import split_cells

PROBLEM = re.compile(r"^##\s*0\.\s*Problems?(?: definition)?\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Problem:
    id: str  # empty for a problem written as a paragraph in a doc that predates the table
    text: str
    who: str
    cost: str


@dataclass(frozen=True)
class Request:
    id: str
    raised_by: str
    text: str
    problems: tuple[str, ...] = ()  # the problems this request addresses


@dataclass(frozen=True)
class FunctionalReq:
    id: str
    text: str
    story: str
    satisfies: tuple[str, ...]
    maturity: str


@dataclass(frozen=True)
class QualityReq:
    id: str
    quality: str
    outline: str
    source: str = ""
    stimulus: str = ""
    artifact: str = ""
    environment: str = ""
    response: str = ""
    measure: str = ""
    verify: str = ""
    evidence: str = ""
    satisfies: tuple[str, ...] = ()


@dataclass(frozen=True)
class Criterion:
    id: str
    text: str
    satisfies: tuple[str, ...]


@dataclass(frozen=True)
class RequirementsDoc:
    problems: tuple[Problem, ...]
    requests: tuple[Request, ...]
    functional: tuple[FunctionalReq, ...]
    quality: tuple[QualityReq, ...]


def _cells(line: str) -> list[str]:
    return split_cells(line)


def tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    """Every markdown table as (lower-cased header cells, body rows)."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header, rows, i = [c.lower() for c in _cells(lines[i])], [], i + 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            out.append((header, rows))
        else:
            i += 1
    return out


def _id(cell: str, pattern: str) -> str | None:
    m = re.fullmatch(rf"\*\*({pattern})\*\*|({pattern})", cell.strip())
    return (m.group(1) or m.group(2)) if m else None


def _col(header: list[str], row: list[str], *names: str) -> str:
    for name in names:
        for i, h in enumerate(header):
            if h.startswith(name) and i < len(row):
                return row[i].strip().strip('"')
    return ""


def _placeholder(*cells: str) -> bool:
    return any(c.startswith("(") for c in cells if c)


def read_paragraph(text: str) -> str:
    """A problem written as a plain paragraph under the heading, as docs did before there was a table."""
    m = PROBLEM.search(text)
    if not m:
        return ""
    body = re.split(r"^##\s", text[m.end() :], maxsplit=1, flags=re.MULTILINE)[0]
    lines = [ln.strip() for ln in body.splitlines() if ln.strip() and not ln.lstrip().startswith(("> ", "|", ">"))]
    para = " ".join(lines)
    return "" if para.startswith("(") else para


def read_requirements(cfg: Config, ws: Workspace) -> RequirementsDoc:
    if not ws.exists(cfg.requirements):
        return RequirementsDoc((), (), (), ())
    return parse_requirements(ws.read(cfg.requirements))


def parse_requirements(text: str) -> RequirementsDoc:
    problems: dict[str, Problem] = {}
    requests: dict[str, Request] = {}
    functional: dict[str, FunctionalReq] = {}
    outline: dict[str, QualityReq] = {}
    detail: dict[str, dict[str, str]] = {}
    for header, rows in tables(text):
        for row in rows:
            if "problem" in header and (rid := _id(row[0], PROBLEM_ID)):
                found = Problem(rid, _col(header, row, "problem"), _col(header, row, "who"), _col(header, row, "cost"))
                if not _placeholder(found.text):
                    problems.setdefault(rid, found)
            elif "raised by" in header and (rid := _id(row[0], REQUEST_ID)):
                addressed = tuple(dict.fromkeys(re.findall(PROBLEM_ID, _col(header, row, "problem"))))
                req = Request(rid, _col(header, row, "raised by"), _col(header, row, "the ask", "ask"), addressed)
                if not _placeholder(req.raised_by, req.text):
                    requests.setdefault(rid, req)
            elif "functional requirement" in header and (rid := _id(row[0], FR_ID)):
                body = _col(header, row, "functional requirement")
                if _placeholder(body):
                    continue
                satisfies = tuple(dict.fromkeys(REQ_ID.findall(_col(header, row, "satisfies"))))
                functional.setdefault(
                    rid,
                    FunctionalReq(rid, body, _col(header, row, "user story"), satisfies, _col(header, row, "maturity")),
                )
            elif "quality" in header and (rid := _id(row[0], NFR_ID)):
                quality = _col(header, row, "quality")
                if _placeholder(quality, *row[2:3]):
                    continue
                if "source" in header or "fit criterion" in header:
                    detail.setdefault(
                        rid,
                        {
                            "source": _col(header, row, "source"),
                            "stimulus": _col(header, row, "stimulus"),
                            "artifact": _col(header, row, "artifact"),
                            "environment": _col(header, row, "environment"),
                            "response": _col(header, row, "response") if "source" in header else "",
                            "measure": _col(header, row, "response measure", "fit criterion"),
                            "verify": _col(header, row, "how to verify"),
                        },
                    )
                else:
                    outline.setdefault(
                        rid,
                        QualityReq(
                            rid,
                            quality,
                            _col(header, row, "requirement"),
                            evidence=_col(header, row, "evidence"),
                            satisfies=tuple(dict.fromkeys(REQ_ID.findall(_col(header, row, "satisfies")))),
                        ),
                    )
    quality = []
    for rid in sorted({*outline, *detail}, key=lambda r: int(r.rsplit("-", 1)[1])):
        base = outline.get(rid, QualityReq(rid, "", ""))
        extra = detail.get(rid, {})
        quality.append(QualityReq(**{**base.__dict__, **{k: v for k, v in extra.items() if v}}))

    def natural(items):
        return tuple(sorted(items, key=lambda r: int(r.id.rsplit("-", 1)[1])))

    shown = natural(problems.values())
    if not shown and (para := read_paragraph(text)):
        shown = (Problem("", para, "", ""),)
    return RequirementsDoc(shown, natural(requests.values()), natural(functional.values()), tuple(quality))


def read_criteria(cfg: Config, ws: Workspace) -> dict[str, Criterion]:
    """Every acceptance criterion the specs declare, with its Given/When/Then text and the requirements it satisfies."""
    out: dict[str, Criterion] = {}
    for md in ws.files([cfg.specs], [".md"]):
        for m in cfg.ac_decl_re.finditer(ws.read(md)):
            cells = _cells(m.group(2))
            text = cells[0] if cells else ""
            out[m.group(1)] = Criterion(m.group(1), text, tuple(dict.fromkeys(REQ_ID.findall(" ".join(cells[1:])))))
    return out
