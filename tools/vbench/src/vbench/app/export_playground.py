"""Use case: the project state of a project written in the playground's own format, for the same UI.

It returns the shape `app/export.py` returns, so the dashboard draws the auth app without knowing which format it
came from. Every number is derived from the files: use case headers, the requirements and criteria tables, and the
tests that carry a criterion id. Nothing is stored and nothing is judged beyond "this criterion has a test".
"""

from __future__ import annotations

import ast
import posixpath
import re
from typing import Any

from ..domain.model import natural_key
from ..domain.playground import (
    LEVELS,
    Criterion,
    Requirement,
    TestFn,
    UseCase,
    comment_tags,
    parse_criteria,
    parse_requirements,
    parse_use_case,
    python_tests,
    title_of,
)
from ..domain.vview import PHASES
from ..ports import Repo, Workspace

USECASES = "docs/usecases"
REQUIREMENTS = "docs/requirements/requirements.md"
CRITERIA = "docs/requirements/acceptance-criteria.md"
DOCS = "docs"
CODE = ("apps/api/app",)
API_TESTS = "apps/api/tests"
WEB_TESTS = "apps/web/src"
CONTEXTS = "docs/domain/contexts"
ADRS = "docs/adr"
UC_IN_NAME = re.compile(r"^(UC-[A-Z]\d+)")

PURPOSE = (
    "Each use case is proved when every one of its acceptance criteria has a test. This is the one that is "
    "furthest from that."
)


def _why(far: dict[str, Any] | None) -> str:
    if far is None:
        return "Every use case is proved."
    if not far["enforced"]:
        return f"{far['id']} has no criteria yet, so nothing proves it."
    return f"{far['id']}: {far['covered']} of {far['enforced']} criteria have a test."


def _humanise(name: str) -> str:
    return re.sub(r"[-_]+", " ", re.sub(r"^(test_|\d+[-_])", "", name.rsplit(".", 1)[0])).strip().capitalize()


def _first_doc_line(text: str) -> str:
    try:
        doc = ast.get_docstring(ast.parse(text)) or ""
    except SyntaxError:
        return ""
    return doc.strip().splitlines()[0] if doc.strip() else ""


def _item(
    id: str,
    phase: str,
    kind: str,
    title: str,
    *,
    ucs=(),
    file=None,
    line=None,
    status="neutral",
    label="",
    acs=(),
    description="",
) -> dict[str, Any]:
    return {
        "id": id,
        "ref": id,
        "phase": phase,
        "kind": kind,
        "title": title,
        "ucs": sorted(set(ucs), key=natural_key),
        "file": file,
        "line": line,
        "status": status,
        "label": label,
        "acs": sorted(set(acs), key=natural_key),
        "description": description,
    }


def _folder_of(context: str) -> str:
    return context.removeprefix("BC-").lower()


def _read_tests(ws: Workspace, criteria: dict[str, Criterion]) -> list[TestFn]:
    out: list[TestFn] = []
    for path in ws.files([API_TESTS], [".py"]):
        out += python_tests(ws.read(path), path)
    for path in ws.files([WEB_TESTS], [".ts", ".tsx"]):
        if ".test." in posixpath.basename(path):
            acs = tuple(a for a in comment_tags(ws.read(path)) if a in criteria)
            out.append(TestFn(path, posixpath.basename(path), 1, acs, ""))
    return out


def _level(t: TestFn, criteria: dict[str, Criterion]) -> str:
    for ac in t.acs:
        lvl = criteria[ac].level if ac in criteria else ""
        if lvl in LEVELS:
            return lvl
        if lvl == "inspection":
            return "system"
    return "integration" if "/integration/" in t.file else "unit"


def export_playground_state(ws: Workspace, repo: Repo) -> dict[str, Any]:
    ucs = [u for p in ws.files([USECASES], [".md"]) if (u := parse_use_case(ws.read(p), p))]
    ucs.sort(key=lambda u: natural_key(u.id))
    reqs: list[Requirement] = parse_requirements(ws.read(REQUIREMENTS)) if ws.exists(REQUIREMENTS) else []
    all_criteria = parse_criteria(ws.read(CRITERIA)) if ws.exists(CRITERIA) else []
    live = {c.id: c for c in all_criteria if not c.retired}
    tests = _read_tests(ws, live)

    tested: dict[str, list[TestFn]] = {}
    for t in tests:
        for ac in t.acs:
            tested.setdefault(ac, []).append(t)
    uc_of: dict[str, str] = {}
    for u in ucs:
        for ac in u.criteria:
            uc_of.setdefault(ac, u.id)

    def test_id(t: TestFn) -> str:
        return f"{t.file}::{t.name}"

    def state(c: Criterion) -> str:
        return "covered" if c.id in tested else "planned" if c.deferred else "uncovered"

    criteria = [
        {
            "id": c.id,
            "uc": uc_of.get(c.id),
            "spec": CRITERIA,
            "state": state(c),
            "tests": sorted(test_id(t) for t in tested.get(c.id, [])),
            "text": c.text,
            "satisfies": list(c.proves),
        }
        for c in sorted(live.values(), key=lambda c: natural_key(c.id))
    ]
    by_ac = {c["id"]: c for c in criteria}

    # ---- use cases
    diagram_paths = ws.files([DOCS], [".puml"])
    use_cases = []
    for u in ucs:
        mine = [by_ac[a] for a in u.criteria if a in by_ac]
        enforced = [c for c in mine if c["state"] != "planned"]
        covered = [c for c in enforced if c["state"] == "covered"]
        designed = any(posixpath.basename(p).startswith(u.id) and "design" in p for p in diagram_paths)
        if not mine:
            stage = "requirements"
        elif enforced and len(covered) == len(enforced):
            stage = "verify"
        else:
            stage = "code" if designed else "design"
        use_cases.append(
            {
                "id": u.id, "title": u.name, "path": u.path, "actor": u.actor or None, "context": u.context or None,
                "rigor": "", "wave": 0, "stage": stage, "task": None, "next": "", "blockedBy": [], "dependsOn": [],
                "enables": [], "acs": len(mine), "covered": len(covered), "enforced": len(enforced), "tasks": 0,
                "tasksClosed": 0, "code": bool(covered), "tested": bool(covered),
            }
        )  # fmt: skip

    # ---- the V
    items: list[dict[str, Any]] = []
    served = {r.id: [u for u in ucs if r.id in u.satisfies] for r in reqs}

    def req_status(rid: str) -> tuple[str, str]:
        mine = [c for c in criteria if rid in c["satisfies"] and c["state"] != "planned"]
        done = [c for c in mine if c["state"] == "covered"]
        if not mine:
            return "neutral", "No criteria"
        if len(done) == len(mine):
            return "ok", "Proved"
        return ("warn", "Partly proved") if done else ("risk", "Not proved")

    for r in reqs:
        status, label = req_status(r.id)
        items.append(
            _item(
                r.id, "requirements", r.kind, r.name, ucs=[u.id for u in served[r.id]], file=REQUIREMENTS, status=status,
                label=label, acs=[c["id"] for c in criteria if r.id in c["satisfies"]], description=r.statement,
            )
        )  # fmt: skip

    def uc_in(path: str) -> list[str]:
        m = UC_IN_NAME.match(posixpath.basename(path))
        return [m.group(1)] if m else []

    for p in diagram_paths:
        name = posixpath.basename(p)
        if name.startswith("_"):
            continue
        title = title_of("", "") or _humanise(name)
        if "analysis" in name:
            items.append(
                _item(
                    p,
                    "system-design",
                    "diagram",
                    title,
                    ucs=uc_in(p),
                    file=p,
                    description="How the use case flows, step by step, before any design.",
                )
            )
        elif "design" in name:
            items.append(
                _item(
                    p,
                    "module-design",
                    "diagram",
                    title,
                    ucs=uc_in(p),
                    file=p,
                    description="How the use case is built: the ports, the adapters and the order of calls.",
                )
            )
    for p in ws.files([CONTEXTS], [".md"]):
        ctx = posixpath.basename(p).removesuffix(".md")
        items.append(
            _item(
                p,
                "architecture",
                "context",
                ctx,
                ucs=[u.id for u in ucs if u.context == ctx],
                file=p,
                description=title_of(ws.read(p), ctx),
            )
        )
    for p in ws.files([ADRS], [".md"]):
        if posixpath.basename(p).startswith(("0000", "README")):
            continue
        items.append(
            _item(
                p,
                "architecture",
                "decision",
                title_of(ws.read(p), _humanise(p)),
                file=p,
                description="A technical decision, with its reasons.",
            )
        )

    for base in CODE:
        for p in ws.files([base], [".py"]):
            if posixpath.basename(p) == "__init__.py":
                continue
            parts = p.removeprefix(base + "/").split("/")
            mine = [u.id for u in ucs if _folder_of(u.context) == parts[0]]
            items.append(
                _item(
                    p,
                    "code",
                    "module",
                    _humanise(posixpath.basename(p)),
                    ucs=mine,
                    file=p,
                    description=_first_doc_line(ws.read(p)),
                )
            )

    unplaced: list[dict[str, Any]] = []
    for t in tests:
        acs = [a for a in t.acs if a in live]
        owners = {uc_of[a] for a in acs if a in uc_of}
        phase = _level(t, live)
        title = t.docstring or _humanise(t.name)
        entry = _item(
            test_id(t), phase, "test", t.name, ucs=owners, file=t.file, line=t.line, acs=acs, description=title
        )
        (items if acs else unplaced).append(entry)

    # ---- requirements as a sheet
    titles = {u.id: u.name for u in ucs}

    def about(rid: str) -> dict[str, Any]:
        status, label = req_status(rid)
        return {
            "status": status,
            "label": label,
            "ucs": [{"id": u.id, "title": titles[u.id]} for u in served.get(rid, [])],
            "criteria": [
                {
                    "id": c["id"], "uc": c["uc"], "text": c["text"], "state": c["state"],
                    "tests": [
                        {"ref": test_id(t), "id": test_id(t), "phase": _level(t, live), "title": t.docstring or _humanise(t.name)}
                        for t in tested.get(c["id"], [])
                    ],
                }
                for c in criteria
                if rid in c["satisfies"]
            ],
        }  # fmt: skip

    sheet = {
        "problems": [],
        "requests": [],
        "functional": [
            {"id": r.id, "text": r.statement, "story": r.name, "satisfies": [], **about(r.id)} for r in reqs if r.kind == "FR"
        ],
        "quality": [
            {
                "id": r.id, "quality": r.quality, "outline": r.name, "source": "", "stimulus": r.stimulus, "artifact": "",
                "environment": r.environment, "response": r.response, "measure": r.measure, "satisfies": [],
                "evidence": "", **about(r.id),
            }
            for r in reqs
            if r.kind == "NFR"
        ],
    }  # fmt: skip

    # ---- gates and the next step
    no_criteria = [r.id for r in reqs if not any(r.id in c["satisfies"] for c in criteria)]
    no_test = [c["id"] for c in criteria if c["state"] == "uncovered"]
    no_design = [
        u["id"]
        for u in use_cases
        if not any(posixpath.basename(p).startswith(u["id"]) and "design" in p for p in diagram_paths)
    ]
    gates = [
        {"name": "requirements", "ok": not no_criteria, "lines": [f"no criterion proves {', '.join(no_criteria)}"] if no_criteria else []},
        {"name": "criteria", "ok": not no_test, "lines": [f"no test carries {', '.join(no_test)}"] if no_test else []},
        {"name": "design", "ok": not no_design, "lines": [f"no design diagram for {', '.join(no_design)}"] if no_design else []},
    ]  # fmt: skip
    open_ = [u for u in use_cases if u["stage"] != "verify"]
    far = min(open_, key=lambda u: (u["covered"] / u["enforced"]) if u["enforced"] else -1, default=None)
    nxt = {
        "command": None,
        "uc": far["id"] if far else None,
        "why": _why(far),
        "purpose": PURPOSE if far else "",
        "blocked": {},
    }

    reqs_done = [i for i in items if i["phase"] == "requirements" and i["ucs"]]
    enforced = [c for c in criteria if c["state"] != "planned"]
    stats = {
        "useCases": {"built": sum(u["stage"] == "verify" for u in use_cases), "total": len(use_cases)},
        "criteria": {"covered": sum(c["state"] == "covered" for c in enforced), "total": len(enforced)},
        "tasks": {"closed": 0, "total": 0},
        "requirements": {"realised": len(reqs_done), "total": sum(i["phase"] == "requirements" for i in items)},
        "tests": {**{r: sum(i["phase"] == r for i in items) for r in LEVELS}, "unplaced": len(unplaced)},
        "gates": {"passing": sum(g["ok"] for g in gates), "total": len(gates)},
    }

    docs = [{"path": p, "title": title_of(ws.read(p), posixpath.basename(p))} for p in ws.files([DOCS], [".md"])]
    diagrams = []
    for p in diagram_paths:
        name = posixpath.basename(p)
        if name.startswith("_"):
            continue
        kind = (
            "analysis sequence" if "analysis" in name else "design sequence" if "sequence" in name else "design" if "design" in name
            else "use case diagram" if "usecases" in name else "diagram"
        )  # fmt: skip
        uc = uc_in(p)
        diagrams.append(
            {"path": p, "title": _humanise(name), "kind": kind, "uc": uc[0] if uc else None, "generated": False}
        )

    rungs = [
        {
            "uc": u.id,
            "realisedIn": [],
            "verifiedBy": sorted({(t.file, _level(t, live)) for a in u.criteria for t in tested.get(a, [])}),
        }
        for u in ucs
    ]
    rungs = [{**r, "verifiedBy": [{"file": f, "rung": lvl} for f, lvl in r["verifiedBy"]]} for r in rungs]

    return {
        "branch": repo.branch(),
        "next": nxt,
        "gates": gates,
        "v": {
            "phases": [{"key": k, "label": label, "arm": arm, "pairs": pair} for k, label, arm, pair in PHASES],
            "items": items,
            "unplaced": unplaced,
            "stats": stats,
        },
        "requirements": sheet,
        "useCases": use_cases,
        "criteria": criteria,
        "rungs": rungs,
        "orphans": [],
        "docs": docs,
        "diagrams": diagrams,
        "graph": "",
    }


__all__ = ["UseCase", "export_playground_state"]
