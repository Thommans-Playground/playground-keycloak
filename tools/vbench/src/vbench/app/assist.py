"""Use case: before adding something, ask whether it already exists.

The word-overlap check always runs and costs nothing. If an agent is set up, it is asked too, and its answer replaces
the baseline only when it is usable: it must be in the shape asked for and may name only entries it was shown. Any
failure of the agent (no key, refusal, a rate limit) leaves the baseline in place with a note saying why. Nothing is
written, and the agent sees only the new entry and the entries chosen to sit beside it.
"""

from __future__ import annotations

import json
from typing import Any

from ..domain.changes import parse_change
from ..domain.config import Config
from ..domain.errors import AgentError, UsageError
from ..domain.overlap import SCHEMA, SYSTEM, Answer, entries_of, parse_answer, question_data, rules_verdict, select
from ..domain.requirements_doc import parse_requirements
from ..ports import Agent, Workspace

TEXT_FIELDS = ("text", "story", "who", "cost", "quality", "outline", "measure")


def _json(answer: Answer, source: str, agent: str, note: str, compared: int) -> dict[str, Any]:
    return {
        "checked": True,
        "source": source,
        "agent": agent,
        "note": note,
        "compared": compared,
        "verdict": answer.verdict,
        "advice": answer.advice,
        "matches": [
            {"id": m.id, "kind": m.kind, "text": m.text, "why": m.why, "score": m.score} for m in answer.matches
        ],
    }


def check_overlap(cfg: Config, ws: Workspace, agent: Agent | None, raw: object) -> dict[str, Any]:
    change = parse_change(raw)
    if change.op != "add":
        return {"checked": False}
    fields = change.fields
    if not any(fields.get(k) for k in ("text", "quality", "outline")):
        raise UsageError("Write the entry first, then check it.")
    text = " ".join(str(fields[k]) for k in TEXT_FIELDS if fields.get(k))
    doc = parse_requirements(ws.read(cfg.requirements) if ws.exists(cfg.requirements) else "")
    entries = entries_of(doc)
    linked = [i for k in ("problems", "satisfies") if isinstance(fields.get(k), list) for i in fields[k]]
    chosen = select(entries, text, linked)
    baseline = rules_verdict(chosen)
    if agent is None:
        note = (
            "No agent is set up, so this is a word-overlap check. "
            "Start with --agent claude for an agent to reason about it."
        )
        return _json(baseline, "rules", "", note, len(chosen))
    try:
        answer = parse_answer(
            agent.structured(
                SYSTEM, json.dumps(question_data(change.kind, fields, chosen, linked), ensure_ascii=False), SCHEMA
            ),
            {e.id: e for e, _ in chosen},
        )
    except AgentError as e:
        return _json(
            baseline,
            "rules",
            agent.name,
            f"{str(e).rstrip('.')[:1].upper()}{str(e).rstrip('.')[1:]}. Showing the word-overlap check instead.",
            len(chosen),
        )
    return _json(answer, "agent", agent.name, "", len(chosen))
