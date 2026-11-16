"""Use-case dependencies: who must be built before whom.

The only authored fact is each spec's `Depends on` header row. Everything else (what a use case enables, its
wave, what blocks it) is derived, so it cannot drift from the specs.
"""

from __future__ import annotations

import posixpath
import re

from ..ports import Workspace
from .config import Config
from .model import natural_key

DEPENDS = re.compile(r"^\|\s*\*\*Depends on\*\*\s*\|(.*)\|\s*$", re.MULTILINE)


def read_links(cfg: Config, ws: Workspace) -> dict[str, list[str]]:
    """uc -> the use-case ids named in its `Depends on` row, in order, without repeats. Every spec is a key."""
    out: dict[str, list[str]] = {}
    for path in ws.files([cfg.specs], [".md"]):
        name = posixpath.basename(path)
        m = cfg.uc_re.match(name) if name.startswith("UC-") else None
        if not m:
            continue
        row = DEPENDS.search(ws.read(path))
        deps = cfg.uc_re.findall(row.group(1)) if row else []
        out[m.group(0)] = [d for i, d in enumerate(deps) if d not in deps[:i]]
    return out


def find_cycle(deps: dict[str, list[str]]) -> list[str] | None:
    """One dependency cycle as `[a, b, ..., a]`, or None."""
    state: dict[str, int] = {}  # 1 = on the current path, 2 = finished

    def visit(uc: str, path: list[str]) -> list[str] | None:
        state[uc] = 1
        for d in deps.get(uc, []):
            if d not in deps:
                continue
            if state.get(d) == 1:
                return [*path[path.index(d) :], uc, d] if d in path else [uc, d]
            if d not in state and (cycle := visit(d, [*path, uc])):
                return cycle
        state[uc] = 2
        return None

    for uc in deps:
        if uc not in state and (cycle := visit(uc, [])):
            return cycle
    return None


def waves(deps: dict[str, list[str]]) -> dict[str, int]:
    """uc -> wave: 0 for a root, else 1 + the deepest dependency. Unknown ids and cycles are ignored here;
    `check links` reports them."""
    memo: dict[str, int] = {}

    def depth(uc: str, seen: frozenset[str]) -> int:
        if uc in memo:
            return memo[uc]
        known = [d for d in deps.get(uc, []) if d in deps and d not in seen and d != uc]
        memo[uc] = 1 + max((depth(d, seen | {uc}) for d in known), default=-1)
        return memo[uc]

    return {uc: depth(uc, frozenset()) for uc in deps}


def enables(deps: dict[str, list[str]]) -> dict[str, list[str]]:
    """The inverse of `deps`: uc -> the use cases that name it."""
    out: dict[str, list[str]] = {uc: [] for uc in deps}
    for uc, ds in deps.items():
        for d in ds:
            if d in out:
                out[d].append(uc)
    return out


def to_mermaid(deps: dict[str, list[str]]) -> str:
    """The build order as a Mermaid flowchart: one subgraph per wave, an arrow from a dependency to what needs it."""
    wave = waves(deps)
    node = lambda uc: uc.replace("-", "_")  # noqa: E731
    lines = ["flowchart LR"]
    for w in sorted(set(wave.values())):
        lines.append(f'  subgraph W{w}["Wave {w}"]')
        lines += [f'    {node(uc)}["{uc}"]' for uc in sorted(deps, key=natural_key) if wave[uc] == w]
        lines.append("  end")
    for uc in sorted(deps, key=natural_key):
        lines += [f"  {node(d)} --> {node(uc)}" for d in deps[uc] if d in deps]
    return "\n".join(lines)
