"""Use case: the whole project state as plain data, for a UI or any other reader.

It applies no rules of its own. Every field comes from the same domain functions the CLI uses, so a dashboard and
`vbench status` cannot disagree.
"""

from __future__ import annotations

import posixpath
import re
from typing import Any

from ..domain.briefs import read_briefs
from ..domain.checks import (
    KINDS,
    collect_declared,
    collect_realised,
    collect_referenced,
    collect_unspecified,
    collect_verified,
)
from ..domain.config import Config
from ..domain.contexts import CONTEXT_FILE, CONTEXT_MAP, USECASE_MAP
from ..domain.describe import diagram_title
from ..domain.graph import enables, read_links, to_mermaid
from ..domain.model import natural_key
from ..domain.next import next_step
from ..domain.registry import refs_for
from ..domain.requirements_doc import RequirementsDoc, read_criteria, read_requirements
from ..domain.specs import read_specs
from ..domain.status import derive_status
from ..domain.vview import PHASES, RUNGS, VItem, build_v
from ..ports import Repo, Workspace

H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def _title(text: str, fallback: str) -> str:
    m = H1.search(text)
    return m.group(1) if m else fallback


def _diagram_kind(cfg: Config, path: str) -> dict[str, Any]:
    name = posixpath.basename(path)
    if name == USECASE_MAP:
        return {"kind": "use-case map", "generated": True}
    if name == CONTEXT_MAP:
        return {"kind": "context map", "generated": False}
    for kind in KINDS:
        if re.search(rf"-{kind}(\.\d+)?\.puml$", name):
            uc = cfg.uc_re.match(name)
            return {"kind": kind, "uc": uc.group(0) if uc else None, "generated": False}
    if CONTEXT_FILE.match(name):
        return {"kind": "context model", "generated": False}
    return {"kind": "diagram", "generated": False}


def _item(i: VItem, refs: dict[tuple[str, str], str]) -> dict[str, Any]:
    return {
        "id": i.id,
        "ref": refs[(i.phase, i.id)],
        "phase": i.phase,
        "kind": i.kind,
        "title": i.title,
        "ucs": list(i.ucs),
        "file": i.file,
        "line": i.line,
        "status": i.status,
        "label": i.label,
        "acs": list(i.acs),
        "description": i.description,
    }


def _sheet(
    doc: RequirementsDoc,
    items: list[VItem],
    refs: dict[tuple[str, str], str],
    use_cases: list[dict[str, Any]],
    criteria: list[dict[str, Any]],
) -> dict[str, Any]:
    """The requirements read as one sheet: the problem, each request, and each requirement with what is related to it:
    the use cases that realise it, the criteria that satisfy it and the tests that prove them."""
    by_item = {i.id: i for i in items if i.phase == "requirements"}
    titles = {u["id"]: u["title"] for u in use_cases}
    tests = [i for i in items if i.kind == "test"]

    def about(rid: str) -> dict[str, Any]:
        item = by_item.get(rid)
        mine = [c for c in criteria if rid in c["satisfies"]]
        return {
            "status": item.status if item else "neutral",
            "label": item.label if item else "",
            "ucs": [{"id": u, "title": titles.get(u, "")} for u in (item.ucs if item else ())],
            "criteria": [
                {
                    "id": c["id"],
                    "uc": c["uc"],
                    "text": c["text"],
                    "state": c["state"],
                    "tests": [
                        {"ref": refs[(t.phase, t.id)], "id": t.id, "phase": t.phase, "title": t.description or t.title}
                        for t in tests
                        if c["id"] in t.acs
                    ],
                }
                for c in mine
            ],
        }

    return {
        "problems": [
            {
                "id": p.id,
                "text": p.text,
                "who": p.who,
                "cost": p.cost,
                "status": by_item[p.id].status if p.id in by_item else "neutral",
                "label": by_item[p.id].label if p.id in by_item else "",
                "requests": [r.id for r in doc.requests if p.id and p.id in r.problems],
            }
            for p in doc.problems
        ],
        "requests": [
            {
                "id": r.id,
                "raisedBy": r.raised_by,
                "text": r.text,
                "problems": list(r.problems),
                "requirements": [x.id for x in (*doc.functional, *doc.quality) if r.id in x.satisfies],
            }
            for r in doc.requests
        ],
        "functional": [
            {"id": f.id, "text": f.text, "story": f.story, "satisfies": list(f.satisfies), **about(f.id)}
            for f in doc.functional
        ],
        "quality": [
            {
                "id": q.id,
                "quality": q.quality,
                "outline": q.outline,
                "source": q.source,
                "stimulus": q.stimulus,
                "artifact": q.artifact,
                "environment": q.environment,
                "response": q.response,
                "measure": q.measure,
                "satisfies": list(q.satisfies),
                "evidence": q.evidence,
                **about(q.id),
            }
            for q in doc.quality
        ],
    }


def _v_view(
    items: list[VItem],
    unplaced: list[VItem],
    use_cases: list[dict[str, Any]],
    criteria: list[dict[str, Any]],
    gates: list[dict[str, Any]],
    refs: dict[tuple[str, str], str],
) -> dict[str, Any]:
    """The logical view: nine phases with their items, and the headline numbers for the dashboard."""
    reqs = [i for i in items if i.phase == "requirements" and i.kind in ("FR", "NFR")]
    enforced = [c for c in criteria if c["state"] != "planned"]
    return {
        "phases": [{"key": k, "label": label, "arm": arm, "pairs": pair} for k, label, arm, pair in PHASES],
        "items": [_item(i, refs) for i in items],
        "unplaced": [_item(i, refs) for i in unplaced],
        "stats": {
            "useCases": {"built": sum(u["stage"] == "verify" for u in use_cases), "total": len(use_cases)},
            "criteria": {"covered": sum(c["state"] == "covered" for c in enforced), "total": len(enforced)},
            "tasks": {"closed": sum(u["tasksClosed"] for u in use_cases), "total": sum(u["tasks"] for u in use_cases)},
            "requirements": {"realised": sum(bool(i.ucs) for i in reqs), "total": len(reqs)},
            "tests": {**{r: sum(i.phase == r for i in items) for r in RUNGS}, "unplaced": len(unplaced)},
            "gates": {"passing": sum(g["ok"] for g in gates), "total": len(gates)},
        },
    }


def export_state(cfg: Config, ws: Workspace, repo: Repo) -> dict[str, Any]:
    report = derive_status(cfg, ws)
    nxt = next_step(report.rows, read_briefs(cfg, ws))
    deps = read_links(cfg, ws)
    back = enables(deps)
    specs = {s.uc: s for s in read_specs(cfg, ws)}
    by_path = {s.path: s.uc for s in specs.values()}

    use_cases = []
    for r in report.rows:
        s = specs[r.uc]
        use_cases.append(
            {
                "id": r.uc,
                "title": s.title,
                "path": s.path,
                "actor": s.actor,
                "context": s.context,
                "rigor": s.rigor,
                "wave": r.wave,
                "stage": r.stage,
                "task": r.task,
                "next": r.next,
                "blockedBy": list(r.blocked_by),
                "dependsOn": deps.get(r.uc, []),
                "enables": sorted(back.get(r.uc, []), key=natural_key),
                "acs": r.acs,
                "covered": r.covered,
                "enforced": r.enforced,
                "tasks": r.tasks,
                "tasksClosed": r.tasks_closed,
                "code": r.code,
                "tested": r.tested,
            }
        )

    declared, planned = collect_declared(cfg, ws)
    details = read_criteria(cfg, ws)
    referenced, unspecified = collect_referenced(cfg, ws), collect_unspecified(cfg, ws)
    criteria = []
    for ac in sorted(declared, key=natural_key):
        state = (
            "tbd"
            if ac in unspecified
            else "planned"
            if ac in planned
            else "covered"
            if ac in referenced
            else "uncovered"
        )
        uc = by_path.get(declared.get(ac, ""))
        detail = details.get(ac)
        criteria.append(
            {
                "id": ac,
                "uc": uc,
                "spec": declared[ac],
                "state": state,
                "tests": sorted(referenced.get(ac, [])),
                "text": detail.text if detail else "",
                "satisfies": list(detail.satisfies) if detail else [],
            }
        )

    realised, verified = collect_realised(cfg, ws), collect_verified(cfg, ws)
    rungs = [
        {
            "uc": u,
            "realisedIn": sorted(realised[u]),
            "verifiedBy": [{"file": f, "rung": rung} for f, rung in sorted(verified.get(u, []))],
        }
        for u in sorted(realised, key=natural_key)
    ]

    docs = [
        {"path": p, "title": _title(ws.read(p), posixpath.basename(p))}
        for p in ws.files([cfg.docs], [".md"])
        if "/usecase-diagrams/" not in p or not posixpath.basename(p).startswith("_")
    ]
    diagrams = [
        {"path": p, "title": diagram_title(ws.read(p)), **_diagram_kind(cfg, p)}
        for p in ws.files([cfg.docs], [".puml"])
        if not posixpath.basename(p).startswith("_")
    ]

    gates = [{"name": g.name, "ok": g.ok, "lines": g.lines} for g in report.gates]
    v_items, v_unplaced = build_v(cfg, ws)
    refs = refs_for(cfg, ws, v_items, v_unplaced)
    return {
        "branch": repo.branch(),
        "next": {
            "command": nxt.command,
            "uc": nxt.uc,
            "why": nxt.why,
            "purpose": nxt.purpose,
            "blocked": {u: list(w) for u, w in nxt.blocked},
        },
        "gates": gates,
        "v": _v_view(v_items, v_unplaced, use_cases, criteria, gates, refs),
        "requirements": _sheet(read_requirements(cfg, ws), v_items + v_unplaced, refs, use_cases, criteria),
        "useCases": use_cases,
        "criteria": criteria,
        "rungs": rungs,
        "orphans": report.orphans,
        "docs": docs,
        "diagrams": diagrams,
        "graph": to_mermaid(deps) if deps else "",
    }
