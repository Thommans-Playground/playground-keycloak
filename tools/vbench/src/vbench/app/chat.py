"""Use case: ask the assistant about the project.

One question in, a stream of events out: `tool` (a read-only lookup is running), `token` (a piece of the answer). The
model may call the tools in `domain/chat.py` for up to `MAX_ROUNDS` rounds; each tool only reads the project's derived
state or one of its documents. Nothing is written, and a failure of the model surfaces as `AgentError` for the caller
to put in the stream.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterator
from typing import Any

from ..domain.chat import LABELS, MAX_ROUNDS, SYSTEM, TOOLS, framed_question, parse_request
from ..domain.config import Config
from ..domain.errors import AgentError
from ..ports import ChatModel, ToolCall, Workspace

FILE_LIMIT = 6000  # characters of a file handed to the model
RESULT_LIMIT = 12000  # characters of any tool result
WORD = re.compile(r"[a-z0-9]{3,}")


def _find(state: dict, key: str, ident: str) -> dict | None:
    return next((x for x in state.get(key, []) if x["id"] == ident), None)


def _item(state: dict, ident: str) -> dict | None:
    return next((i for i in state["v"]["items"] if ident in (i["id"], i["ref"])), None)


def _brief(i: dict) -> dict:
    return {k: i.get(k) for k in ("ref", "kind", "phase", "title", "description", "label", "ucs", "acs", "file")}


def _overview(state: dict, ws: Workspace, args: dict) -> dict:
    return {
        "next": state["next"],
        "gates": [{"name": g["name"], "passing": g["ok"]} for g in state["gates"]],
        "useCases": [
            {k: u[k] for k in ("id", "title", "stage", "wave", "next", "blockedBy", "covered", "enforced")}
            for u in state["useCases"]
        ],
    }


def _use_case(state: dict, ws: Workspace, args: dict) -> dict:
    u = _find(state, "useCases", str(args.get("id", "")))
    if not u:
        return {"error": f"No use case {args.get('id')!r}. Known: {[x['id'] for x in state['useCases']]}"}
    items = [_brief(i) for i in state["v"]["items"] if u["id"] in i["ucs"]]
    return {
        "useCase": u,
        "criteria": [c for c in state["criteria"] if c["uc"] == u["id"]],
        "items": items,
        "diagrams": [d for d in state["diagrams"] if d.get("uc") == u["id"]],
    }


def _get_item(state: dict, ws: Workspace, args: dict) -> dict:
    ident = str(args.get("id", ""))
    if i := _item(state, ident):
        return _brief(i) | {"line": i.get("line")}
    if c := next((c for c in state["criteria"] if c["id"] == ident), None):
        return {"criterion": c}
    if u := _find(state, "useCases", ident):
        return {"useCase": u}
    return {"error": f"Nothing is called {ident!r}."}


def _impact(state: dict, ws: Workspace, args: dict) -> dict:
    ident = str(args.get("id", ""))
    ucs: set[str] = set()
    criteria: list[dict] = []
    if u := _find(state, "useCases", ident):
        ucs = {u["id"], *u["enables"]}
        criteria = [c for c in state["criteria"] if c["uc"] in ucs]
    elif c := next((c for c in state["criteria"] if c["id"] == ident), None):
        criteria, ucs = [c], {c["uc"]} if c["uc"] else set()
    else:
        criteria = [c for c in state["criteria"] if ident in c.get("satisfies", [])]
        ucs = {c["uc"] for c in criteria if c["uc"]}
        if (i := _item(state, ident)) is not None:
            ucs |= set(i["ucs"])
            criteria += [c for c in state["criteria"] if c["id"] in i["acs"] and c not in criteria]
    ac_ids = {c["id"] for c in criteria}
    items = [
        _brief(i) for i in state["v"]["items"] if i["ref"] != ident and (ucs & set(i["ucs"]) or ac_ids & set(i["acs"]))
    ]
    return {
        "id": ident,
        "useCases": sorted(ucs),
        "criteria": [{k: c[k] for k in ("id", "uc", "state", "text")} for c in criteria],
        "items": items[:60],
        "note": "Derived from the project's links; review each before changing.",
    }


def _readable(state: dict) -> list[str]:
    paths = [d["path"] for d in state["docs"]] + [d["path"] for d in state["diagrams"]]
    return sorted({*paths, *(u["path"] for u in state["useCases"])})


def _read(state: dict, ws: Workspace, args: dict) -> dict:
    path = str(args.get("path", ""))
    if path not in _readable(state) or not ws.exists(path):
        return {"error": f"{path!r} is not a document of this project. Paths come from the other tools."}
    text = ws.read(path)
    return {"path": path, "text": text[:FILE_LIMIT], "truncated": len(text) > FILE_LIMIT}


def _search(state: dict, ws: Workspace, args: dict) -> dict:
    words = set(WORD.findall(str(args.get("query", "")).lower()))
    if not words:
        return {"error": "Give some words to search for."}
    hits = []
    for path in _readable(state)[:80]:
        if not ws.exists(path):
            continue
        text = ws.read(path)
        low = text.lower()
        score = sum(low.count(w) for w in words)
        if score:
            at = min((low.find(w) for w in words if w in low), default=0)
            hits.append({"path": path, "score": score, "snippet": text[max(0, at - 80) : at + 240].strip()})
    return {"matches": sorted(hits, key=lambda h: -h["score"])[:5]}


RUNNERS: dict[str, Callable[[dict, Workspace, dict], dict]] = {
    "project_overview": _overview,
    "get_use_case": _use_case,
    "get_item": _get_item,
    "impact": _impact,
    "read_file": _read,
    "search_docs": _search,
}


def run_tool(call: ToolCall, state: dict, ws: Workspace) -> str:
    runner = RUNNERS.get(call.name)
    if runner is None:
        return json.dumps({"error": f"There is no tool {call.name!r}."})
    try:
        out = json.dumps(runner(state, ws, call.arguments if isinstance(call.arguments, dict) else {}))
    except Exception as e:  # a bad lookup is a result the model can read, not a crash
        out = json.dumps({"error": f"{type(e).__name__}: {e}"})
    return out if len(out) <= RESULT_LIMIT else out[:RESULT_LIMIT] + '..."truncated"'


def stream_chat(
    model: ChatModel, cfg: Config, ws: Workspace, state_of: Callable[[], dict[str, Any]], raw: object
) -> Iterator[dict[str, Any]]:
    message, history, page, about = parse_request(raw)
    state = state_of()
    messages: list[dict] = [*history, {"role": "user", "content": framed_question(message, page, about)}]
    for round_ in range(MAX_ROUNDS + 1):
        calls: list[ToolCall] = []
        said = ""
        # On the last round no tools are offered, so it has to answer with what it found.
        for kind, value in model.turn(SYSTEM, messages, TOOLS if round_ < MAX_ROUNDS else []):
            if kind == "token":
                said += str(value)
                yield {"type": "token", "text": str(value)}
            elif kind == "calls":
                calls = list(value)  # type: ignore[arg-type]
        if not calls:
            return
        messages.append(
            {
                "role": "assistant",
                "content": said,
                "calls": [{"id": c.id, "name": c.name, "arguments": c.arguments} for c in calls],
            }
        )
        for c in calls:
            yield {"type": "tool", "name": c.name, "label": LABELS.get(c.name, c.name)}
            messages.append({"role": "tool", "id": c.id, "content": run_tool(c, state, ws)})
    raise AgentError("The assistant used all its lookups without answering; ask again more narrowly.")
