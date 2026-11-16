"""Steps: the numbered messages of a use case's sequence diagram, as ids the code can carry.

A sequence diagram says, message by message, how a use case works. Giving each message an id (`STP-N-002`) turns
the diagram into the use case's table of contents: a task cites the steps it builds, the code that realises a step
says so (`Realises UC-N-001 · STP-N-002`), and the test that drives it says so too (`Verifies UC-N-001 · STP-N-002 ·
unit rung.`). `vbench trace` then reads the chain back out of the code, so nothing is kept by hand.

This module is pure parsing and values; `checks.check_steps` gathers the project's files and judges.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import Config

PLANNED = "(planned)"
ARROW = re.compile(r"-+>+|<-+|\.+>+|<\.+")


@dataclass(frozen=True)
class Step:
    id: str
    uc: str
    path: str  # the diagram
    line: int
    label: str  # the message, without the id
    planned: bool = False  # marked `(planned)` in the diagram: not built yet, so no code or test is owed


@dataclass
class StepRow:
    """One step with everything the project says about it."""

    step: Step
    tasks: list[str] = field(default_factory=list)
    code: list[tuple[str, int]] = field(default_factory=list)  # (file, line) of a `Realises … STP-…` tag
    tests: list[str] = field(default_factory=list)  # test files with a real test behind the tag
    hollow: list[str] = field(default_factory=list)  # test files that say it with no real test behind


def label_of(line: str, step_id: str) -> str:
    """The message text of a diagram line: what follows the id, or the text after the colon when the id leads."""
    after = line.split(step_id, 1)[1] if step_id in line else line
    text = after.strip(" \t:[]*-")
    return re.sub(r"\s+", " ", text.replace(PLANNED, "")).strip()


def declared(cfg: Config, uc: str, path: str, text: str) -> list[Step]:
    """Step ids written in a sequence diagram, in drawing order. An id repeated in one diagram (a call and its
    return, the arms of an `alt`) is one step, declared where it first appears."""
    seen: dict[str, Step] = {}
    for n, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("'") or not stripped:
            continue  # a PlantUML comment
        for sid in cfg.step_re.findall(line):
            if sid not in seen:
                seen[sid] = Step(sid, uc, path, n, label_of(line, sid), PLANNED in line.lower())
    return list(seen.values())


def cited(cfg: Config, clause: str) -> tuple[list[str], list[str]]:
    """(use-case ids, step ids) written in the text after `Realises` / `Verifies`."""
    return cfg.uc_re.findall(clause), cfg.step_re.findall(clause)


def render_tour(uc: str, rows: list[StepRow]) -> list[str]:
    """A use case's steps in diagram order, each with its task, its code and its test: the reading order."""
    if not rows:
        return [f"{uc}: no step ids in its sequence diagram yet (add `STP-<area>-<nnn>` to each message)."]
    out = [f"{uc}: {len(rows)} step(s), in diagram order", ""]
    for r in rows:
        s = r.step
        mark = "  (planned)" if s.planned else ""
        out.append(f"{s.id}  {s.label}{mark}")
        out.append(f"    diagram  {s.path}:{s.line}")
        out.append(f"    task     {', '.join(r.tasks) or '-'}")
        out.append(f"    code     {', '.join(f'{p}:{n}' for p, n in r.code) or '-'}")
        tests = ", ".join(r.tests)
        if not tests:
            tests = "- (docstring only: " + ", ".join(r.hollow) + ")" if r.hollow else "-"
        out.append(f"    test     {tests}")
        out.append("")
    return out[:-1]
