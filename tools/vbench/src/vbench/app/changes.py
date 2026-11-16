"""Use cases: preview a change to the requirements, apply it, and commit what it wrote.

Preview writes nothing: it returns the diff, the blast radius and the checks a person needs to decide. Apply plans the
change again and writes only if it is still exactly what was shown (the digest), so a stale preview cannot overwrite
newer edits. Commit takes only documentation files and a one-line message in the repository's convention.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import asdict
from typing import Any

from ..domain.changes import Plan, parse_change, plan_change
from ..domain.config import Config
from ..domain.errors import StaleError, UsageError
from ..domain.paths import docs_path
from ..ports import Committer, Templates, Workspace
from .check import run_checks
from .new import spec_template
from .sync import sync


def _plan_json(plan: Plan) -> dict[str, Any]:
    return {
        "summary": plan.summary,
        "change": {"op": plan.change.op, "kind": plan.change.kind, "id": plan.change.id, "fields": plan.change.fields},
        "errors": plan.errors,
        "warnings": plan.warnings,
        "diff": plan.diff,
        "impact": [asdict(i) for i in plan.impact],
        "nextStep": plan.next_step,
        "digest": plan.digest,
        "files": sorted(plan.edits),
    }


def _plan(cfg: Config, ws: Workspace, raw: object, templates: Templates | None) -> Plan:
    """Plan the change; a use case is scaffolded from the project's template, or the one vbench ships."""
    change = parse_change(raw)
    template = spec_template(cfg, ws, templates) if templates is not None and change.kind == "usecase" else None
    return plan_change(cfg, ws, change, spec_template=template)


def preview_change(cfg: Config, ws: Workspace, raw: object, templates: Templates | None = None) -> dict[str, Any]:
    return _plan_json(_plan(cfg, ws, raw, templates))


def apply_change(
    cfg: Config,
    ws: Workspace,
    raw: object,
    digest: str,
    templates: Templates | None = None,
    written: set[str] | None = None,
) -> dict[str, Any]:
    """Write the change if it is still what was previewed. `written` collects the files this wrote, so a later commit
    can be limited to them. If a file cannot be written, the ones already written are put back."""
    plan = _plan(cfg, ws, raw, templates)
    if plan.errors:
        raise UsageError("; ".join(plan.errors))
    if not plan.edits:
        raise UsageError("Nothing to change.")
    if plan.digest != digest:
        raise StaleError("The files changed since this was previewed. Preview it again.")
    before = {path: ws.read(path) if ws.exists(path) else None for path in plan.edits}
    try:
        for path, text in plan.edits.items():
            ws.write(path, text, overwrite=True)
    except OSError as e:
        for (
            name,
            old,
        ) in before.items():  # put each file back as it was; one that cannot be restored must not hide the rest
            if old is not None:
                with contextlib.suppress(OSError):
                    ws.write(name, old, overwrite=True)
        raise UsageError(f"Could not write {path}; nothing was changed: {e}") from e
    if written is not None:
        written.update(plan.edits)
    regenerated = sync(cfg, ws)  # generated blocks that quote the requirements follow the change
    gates = [{"name": r.name, "ok": r.ok, "lines": r.lines} for r in run_checks(cfg, ws)]
    return {
        "summary": plan.summary,
        "id": plan.change.id,
        "written": sorted(plan.edits),
        "regenerated": regenerated,
        "gates": gates,
        "nextStep": plan.next_step,
        "impact": [asdict(i) for i in plan.impact],
    }


def commit_changes(
    cfg: Config,
    ws: Workspace,
    committer: Committer,
    paths: object,
    summary: object,
    written: set[str] | None = None,
) -> dict[str, Any]:
    """Commit documentation files. With `written` (the files applied in this session), only those may be committed, so
    a caller cannot sweep in edits it did not make; the set is emptied of what was committed."""
    if not isinstance(paths, list) or not paths or not all(isinstance(p, str) for p in paths):
        raise UsageError("`paths` is a list of the files to commit")
    clean_paths: list[str] = []
    for p in paths:
        clean = docs_path(cfg, p)
        if clean is None:
            raise UsageError(f"{p} is not a documentation file, so it is not committed from here")
        if not ws.exists(clean):
            raise UsageError(f"{p} does not exist")
        if written is not None and clean not in written:
            raise UsageError(
                f"{p} was not changed by an applied change in this session, so it is not committed from here"
            )
        clean_paths.append(clean)
    line = re.sub(r"\s+", " ", str(summary or "update the requirements")).strip()[:90]
    message = f"chore: {line[:1].lower()}{line[1:]}"
    if not cfg.commit_re.match(message):
        raise UsageError(f"`{message}` does not follow the commit convention")
    sha = committer.commit(clean_paths, message)
    if written is not None:
        written.difference_update(clean_paths)
    return {"commit": sha, "message": message, "paths": clean_paths}
