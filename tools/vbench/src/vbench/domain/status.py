"""Progress derived from specs, tags and gates. Read-only; no state is stored anywhere.

Each use case sits at one stage of the V, worked out from the files alone:

    requirements  no acceptance criterion has been written yet (rows still say TBD)
    design        criteria exist, but no task closes one, or a required diagram (or the context's model) is missing
    code          a task has criteria with no marked test (`task` is the first such task)
    rung          every task is closed, but no code realises it or no test verifies it
    verify        built; the next step is the independent re-check
"""

from __future__ import annotations

from ..ports import Workspace
from .checks import (
    check_acs,
    check_diagrams,
    check_docs,
    check_links,
    check_refs,
    check_rungs,
    collect_declared,
    collect_realised,
    collect_referenced,
    collect_tasks,
    collect_unspecified,
    collect_verified,
    lifecycle_undecided,
    missing_diagrams,
    missing_system_diagrams,
)
from .config import Config
from .graph import read_links, waves
from .model import StatusReport, UcRow, natural_key
from .specs import read_specs

BUILT = "verify"


def command_for(uc: str, stage: str, task: str | None) -> str:
    return {
        "requirements": f"/vbench:v-1-requirements {uc}",
        "design": f"/vbench:v-2-design {uc}",
        "code": f"/vbench:v-3-code {uc}" + (f" {task}" if task else ""),
        "rung": f"/vbench:v-3-code {uc}",
        "verify": f"/vbench:v-4-verify {uc}",
    }[stage]


def derive_status(cfg: Config, ws: Workspace, narrow: str | None = None) -> StatusReport:
    declared, planned = collect_declared(cfg, ws)
    unspecified = collect_unspecified(cfg, ws)
    referenced = collect_referenced(cfg, ws)
    realised, verified = collect_realised(cfg, ws), collect_verified(cfg, ws)
    tasks = collect_tasks(cfg, ws)
    deps = read_links(cfg, ws)
    no_diagram = {**missing_diagrams(cfg, ws), **missing_system_diagrams(cfg, ws)}
    for uc in lifecycle_undecided(cfg, ws):  # the full tier needs the lifecycle decided, so design is not finished
        no_diagram.setdefault(uc, ["lifecycle decision"])
    wave = waves(deps)
    ucs = sorted(deps, key=lambda u: (wave[u], natural_key(u)))

    spec_uc = {s.path: s.uc for s in read_specs(cfg, ws)}
    stages: dict[str, tuple[str, str | None]] = {}
    rows: dict[str, UcRow] = {}
    for uc in ucs:
        acs = [a for a, path in declared.items() if spec_uc.get(path) == uc]
        enforced = [a for a in acs if a not in planned]
        covered = [a for a in enforced if a in referenced]
        code, tested = uc in realised, uc in verified
        mine = {t: acs_ for t, (path, acs_) in tasks.items() if spec_uc.get(path) == uc}

        def pending(task_acs: list[str]) -> bool:
            need = [a for a in task_acs if a not in planned]
            return bool(need) and not all(a in referenced for a in need)

        closed = sum(1 for a in mine.values() if a and not pending(a) and any(x not in planned for x in a))
        if not [a for a in acs if a not in unspecified]:
            stage, task = "requirements", None
        elif not any(mine.values()) or uc in no_diagram:
            stage, task = "design", None
        elif open_tasks := sorted((t for t, a in mine.items() if pending(a)), key=natural_key):
            stage, task = "code", open_tasks[0]
        elif not (code and tested):
            stage, task = "rung", None
        else:
            stage, task = BUILT, None
        stages[uc] = (stage, task)
        rows[uc] = UcRow(
            uc, len(acs), len(covered), len(enforced), code, tested, "", len(mine), closed, wave[uc], (), stage, task
        )

    out: list[UcRow] = []
    for uc in ucs:
        blocked = tuple(d for d in deps[uc] if d in stages and stages[d][0] != BUILT)
        stage, task = stages[uc]
        nxt = command_for(uc, stage, task)
        out.append(UcRow(**{**rows[uc].__dict__, "blocked_by": blocked, "next": nxt}))

    if narrow:
        out = [r for r in out if r.uc == narrow or r.uc.startswith(f"UC-{narrow.upper()}")]
    orphans = sorted(u for u in realised if u not in deps)
    return StatusReport(
        out,
        orphans,
        [
            check_refs(cfg, ws),
            check_rungs(cfg, ws),
            check_acs(cfg, ws),
            check_links(cfg, ws),
            check_diagrams(cfg, ws),
            check_docs(cfg, ws),
        ],
    )
