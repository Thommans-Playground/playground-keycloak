"""The trace: what comes from what, from a problem down to a test, as a graph that can be walked up or down.

    problem <- request <- requirement <- use case <- criterion <- test
                              ^-------------------------'

A requirement satisfies requests; a use case realises requirements; a criterion belongs to a use case and satisfies
requirements; a test proves criteria. Every arrow is an id written in a document or a tag, so the graph is derived,
never stored. `up` goes toward the problem, `down` toward the tests.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from ..ports import Workspace
from .checks import collect_declared
from .config import Config
from .requirements_doc import RequirementsDoc, parse_requirements, read_criteria
from .specs import read_specs
from .vview import build_v


@dataclass(frozen=True)
class Trace:
    parents: dict[str, tuple[str, ...]]  # id -> the ids it comes from
    kinds: dict[str, str]  # id -> problem | request | requirement | usecase | criterion | test
    labels: dict[str, str]  # id -> a short name, for listing it

    def children(self, id_: str) -> list[str]:
        return [c for c, ps in self.parents.items() if id_ in ps]

    def _walk(self, start: str, step) -> list[tuple[str, int]]:
        seen, out, queue = {start}, [], deque([(start, 0)])
        while queue:
            node, depth = queue.popleft()
            for nxt in step(node):
                if nxt not in seen:
                    seen.add(nxt)
                    out.append((nxt, depth + 1))
                    queue.append((nxt, depth + 1))
        return out

    def up(self, id_: str) -> list[tuple[str, int]]:
        """Everything above it, nearest first, with the number of steps."""
        return self._walk(id_, lambda n: self.parents.get(n, ()))

    def down(self, id_: str) -> list[tuple[str, int]]:
        """Everything below it, nearest first, with the number of steps."""
        return self._walk(id_, self.children)


def build_trace(cfg: Config, ws: Workspace, doc: RequirementsDoc | None = None) -> Trace:
    doc = doc or parse_requirements(ws.read(cfg.requirements) if ws.exists(cfg.requirements) else "")
    parents: dict[str, list[str]] = {}
    kinds: dict[str, str] = {}
    labels: dict[str, str] = {}

    def link(child: str, parent: str) -> None:
        if parent not in parents.setdefault(child, []):
            parents[child].append(parent)

    for p in doc.problems:
        if p.id:
            kinds[p.id], labels[p.id] = "problem", p.text
    for r in doc.requests:
        kinds[r.id], labels[r.id] = "request", r.text
        for p in r.problems:
            link(r.id, p)
    for x in (*doc.functional, *doc.quality):
        kinds[x.id] = "requirement"
        labels[x.id] = x.text if hasattr(x, "text") else f"{x.quality}: {x.outline}"
        for r in x.satisfies:
            link(x.id, r)

    items, unplaced = build_v(cfg, ws)
    for i in items:
        if i.phase == "requirements" and i.kind in ("FR", "NFR"):
            for u in i.ucs:
                kinds.setdefault(u, "usecase")
                link(u, i.id)
    specs = {s.path: s for s in read_specs(cfg, ws)}
    for s in specs.values():
        kinds[s.uc], labels[s.uc] = "usecase", s.title
    declared, _ = collect_declared(cfg, ws)
    for ac, c in read_criteria(cfg, ws).items():
        kinds[ac], labels[ac] = "criterion", c.text
        for x in c.satisfies:
            link(ac, x)
        if declared.get(ac) in specs:
            link(ac, specs[declared[ac]].uc)
    for t in (*items, *unplaced):
        if t.kind == "test":
            kinds[t.id], labels[t.id] = "test", t.description or t.title
            for ac in t.acs:
                link(t.id, ac)
    return Trace({k: tuple(v) for k, v in parents.items()}, kinds, labels)
