"""The logical view of the V-cycle: everything the project holds, placed on one of nine phases.

    left arm (specify)     requirements   system design   architecture   module design
    vertex                 code
    right arm (prove)      acceptance     system          integration    unit          (tests, by rung)

Each left-arm phase is paired with the test level that proves it. A phase's items are plain facts read from the
specs, diagrams, tags and tests (nothing is stored), and every item names the use cases it belongs to, so a UI can
draw the V that any one item is part of. Tests are indexed per function for Python (with `ast`), per file otherwise.
"""

from __future__ import annotations

import ast
import posixpath
import re
from dataclasses import dataclass

from ..ports import Workspace
from .checks import (
    VERIFIES,
    collect_declared,
    collect_realised,
    collect_referenced,
    collect_verified,
    diagram_files,
    missing_diagrams,
)
from .config import Config
from .contexts import CONTEXT_MAP, context_files
from .describe import diagram_title, first_line, humanise, module_summary
from .ids import FR_ID, NFR_ID, REQ_ID, REQUEST_ID
from .model import natural_key
from .requirements_doc import read_requirements
from .specs import read_specs, slug

# key, label, arm, the phase on the other arm that proves it (or that it is the vertex of)
PHASES = (
    ("requirements", "Requirements", "left", "acceptance"),
    ("system-design", "System design", "left", "system"),
    ("architecture", "Architecture", "left", "integration"),
    ("module-design", "Module design", "left", "unit"),
    ("code", "Code", "vertex", None),
    ("unit", "Unit tests", "right", "module-design"),
    ("integration", "Integration tests", "right", "architecture"),
    ("system", "System tests", "right", "system-design"),
    ("acceptance", "Acceptance tests", "right", "requirements"),
)
RUNGS = ("unit", "integration", "system", "acceptance")
RUNG_WORD = re.compile(r"\b(unit|integration|system|acceptance)\s+rung")
REQ_ROWS = {
    "REQ": re.compile(
        rf"^\|\s*\*\*({REQUEST_ID})\*\*\s*\|([^|]*)\|([^|]*)\|", re.MULTILINE
    ),  # id | raised by | the ask
    "FR": re.compile(rf"^\|\s*\*\*({FR_ID})\*\*\s*\|([^|]*)\|", re.MULTILINE),  # id | requirement
    "NFR": re.compile(rf"^\|\s*\*\*({NFR_ID})\*\*\s*\|([^|]*)\|([^|]*)\|", re.MULTILINE),  # id | quality | requirement
}


@dataclass(frozen=True)
class VItem:
    id: str
    phase: str
    kind: str
    title: str
    ucs: tuple[str, ...] = ()
    file: str | None = None
    line: int | None = None
    status: str = "neutral"  # ok | warn | risk | neutral, always paired with `label`
    label: str = ""
    acs: tuple[str, ...] = ()
    description: str = ""  # what it is, in words: the name says which, this says what


@dataclass(frozen=True)
class IndexedTest:
    id: str
    name: str
    file: str
    line: int | None
    ucs: tuple[str, ...]
    rung: str | None
    acs: tuple[str, ...]
    doc: str = ""  # the first explaining line of its docstring, if any


def _uniq(items) -> tuple:
    return tuple(dict.fromkeys(items))


def _rungs(clauses: list[str]) -> list[str]:
    return list(dict.fromkeys(w for c in clauses for w in RUNG_WORD.findall(c)))


# ----------------------------------------------------------------------------------------------- tests
def _index_python(cfg: Config, path: str, text: str) -> list[IndexedTest] | None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    mod = VERIFIES.findall(ast.get_docstring(tree) or "")
    mod_ucs, mod_rungs = _uniq(cfg.uc_re.findall(" ".join(mod))), _rungs(mod)
    out: list[IndexedTest] = []

    def visit(body: list[ast.stmt], prefix: str, inherited: list[str]) -> None:
        for node in body:
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                visit(node.body, f"{prefix}{node.name}.", inherited + [ast.unparse(d) for d in node.decorator_list])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                clauses = VERIFIES.findall(ast.get_docstring(node) or "")
                ucs = _uniq(cfg.uc_re.findall(" ".join(clauses))) or mod_ucs
                found = _rungs(clauses) or (mod_rungs if len(mod_rungs) == 1 else [])
                decorators = inherited + [ast.unparse(d) for d in node.decorator_list]
                acs = _uniq(
                    a for d in decorators for call in cfg.ac_mark_re.findall(d) for a in cfg.ac_re.findall(call)
                )
                out.append(
                    IndexedTest(
                        f"{path}::{prefix}{node.name}",
                        f"{prefix}{node.name}",
                        path,
                        node.lineno,
                        ucs,
                        found[0] if found else None,
                        acs,
                        first_line(ast.get_docstring(node)),
                    )
                )

    visit(tree.body, "", [])
    return out if out or not VERIFIES.search(text) else None


def collect_test_cases(cfg: Config, ws: Workspace) -> list[IndexedTest]:
    """Every test the project holds: per function for Python, per file when it cannot be parsed or is not Python."""
    out: list[IndexedTest] = []
    for path in ws.files(cfg.tests, cfg.test_ext):
        text = ws.read(path)
        indexed = _index_python(cfg, path, text) if path.endswith(".py") else None
        if indexed is None:
            clauses = VERIFIES.findall(text)
            rungs = _rungs(clauses)
            acs = _uniq(a for call in cfg.ac_mark_re.findall(text) for a in cfg.ac_re.findall(call))
            if not clauses and not acs:
                continue  # not a test file the method knows about
            indexed = [
                IndexedTest(
                    path,
                    posixpath.basename(path),
                    path,
                    None,
                    _uniq(cfg.uc_re.findall(" ".join(clauses))),
                    rungs[0] if len(rungs) == 1 else None,
                    acs,
                )
            ]
        out += indexed
    return sorted(out, key=lambda t: (t.file, t.line or 0))


# ----------------------------------------------------------------------------------------------- items
def _requirements(cfg: Config, ws: Workspace) -> list[tuple[str, str, str]]:
    if not ws.exists(cfg.requirements):
        return []
    text, seen, out = ws.read(cfg.requirements), set(), []
    for kind, rx in REQ_ROWS.items():
        for m in rx.finditer(text):
            rid = m.group(1)
            cells = [c.strip() for c in m.groups()[1:]]
            if rid in seen or any(c.startswith("(") for c in cells[:2]):
                continue
            seen.add(rid)
            if kind == "REQ":
                title = cells[1]
            elif kind == "NFR":
                title = f"{cells[0]}: {cells[1]}"
            else:
                title = cells[0]
            out.append((kind, rid, title.strip('" ')))
    return sorted(out, key=lambda t: natural_key(t[1]))


def build_v(cfg: Config, ws: Workspace) -> tuple[list[VItem], list[VItem]]:
    """(items placed on a phase, tests that cannot be placed because they name no use case or no rung)."""
    specs = sorted(read_specs(cfg, ws), key=lambda s: natural_key(s.uc))
    by_uc = {s.uc: s for s in specs}
    _declared, planned = collect_declared(cfg, ws)
    referenced = collect_referenced(cfg, ws)
    realised, verified = collect_realised(cfg, ws), collect_verified(cfg, ws)
    items: list[VItem] = []

    # what each criterion satisfies, and what each use case realises
    satisfies: dict[str, list[str]] = {}
    realises: dict[str, set[str]] = {}
    tasks: list[tuple[str, str, str, list[str]]] = []
    for s in specs:
        text = ws.read(s.path)
        for m in cfg.ac_decl_re.finditer(text):
            satisfies[m.group(1)] = REQ_ID.findall(m.group(2))
        m = re.search(r"^\|\s*\*\*Realises\*\*\s*\|(.*)\|\s*$", text, re.MULTILINE)
        realises[s.uc] = set(REQ_ID.findall(m.group(1))) if m else set()
        for t in cfg.task_decl_re.finditer(text):
            cells = [c.strip() for c in t.group(2).strip().strip("|").split("|")]  # description | ACs it closes
            if cells and not cells[0].startswith("("):
                tasks.append((t.group(1), s.uc, cells[0], cfg.ac_re.findall(t.group(2))))

    # requirements
    doc = read_requirements(cfg, ws)
    about: dict[str, str] = {
        **{r.id: f"Raised by {r.raised_by}" if r.raised_by else "" for r in doc.requests},
        **{f.id: f.story for f in doc.functional},
        **{
            q.id: " ".join(
                p
                for p in (
                    f"{q.source} {q.stimulus.lower()}." if q.source else "",
                    f"{q.response}.",
                    f"Measure: {q.measure}.",
                )
                if p and p not in (".", "Measure: .")
            )
            for q in doc.quality
        },
    }
    for p in doc.problems:
        if not p.id:
            continue
        raised = [r.id for r in doc.requests if p.id in r.problems]
        affects = " ".join(x for x in (f"{p.who}." if p.who else "", f"Cost: {p.cost}." if p.cost else "") if x)
        items.append(
            VItem(
                p.id,
                "requirements",
                "problem",
                p.text,
                (),
                cfg.requirements,
                None,
                "ok" if raised else "warn",
                "Has a request" if raised else "No request yet",
                (),
                affects,
            )
        )
    for kind, rid, title in _requirements(cfg, ws):
        ucs = tuple(u for u in sorted(realises, key=natural_key) if rid in realises[u])
        acs = tuple(a for a, reqs in satisfies.items() if rid in reqs)
        if kind == "REQ":
            items.append(
                VItem(
                    rid,
                    "requirements",
                    "request",
                    title,
                    (),
                    cfg.requirements,
                    None,
                    "neutral",
                    "Request",
                    (),
                    about.get(rid, ""),
                )
            )
        else:
            items.append(
                VItem(
                    rid,
                    "requirements",
                    kind,
                    title,
                    ucs,
                    cfg.requirements,
                    None,
                    "ok" if ucs else "warn",
                    "Realised" if ucs else "No use case yet",
                    acs,
                    about.get(rid, ""),
                )
            )

    # system design: where each use case lives
    contexts: dict[str, list[str]] = {}
    for s in specs:
        contexts.setdefault(s.context or "Unassigned", []).append(s.uc)
    cmap = f"{cfg.docs.rstrip('/')}/{CONTEXT_MAP}"
    for name, ucs in sorted(contexts.items()):
        placed = name != "Unassigned"
        items.append(
            VItem(
                slug(name),
                "system-design",
                "context",
                name,
                tuple(ucs),
                cmap if ws.exists(cmap) else None,
                None,
                "ok" if placed else "warn",
                "Placed" if placed else "No context named",
                (),
                ("Holds " + ", ".join(by_uc[u].title for u in ucs) + ".")
                if placed
                else "These use cases name no bounded context.",
            )
        )

    # architecture: each context's domain model, and the class diagram of each use case
    models = context_files(cfg, ws)
    by_stem, _ = diagram_files(cfg, ws)
    for name, ucs in sorted(contexts.items()):
        have = models.get(slug(name))
        owed = any(by_uc[u].rigor == "full" for u in ucs)
        items.append(
            VItem(
                f"{slug(name)}-model",
                "architecture",
                "domain model",
                f"{name} domain model",
                tuple(ucs),
                have,
                None,
                "ok" if have else ("risk" if owed else "neutral"),
                "Drawn" if have else ("Missing" if owed else "None yet"),
                (),
                (diagram_title(ws.read(have)) if have else "")
                or (
                    f"The aggregates, entities and rules of the {name} context."
                    if have
                    else f"Not drawn yet; the full tier needs it for {name}."
                    if owed
                    else "Not needed below the full tier."
                ),
            )
        )
    for s in specs:
        for kind, phase, label in (
            ("class", "architecture", "class diagram"),
            ("sequence", "module-design", "sequence diagram"),
            ("state", "module-design", "state diagram"),
        ):
            for path in by_stem.get(s.stem, {}).get(kind, []):
                items.append(
                    VItem(
                        path,
                        phase,
                        label,
                        posixpath.basename(path),
                        (s.uc,),
                        path,
                        None,
                        "ok",
                        "Drawn",
                        (),
                        diagram_title(ws.read(path)) or f"The {kind} diagram of {s.title}.",
                    )
                )

    for uc, kinds in missing_diagrams(cfg, ws).items():  # a diagram it must have, shown where it belongs
        for kind in kinds:
            phase = "architecture" if kind == "class" else "module-design"
            title = f"{uc} {kind} diagram"
            why = f"The {by_uc[uc].rigor} tier needs a {kind} diagram of {by_uc[uc].title}; it is not drawn yet."
            items.append(
                VItem(
                    f"{uc}-missing-{kind}",
                    phase,
                    f"{kind} diagram",
                    title,
                    (uc,),
                    None,
                    None,
                    "risk",
                    "Missing",
                    (),
                    why,
                )
            )

    # module design: the task plan
    for tid, uc, desc, acs in tasks:
        need = [a for a in acs if a not in planned]
        closed = bool(need) and all(a in referenced for a in need)
        items.append(
            VItem(
                tid,
                "module-design",
                "task",
                desc,
                (uc,),
                by_uc[uc].path,
                None,
                "ok" if closed else "warn",
                "Closed" if closed else "Open",
                tuple(acs),
                f"Part of {by_uc[uc].title}; closes {', '.join(acs)}." if acs else f"Part of {by_uc[uc].title}.",
            )
        )

    # code
    by_file: dict[str, list[str]] = {}
    for uc, files in realised.items():
        for f in files:
            by_file.setdefault(f, []).append(uc)
    for f in sorted(by_file):
        ucs = tuple(sorted(by_file[f], key=natural_key))
        ok = all(u in verified for u in ucs)
        items.append(
            VItem(
                f,
                "code",
                "code",
                posixpath.basename(f),
                ucs,
                f,
                None,
                "ok" if ok else "warn",
                "Has a verifying test" if ok else "No verifying test",
                (),
                module_summary(f, ws.read(f))
                or f"Realises {', '.join(by_uc[u].title if u in by_uc else u for u in ucs)}.",
            )
        )

    # tests, by rung
    unplaced: list[VItem] = []
    for t in collect_test_cases(cfg, ws):
        if t.rung and t.ucs:
            n = len(t.acs)
            items.append(
                VItem(
                    t.id,
                    t.rung,
                    "test",
                    t.name,
                    t.ucs,
                    t.file,
                    t.line,
                    "ok" if n else "neutral",
                    f"Covers {n} criteri{'on' if n == 1 else 'a'}" if n else "No criterion marker",
                    t.acs,
                    t.doc or humanise(t.name),
                )
            )
        else:
            why = "Names no use case" if not t.ucs else "Names no level (unit, integration, system or acceptance)"
            unplaced.append(
                VItem(
                    t.id,
                    "unplaced",
                    "test",
                    t.name,
                    t.ucs,
                    t.file,
                    t.line,
                    "warn",
                    why,
                    t.acs,
                    t.doc or humanise(t.name),
                )
            )
    return items, unplaced
