"""The report card: one use case as a table of the V, the specification on the left and what proves it on the right.

    | Layer | Specification              | Verification                 |
    | --- | --- | --- |
    | 1 | ● Requirements  3 ACs        | ● Acceptance  3/3 covered    |
    | 2 | ● Design  ready              | ● Integration  not tracked   |
    | 3 | ● Tasks  2/2 closed          | ● Unit tests  yes            |
    | Code | ● Code  yes               |                              |

Every cell is a plain fact read from the status row, so the card says nothing the status table does not. Integration is
not tracked by the script yet, and the card says so instead of showing a colour it has not earned. Pure: no I/O; the
caller gives a `paint(tone, text)` to colour a piece (tones: ok, warn, fail, muted, id), and the default adds nothing.
"""

from __future__ import annotations

from collections.abc import Callable

from .model import UcRow

Paint = Callable[[str, str], str]


def _plain(tone: str, text: str) -> str:
    return text


# The shape says the state, so the card reads the same with colour off (a pipe, NO_COLOR, CI):
# finished, in progress, not started.
SHAPE = {"ok": "●", "warn": "◐", "muted": "○"}


def _dot(tone: str, paint: Paint) -> str:
    return paint(tone, SHAPE[tone])


def render_card(r: UcRow, paint: Paint = _plain) -> list[str]:
    started = r.stage != "requirements"
    designed = r.stage not in ("requirements", "design")
    tasks_done = r.tasks > 0 and r.tasks_closed == r.tasks
    proved = r.enforced > 0 and r.covered == r.enforced

    def tone(done: bool, partial: bool = False) -> str:
        return "ok" if done else "warn" if partial else "muted"

    #  (tone, label, fact) for each cell
    left = [
        (tone(started), "Requirements", f"{r.acs} AC{'' if r.acs == 1 else 's'}" if r.acs else "not written"),
        (tone(designed), "Design", "ready" if designed else "open" if started else "not started"),
        (tone(tasks_done, r.tasks_closed > 0), "Tasks", f"{r.tasks_closed}/{r.tasks} closed"),
    ]
    right = [
        (tone(proved, r.covered > 0), "Acceptance", f"{r.covered}/{r.enforced} covered"),
        ("muted", "Integration", "not tracked"),
        (tone(r.tested), "Unit tests", "yes" if r.tested else "no"),
    ]

    def cell(item: tuple[str, str, str]) -> str:
        t, label, fact = item
        return f"{_dot(t, paint)} {label}  {paint('muted', fact)}"

    code = (tone(r.code), "Code", "yes" if r.code else "no")
    lines = [
        f"{paint('id', r.uc)}   {paint('muted', 'next:')} {r.next}",
        "",
        "| Layer | Specification | Verification |",
        "| --- | --- | --- |",
    ]
    for i in range(3):
        lines.append(f"| {i + 1} | {cell(left[i])} | {cell(right[i])} |")
    lines.append(f"| Code | {cell(code)} | |")
    return lines
