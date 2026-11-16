"""The single next action. Pure: it reads the derived rows and applies the rule, nothing else."""

from __future__ import annotations

from collections.abc import Sequence

from .briefs import Brief
from .model import NextStep, UcRow
from .status import BUILT, command_for

WHY = {
    "requirements": "{uc} has no acceptance criteria written yet (its rows still say TBD).",
    "design": (
        "{uc}'s design is incomplete: it needs a task that names a criterion, every diagram it requires "
        "(its tier's, and a state diagram when it has a lifecycle) and, at the full tier, a Lifecycle decision."
    ),
    "code": ("{task} has acceptance criteria with no marked test ({covered}/{enforced} of the use case covered)."),
    "rung": "{uc}: every task is closed, but no code is tagged Realises or no test is tagged Verifies.",
    "verify": "{uc} is built; it needs the independent re-check.",
}

# One line on why each step exists, for someone new to the method. Plain words, no jargon.
PURPOSE = {
    "discovery": "Agreeing the scope first stops you building the wrong thing.",
    "requirements": "Acceptance criteria are the contract that every later test and review is checked against.",
    "design": "Deciding the structure and the tests up front keeps the code small and the tests honest.",
    "code": "Writing the test first proves it can fail, so a pass means something.",
    "rung": "Tags tell the checks which code and tests belong to which use case.",
    "verify": "A second, independent look catches what the author has stopped seeing.",
    "ship": "Every use case is proved and reviewed together before it is merged.",
}


def next_step(rows: list[UcRow], briefs: Sequence[Brief] = ()) -> NextStep:
    """Work the lowest wave first. A use case waits until everything it depends on is built."""
    if not rows:
        approved = [b for b in briefs if b.status == "approved"]
        drafts = [b for b in briefs if b.status != "approved"]
        if approved:
            b = approved[0]
            return NextStep(
                f"/vbench:v-1-requirements {b.path}",
                None,
                f'The discovery brief "{b.title}" is approved but not yet turned into requirements.',
                purpose=PURPOSE["requirements"],
            )
        if drafts:
            b = drafts[0]
            return NextStep(
                f"/vbench:discovery {b.path}",
                None,
                f'The discovery brief "{b.title}" is still a draft. Finish it with the agent, then set its Status '
                "to approved.",
                purpose=PURPOSE["discovery"],
            )
        return NextStep(
            "/vbench:discovery",
            None,
            "There are no use cases and no discovery brief yet. Start by agreeing the scope.",
            purpose=PURPOSE["discovery"],
        )
    unbuilt = [r for r in rows if r.stage != BUILT]
    blocked = tuple((r.uc, r.blocked_by) for r in unbuilt if r.blocked_by)
    if not unbuilt:
        return NextStep(
            "/vbench:v-4-verify all",
            None,
            f"All {len(rows)} use case(s) are built. Verify them, then `/vbench:v-5-ship`.",
            purpose=PURPOSE["ship"],
        )
    ready = [r for r in unbuilt if not r.blocked_by]  # rows arrive ordered by (wave, id)
    if not ready:
        return NextStep(None, None, "Every remaining use case is blocked. Run `vbench check links`.", blocked)
    return _step_for(ready[0], blocked)


def _step_for(r: UcRow, blocked: tuple[tuple[str, tuple[str, ...]], ...] = ()) -> NextStep:
    why = WHY[r.stage].format(uc=r.uc, task=r.task, covered=r.covered, enforced=r.enforced)
    return NextStep(command_for(r.uc, r.stage, r.task), r.uc, f"{why} (wave {r.wave})", blocked, PURPOSE[r.stage])


def ready_steps(rows: list[UcRow], briefs: Sequence[Brief] = ()) -> list[NextStep]:
    """Every step that can start now: all unbuilt use cases whose dependencies are built, in (wave, id) order. Work on
    them is independent, so several people or agents can take one each. Where `next_step` has a single answer that
    is not a use case (discovery, verify all, everything blocked), that one step is the list."""
    unbuilt = [r for r in rows if r.stage != BUILT]
    ready = [r for r in unbuilt if not r.blocked_by]
    if not rows or not ready:
        return [next_step(rows, briefs)]
    blocked = tuple((r.uc, r.blocked_by) for r in unbuilt if r.blocked_by)
    return [_step_for(r, blocked) for r in ready]
