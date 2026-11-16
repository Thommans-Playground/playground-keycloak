"""Values the core produces."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Result:
    name: str
    ok: bool
    lines: list[str] = field(default_factory=list)

    def render(self) -> str:
        return "\n".join(self.lines)


@dataclass(frozen=True)
class UcRow:
    uc: str
    acs: int
    covered: int
    enforced: int
    code: bool
    tested: bool
    next: str
    tasks: int = 0
    tasks_closed: int = 0
    wave: int = 0
    blocked_by: tuple[str, ...] = ()
    stage: str = ""  # requirements | design | code | rung | verify
    task: str | None = None  # the id of the first open task, while stage == code


@dataclass
class StatusReport:
    rows: list[UcRow]
    orphans: list[str]
    gates: list[Result]


def natural_key(s: str) -> list:
    """UC-C-010 sorts after UC-C-002: split into text and number runs."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


@dataclass(frozen=True)
class NextStep:
    command: str | None  # None when nothing can proceed
    uc: str | None
    why: str
    blocked: tuple[tuple[str, tuple[str, ...]], ...] = ()  # (uc, the unbuilt use cases it waits for)
    purpose: str = ""  # one line on why this step exists, for someone new to the method
