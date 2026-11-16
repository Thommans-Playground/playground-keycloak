"""A change to the requirements, planned before anything is written.

A change adds, updates or deletes one problem, request, functional requirement or quality requirement. Planning it
validates the fields and the links, works out the new text of the requirements doc, a diff, and the blast radius: what
else the change touches, up toward the problem and down toward the tests. Links inside the requirements doc are
cleaned up automatically (a deleted request is removed from the requirements that satisfied it); anything in a spec,
a criterion or a test is only flagged for review, because a person has to read it again. Nothing here writes a file.
"""

from __future__ import annotations

import difflib
import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from ..ports import Workspace
from .config import Config
from .ids import FR_ID, NFR_ID, PROBLEM_ID, REQUEST_ID, collect_id_texts, next_ids, next_uc_id
from .mdtable import TableError, delete_row, locate, upsert_row
from .requirements_doc import RequirementsDoc, parse_requirements
from .scaffold import ac_table, spec_text
from .specs import read_specs
from .trace import Trace, build_trace

OPS = ("add", "update", "delete")
KINDS = ("problem", "request", "functional", "quality", "criterion", "usecase")
# A spec is read and rewritten by people, so from here a criterion or a use case can only be added.
ADD_ONLY = ("criterion", "usecase")
NOUN = {
    "criterion": "acceptance criterion",
    "usecase": "use case",
    "problem": "problem",
    "request": "request",
    "functional": "functional requirement",
    "quality": "quality requirement",
}
FIELDS = {
    "problem": ("text", "who", "cost"),
    "request": ("text", "raised_by", "problems"),
    "functional": ("text", "story", "satisfies"),
    "quality": (
        "quality",
        "outline",
        "satisfies",
        "source",
        "stimulus",
        "artifact",
        "environment",
        "response",
        "measure",
        "evidence",
    ),
    "criterion": ("uc", "text", "satisfies"),
    "usecase": ("title", "area", "realises"),
}
REQUIRED = {
    "problem": ("text",),
    "request": ("text",),
    "functional": ("text",),
    "quality": ("quality", "outline"),
    "criterion": ("uc", "text"),
    "usecase": ("title", "area"),
}
LISTS = ("problems", "satisfies", "realises")
# The fields that say what a thing is. Changing one means what depends on it should be read again; the others
# (who raised a request, the evidence) do not.
MEANING = (
    "text",
    "who",
    "cost",
    "story",
    "quality",
    "outline",
    "source",
    "stimulus",
    "artifact",
    "environment",
    "response",
    "measure",
)
ID_KIND = {"problem": "problem", "request": "request", "functional": "fr", "quality": "nfr"}
ID_RE = {
    "problem": PROBLEM_ID,
    "request": REQUEST_ID,
    "functional": FR_ID,
    "quality": NFR_ID,
    "criterion": r"AC-[A-Z]-\d{3}",
    "usecase": r"UC-[A-Z]-\d{3}",
}
LAYER = {
    "problem": "problem",
    "request": "request",
    "functional": "requirement",
    "quality": "requirement",
    "criterion": "criterion",
    "usecase": "usecase",
}
MAX_TEXT = 2000


class ChangeError(Exception):
    """The change is not a change this tool can make."""


@dataclass(frozen=True)
class Change:
    op: str
    kind: str
    id: str | None = None
    fields: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class Impact:
    id: str
    kind: str  # problem | request | requirement | usecase | criterion | test
    label: str
    direction: str  # up (toward the problem) | down (toward the tests) | here
    effect: str  # deleted | link-removed | link-added | status-changes | orphaned | needs-review | affected
    detail: str
    auto: bool = False  # done by the change itself, not left for a person


@dataclass
class Plan:
    change: Change
    summary: str
    edits: dict[str, str] = field(default_factory=dict)  # path -> the whole new text
    diff: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    impact: list[Impact] = field(default_factory=list)
    next_step: str = ""
    digest: str = ""


# ------------------------------------------------------------------------------------------------ parsing
def parse_change(raw: object) -> Change:
    """A change from the JSON a client sent. Anything unexpected is refused, not ignored."""
    if not isinstance(raw, dict):
        raise ChangeError("a change is an object with `op`, `kind`, `id` and `fields`")
    op, kind, id_, fields = raw.get("op"), raw.get("kind"), raw.get("id"), raw.get("fields", {})
    if op not in OPS:
        raise ChangeError(f"`op` is one of {', '.join(OPS)}")
    if kind not in KINDS:
        raise ChangeError(f"`kind` is one of {', '.join(KINDS)}")
    if kind in ADD_ONLY and op != "add":
        raise ChangeError(f"a {NOUN[kind]} can only be added from here; edit its spec to change it")
    if id_ is not None and not (isinstance(id_, str) and re.fullmatch(ID_RE[kind], id_)):
        raise ChangeError(f"`id` must look like {ID_RE[kind].replace(chr(92) + 'd{3}', 'nnn')}")
    if not isinstance(fields, dict):
        raise ChangeError("`fields` is an object")
    clean: dict[str, object] = {}
    for key, value in fields.items():
        if key not in FIELDS[kind]:
            raise ChangeError(f"a {NOUN[kind]} has no field `{key}`")
        if key in LISTS:
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise ChangeError(f"`{key}` is a list of ids")
            clean[key] = list(dict.fromkeys(v.strip() for v in value if v.strip()))
        else:
            if not isinstance(value, str):
                raise ChangeError(f"`{key}` is text")
            text = re.sub(r"\s+", " ", value).strip()
            if len(text) > MAX_TEXT:
                raise ChangeError(f"`{key}` is longer than {MAX_TEXT} characters")
            clean[key] = text
    if op != "add" and not id_:
        raise ChangeError(f"`id` says which {NOUN[kind]} to {op}")
    return Change(op, kind, id_, clean)


# ------------------------------------------------------------------------------------------------ the doc's tables
def _has(header: list[str], *starts: str) -> bool:
    return all(any(h.startswith(s) for h in header) for s in starts)


TABLES: dict[str, Callable[[list[str]], bool]] = {
    "problem": lambda h: _has(h, "problem", "who", "cost"),
    "request": lambda h: "raised by" in h,
    "functional": lambda h: _has(h, "functional requirement"),
    "quality": lambda h: _has(h, "quality", "requirement") and not _has(h, "source"),
    "scenario": lambda h: _has(h, "quality", "source"),
}
COLUMNS = {
    "problem": {"text": "problem", "who": "who", "cost": "cost"},
    "request": {"text": "the ask", "raised_by": "raised by", "problems": "problem"},
    "functional": {"text": "functional requirement", "story": "user story", "satisfies": "satisfies"},
    "quality": {"quality": "quality", "outline": "requirement", "satisfies": "satisfies", "evidence": "evidence"},
    "scenario": {
        "quality": "quality",
        "source": "source",
        "stimulus": "stimulus",
        "artifact": "artifact",
        "environment": "environment",
        "response": "response",
        "measure": "response measure",
    },
}


def _existing(doc: RequirementsDoc, kind: str, id_: str) -> dict[str, object] | None:
    if kind == "problem":
        p = next((p for p in doc.problems if p.id == id_), None)
        return {"text": p.text, "who": p.who, "cost": p.cost} if p else None
    if kind == "request":
        r = next((r for r in doc.requests if r.id == id_), None)
        return {"text": r.text, "raised_by": r.raised_by, "problems": list(r.problems)} if r else None
    if kind == "functional":
        f = next((f for f in doc.functional if f.id == id_), None)
        return {"text": f.text, "story": f.story, "satisfies": list(f.satisfies)} if f else None
    q = next((q for q in doc.quality if q.id == id_), None)
    if not q:
        return None
    return {
        "quality": q.quality,
        "outline": q.outline,
        "satisfies": list(q.satisfies),
        "source": q.source,
        "stimulus": q.stimulus,
        "artifact": q.artifact,
        "environment": q.environment,
        "response": q.response,
        "measure": q.measure,
        "evidence": q.evidence,
    }


def _cell(key: str, value: object, kind: str) -> str:
    if isinstance(value, list):
        return ", ".join(value)
    return f'"{str(value).strip(chr(34))}"' if (kind, key) == ("request", "text") else str(value)


def _upsert(text: str, kind: str, id_: str, values: dict[str, object], *, add: bool) -> str:
    """Write a requirement-side row into its table, or tables (a quality requirement has an outline and a scenario)."""
    tables = (
        ["problem"]
        if kind == "problem"
        else ["request"]
        if kind == "request"
        else ["functional"]
        if kind == "functional"
        else ["quality", "scenario"]
    )
    for table in tables:
        cols = {COLUMNS[table][k]: _cell(k, v, table) for k, v in values.items() if k in COLUMNS[table]}
        if add and table == "functional":
            cols["maturity"] = "⚪"
        if cols or add:
            text = upsert_row(text, TABLES[table], id_, cols)
    return text


def _remove(text: str, kind: str, id_: str) -> str:
    tables = (
        ["problem"]
        if kind == "problem"
        else ["request"]
        if kind == "request"
        else ["functional"]
        if kind == "functional"
        else ["quality", "scenario"]
    )
    for table in tables:
        try:
            text = delete_row(text, TABLES[table], id_)
        except TableError:
            if table != "scenario":
                raise
    return text


def _drop_link(text: str, kind: str, id_: str, link_key: str, gone: str, current: list[str]) -> str:
    return _upsert(text, kind, id_, {link_key: [x for x in current if x != gone]}, add=False)


# ------------------------------------------------------------------------------------------------ planning
def plan_change(
    cfg: Config, ws: Workspace, change: Change, *, trace: Trace | None = None, spec_template: str | None = None
) -> Plan:
    kind, op = change.kind, change.op
    plan = Plan(change, f"{op.capitalize()} {NOUN[kind]}")
    if not ws.exists(cfg.requirements):
        plan.errors.append(f"{cfg.requirements} does not exist; run `vbench init` first")
        return plan
    old = ws.read(cfg.requirements)
    doc = parse_requirements(old)
    trace = trace or build_trace(cfg, ws, doc)

    problems = {p.id for p in doc.problems if p.id}
    requests = {r.id for r in doc.requests}
    fields = dict(change.fields)
    if kind in ADD_ONLY:
        return _plan_in_specs(plan, cfg, ws, doc, trace, fields, spec_template)

    if op == "add":
        for key in REQUIRED[kind]:
            if not fields.get(key):
                plan.errors.append(f"`{key}` is required")
        id_ = next_ids(ID_KIND[kind], "", collect_id_texts(cfg, ws))[0]
        change = Change(op, kind, id_, fields)
        plan.change, plan.summary = change, f"Add {NOUN[kind]} {id_}"
        current: dict[str, object] = {}
    else:
        id_ = change.id or ""
        found = _existing(doc, kind, id_)
        if found is None:
            plan.errors.append(f"{id_} is not in {cfg.requirements}")
            return plan
        current = found
        plan.summary = f"{op.capitalize()} {NOUN[kind]} {id_}"

    # links must point at things that exist
    for key, known, noun in (("problems", problems, "problem"), ("satisfies", requests, "request")):
        for ref in fields.get(key, []) if isinstance(fields.get(key), list) else []:
            if ref not in known:
                plan.errors.append(f"{ref} is not a {noun} in the requirements doc")
    if kind == "quality" and op != "delete" and not fields.get("measure") and not current.get("measure"):
        plan.warnings.append("A quality requirement needs a response measure to be checkable.")
    if op == "add":
        plan.warnings += _similar(doc, kind, fields)
    if plan.errors:
        return plan

    new = old
    try:
        if op == "delete":
            new, auto = _cascade_delete(new, kind, id_, trace, doc)
            plan.impact += auto
        else:
            values = {k: v for k, v in fields.items() if op == "add" or v != current.get(k)}
            if op == "update" and not values:
                plan.warnings.append("Nothing changed.")
            new = _upsert(new, kind, id_, values, add=op == "add")
    except TableError as e:
        plan.errors.append(str(e))
        return plan

    plan.impact += _impact(change, current, fields, trace)
    plan.next_step = _next_step(change)
    if new != old:
        plan.edits[cfg.requirements] = new
        plan.diff = "\n".join(
            difflib.unified_diff(old.split("\n"), new.split("\n"), cfg.requirements, cfg.requirements, lineterm="", n=2)
        )
    after = parse_requirements(new)
    plan.warnings += [
        f"{r.id} would name {p}, which does not exist"
        for r in after.requests
        for p in r.problems
        if p not in {x.id for x in after.problems}
    ]
    plan.digest = edits_digest(plan.edits)
    return plan


def edits_digest(edits: dict[str, str]) -> str:
    """One fingerprint of every file a plan writes, so apply can tell whether the files moved since the preview."""
    return hashlib.sha256("\0".join(f"{p}\0{t}" for p, t in sorted(edits.items())).encode()).hexdigest()


def _similar(doc: RequirementsDoc, kind: str, fields: dict[str, object]) -> list[str]:
    key = "quality" if kind == "quality" else "text"
    mine = re.sub(r"\W+", " ", str(fields.get(key, ""))).lower().strip()
    pool = {
        "problem": [(p.id, p.text) for p in doc.problems],
        "request": [(r.id, r.text) for r in doc.requests],
        "functional": [(f.id, f.text) for f in doc.functional],
        "quality": [(q.id, f"{q.quality} {q.outline}") for q in doc.quality],
    }[kind]
    out = []
    for id_, text in pool:
        theirs = re.sub(r"\W+", " ", text).lower().strip()
        if mine and difflib.SequenceMatcher(None, mine, theirs).ratio() >= 0.85:
            out.append(f'This looks like {id_}: "{text[:80]}". Update that one instead if it is the same thing.')
    return out


def _cascade_delete(text: str, kind: str, id_: str, trace: Trace, doc: RequirementsDoc) -> tuple[str, list[Impact]]:
    """Remove the id from every link that names it inside the requirements doc, then remove the row."""
    auto: list[Impact] = []
    if kind == "problem":
        for r in doc.requests:
            if id_ in r.problems:
                text = _drop_link(text, "request", r.id, "problems", id_, list(r.problems))
                auto.append(
                    Impact(
                        r.id,
                        "request",
                        trace.labels.get(r.id, ""),
                        "down",
                        "link-removed",
                        f"no longer names {id_}",
                        auto=True,
                    )
                )
    elif kind == "request":
        for x in (*doc.functional, *doc.quality):
            if id_ in x.satisfies:
                k = "functional" if x.id.startswith("REQ-FR") else "quality"
                text = _drop_link(text, k, x.id, "satisfies", id_, list(x.satisfies))
                auto.append(
                    Impact(
                        x.id,
                        "requirement",
                        trace.labels.get(x.id, ""),
                        "down",
                        "link-removed",
                        f"no longer satisfies {id_}",
                        auto=True,
                    )
                )
    return _remove(text, kind, id_), auto


def _label(trace: Trace, id_: str) -> str:
    return trace.labels.get(id_, "")


def _impact(change: Change, current: dict[str, object], fields: dict[str, object], trace: Trace) -> list[Impact]:
    """What else the change touches. Direction is up (toward the problem) or down (toward the tests)."""
    kind, op, id_ = change.kind, change.op, change.id or ""
    me = LAYER[kind]
    out: list[Impact] = []

    def note(node: str, direction: str, effect: str, detail: str) -> None:
        out.append(Impact(node, trace.kinds.get(node, "requirement"), _label(trace, node), direction, effect, detail))

    def parent_key() -> str:
        return "problems" if kind == "request" else "satisfies"

    if op == "add":
        for p in fields.get(parent_key(), []) if isinstance(fields.get(parent_key()), list) else []:
            if kind == "request" and not trace.children(p):
                note(p, "up", "status-changes", "No request yet becomes Has a request")
            else:
                note(
                    p,
                    "up",
                    "link-added",
                    f"gains {id_} as a {me}" if kind != "request" else f"gains {id_} as a request",
                )
        return out

    if op == "delete":
        out.append(Impact(id_, me, _label(trace, id_), "here", "deleted", f"{id_} is removed from {NOUN[kind]}s"))
        for parent in trace.parents.get(id_, ()):
            siblings = [c for c in trace.children(parent) if c != id_ and trace.kinds.get(c) == me]
            note(
                parent,
                "up",
                "status-changes" if not siblings else "link-removed",
                "loses its only " + me if not siblings else f"loses {id_}",
            )
        for node, depth in trace.down(id_):
            other_parents = [p for p in trace.parents.get(node, ()) if p != id_]
            layer = trace.kinds.get(node)
            if depth == 1 and layer in ("request", "requirement") and kind in ("problem", "request"):
                if not other_parents:
                    note(node, "down", "orphaned", f"now has no {'problem' if layer == 'request' else 'request'}")
            elif depth == 1 and layer in ("usecase", "criterion"):
                note(
                    node,
                    "down",
                    "needs-review",
                    f"still names {id_}: update its {'Realises row' if layer == 'usecase' else 'Satisfies column'}",
                )
            elif layer in ("usecase", "criterion", "test") or depth > 1:
                note(node, "down", "affected", f"sits below {id_}")
        return out

    # an update: a change of meaning means what hangs below should be read again
    changed = [k for k, v in fields.items() if v != current.get(k)]
    if any(k in MEANING for k in changed):
        for node, depth in trace.down(id_):
            note(
                node,
                "down",
                "needs-review" if depth == 1 else "affected",
                "its wording may no longer match; read it again" if depth == 1 else f"sits {depth} steps below {id_}",
            )
    key = parent_key()
    if key in changed:
        before, after = set(current.get(key, [])), set(fields.get(key, []))
        for gone in sorted(before - after):
            siblings = [c for c in trace.children(gone) if c != id_]
            note(
                gone,
                "up",
                "status-changes" if not siblings else "link-removed",
                "loses its only " + me if not siblings else f"loses {id_}",
            )
        for new in sorted(after - before):
            note(new, "up", "link-added", f"gains {id_}")
        if not after and kind != "problem":
            out.append(
                Impact(
                    id_,
                    me,
                    _label(trace, id_),
                    "here",
                    "orphaned",
                    f"now names no {'problem' if kind == 'request' else 'request'}",
                )
            )
    return out


def _next_step(change: Change) -> str:
    if change.op != "add":
        return ""
    return {
        "problem": "Next: add a request that names this problem.",
        "request": "Next: add a requirement that satisfies this request.",
        "functional": "Next: a use case that realises it (`vbench new uc`), then its criteria.",
        "quality": "Next: a criterion that cites it (/vbench:v-1-requirements).",
    }[change.kind]


# --------------------------------------------------------------------------------------- criteria and use cases
def _files_diff(ws: Workspace, plan: Plan) -> None:
    """The diff of every file the plan writes (a new file diffs against nothing), and the digest of the lot."""
    parts = []
    for path, new in sorted(plan.edits.items()):
        old = ws.read(path) if ws.exists(path) else ""
        lines = difflib.unified_diff(old.split("\n") if old else [], new.split("\n"), path, path, lineterm="", n=2)
        parts.append("\n".join(lines))
    plan.diff = "\n".join(parts)
    plan.digest = edits_digest(plan.edits)


def _plan_criterion(plan: Plan, cfg: Config, ws: Workspace, trace: Trace, fields: dict[str, object]) -> Plan:
    """Add a criterion to a use case's spec. A scaffold row still marked TBD is filled in rather than left beside it."""
    uc = str(fields["uc"])
    spec = next((s for s in read_specs(cfg, ws) if s.uc == uc), None)
    if spec is None:
        plan.errors.append(f"{uc} has no spec under {cfg.specs}")
        return plan
    text = ws.read(spec.path)
    try:
        found = locate(text, ac_table)
    except TableError:
        plan.errors.append(f"{spec.path} has no acceptance-criteria table")
        return plan
    said = next((i for i, h in enumerate(found.header) if h.startswith("given")), 1)
    scaffold = next(
        (c[0].strip("* ") for _, c in found.rows if len(c) > said and c[said].upper().startswith("TBD")), None
    )
    ac = scaffold or next_ids("ac", uc[3], collect_id_texts(cfg, ws))[0]
    sentence = str(fields["text"])
    if not re.search(r"\bgiven\b.*\bwhen\b.*\bthen\b", sentence, re.IGNORECASE):
        plan.warnings.append("Write it as Given … when … then …, so it can become a test.")
    satisfies = fields.get("satisfies", [])
    plan.change = Change("add", "criterion", ac, fields)
    plan.summary = f"Add acceptance criterion {ac} to {uc}" + (" (fills the scaffold row)" if scaffold else "")
    plan.edits[spec.path] = upsert_row(text, ac_table, ac, {"given": sentence, "satisfies": ", ".join(satisfies)})
    plan.warnings.append(f"No test carries {ac} yet, so `vbench check acs` fails until one does.")
    plan.impact = [
        Impact(r, "requirement", trace.labels.get(r, ""), "up", "link-added", f"gains {ac} to satisfy")
        for r in satisfies
    ]
    plan.impact.append(Impact(uc, "usecase", trace.labels.get(uc, ""), "up", "link-added", f"gains {ac}"))
    plan.next_step = f'Next: the test that proves it, tagged `@pytest.mark.ac("{ac}")` (/vbench:v-3-code {uc}).'
    return plan


def _plan_use_case(
    plan: Plan, cfg: Config, ws: Workspace, trace: Trace, fields: dict[str, object], template: str | None
) -> Plan:
    """Add a use case: the same spec file `vbench new uc` writes, naming the requirements it realises."""
    area = str(fields["area"]).strip().upper()
    if not re.fullmatch(r"[A-Z]", area):
        plan.errors.append("`area` is a single letter, the area code")
    slug = re.sub(r"[^a-z0-9]+", "-", str(fields["title"]).lower()).strip("-")
    if not slug:
        plan.errors.append("`title` has no letters or digits to name the file from")
    if template is None:
        plan.errors.append("there is no use-case template to scaffold from")
    if plan.errors:
        return plan
    texts = collect_id_texts(cfg, ws)
    names = [p.rsplit("/", 1)[-1] for p in ws.files([cfg.specs.rstrip("/")], [".md"])]
    code = [ws.read(p) for p in [*ws.files(cfg.prod, cfg.prod_ext), *ws.files(cfg.tests, cfg.test_ext)]]
    uc = next_uc_id(area, names, code)
    ac, task = next_ids("ac", area, texts)[0], next_ids("task", area, texts)[0]
    path = f"{cfg.specs.rstrip('/')}/{uc}-{slug}.md"
    if ws.exists(path):
        plan.errors.append(f"{path} already exists")
        return plan
    realises = fields.get("realises", [])
    plan.change = Change("add", "usecase", uc, {**fields, "area": area})
    plan.summary = f"Add use case {uc}"
    plan.edits[path] = spec_text(cfg, template or "", uc, str(fields["title"]), ac, task, realises)
    plan.impact = [
        Impact(r, "requirement", trace.labels.get(r, ""), "up", "link-added", f"is realised by {uc}") for r in realises
    ]
    plan.next_step = f"Next: write its criteria (/vbench:v-1-requirements {uc}), then its design."
    return plan


def _plan_in_specs(
    plan: Plan,
    cfg: Config,
    ws: Workspace,
    doc: RequirementsDoc,
    trace: Trace,
    fields: dict[str, object],
    template: str | None,
) -> Plan:
    """Add a criterion or a use case: both are written in the specs folder rather than in the requirements doc."""
    kind = plan.change.kind
    plan.errors += [f"`{key}` is required" for key in REQUIRED[kind] if not fields.get(key)]
    wanted = [r for k in ("satisfies", "realises") for r in (fields.get(k) if isinstance(fields.get(k), list) else [])]
    known = {x.id for x in (*doc.functional, *doc.quality)}
    plan.errors += [f"{r} is not a requirement in the requirements doc" for r in wanted if r not in known]
    if plan.errors:
        return plan
    planned = (
        _plan_criterion(plan, cfg, ws, trace, fields)
        if kind == "criterion"
        else _plan_use_case(plan, cfg, ws, trace, fields, template)
    )
    if not planned.errors:
        _files_diff(ws, planned)
    return planned
