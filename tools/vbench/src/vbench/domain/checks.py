"""The three deterministic checks, ported from the aiaas-mk3 `docs/tools/check_*.py` scripts.

    refs   every documentation cross-reference resolves        (the horizontal-trace rung)
    rungs  every UC realised in code has a verifying test      (the ascent: Realises -> Verifies)
    acs    every acceptance criterion has a marked test        (the finest rung: AC -> test)

They judge *existence* of a link, never test quality. A tautological test still closes a rung here;
that stays a human review concern. Verdicts come from parsing, never from an LLM.

The checks read the project only through the `Workspace` port.
"""

from __future__ import annotations

import posixpath
import re
from collections import defaultdict
from fnmatch import fnmatch

from ..ports import Workspace
from .config import Config
from .contexts import CONTEXT_MAP, USECASE_MAP, at, context_files
from .docsgen import stale_blocks
from .graph import enables, find_cycle, read_links, waves
from .junit import Run, read_run
from .model import Result, natural_key
from .pytests import read_python_tests
from .requirements_doc import read_criteria, read_requirements
from .specs import SpecInfo, read_specs, slug
from .steps import StepRow, cited, declared
from .usecase_map import render_usecase_map
from .vocabulary import confusions, names_in_diagram, read_terms

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
PUML_INCLUDE = re.compile(r"^\s*!include(?:sub)?\s+(\S+)", re.MULTILINE)
EXTERNAL = ("http://", "https://", "mailto:", "tel:")
REALISES = re.compile(r"Realises\s+([^\n]*)")
VERIFIES = re.compile(r"Verifies\s+([^\n]*)")
PLANNED = "(planned)"
FAKE = re.compile(r"(?:#|//|--|/\*)\s*FAKE:\s*(.*)")  # a scaffolded stand-in still in the code: `# FAKE: STP-A-001`
BUILT = "✅"  # the requirements doc's mark for "built and verified"


def _beside(path: str, rel: str) -> str:
    return posixpath.normpath(posixpath.join(posixpath.dirname(path), rel))


# --------------------------------------------------------------------------- refs
def check_refs(cfg: Config, ws: Workspace) -> Result:
    errors: list[str] = []

    for md in ws.files([cfg.docs], [".md"]):
        text = ws.read(md)
        for m in MD_LINK.finditer(text):
            raw = m.group(1)
            t = raw.strip()
            if not t or t.startswith(EXTERNAL) or t.startswith("#"):
                continue
            rel = t.split("#", 1)[0].strip().strip("'\"")
            if rel and not ws.exists(_beside(md, rel)):
                errors.append(f"{md}: broken link -> {raw}")
        for m in cfg.docs_ref_re.finditer(text):
            ref = m.group(0)
            if not ws.exists(ref):
                msg = f"{md}: inline path not found -> {ref}"
                if msg not in errors:
                    errors.append(msg)

    for puml in ws.files([cfg.docs], [".puml"]):
        for m in PUML_INCLUDE.finditer(ws.read(puml)):
            inc = m.group(1).strip()
            if not ws.exists(_beside(puml, inc)):
                errors.append(f"{puml}: missing !include -> {inc}")

    for src in ws.files(cfg.prod, cfg.prod_ext):
        seen: set[str] = set()
        for m in cfg.docs_ref_re.finditer(ws.read(src)):
            ref = m.group(0)
            if ref not in seen and not ws.exists(ref):
                seen.add(ref)
                errors.append(f"{src}: Spec ref not found -> {ref}")

    if errors:
        lines = ["Documentation reference-integrity check FAILED:", ""]
        lines += [f"  - {e}" for e in errors]
        lines += ["", f"{len(errors)} broken reference(s). Fix the link or the target."]
        return Result("refs", False, lines)
    return Result("refs", True, ["refs: all documentation cross-references resolve."])


# -------------------------------------------------------------------------- rungs
def _rung_of(clause: str) -> str:
    """'... · unit rung.' -> 'unit'."""
    tail = clause.rsplit("·", 1)[-1].strip().strip(".\"'")
    return tail[:-5].strip() if tail.endswith(" rung") else tail


def collect_realised(cfg: Config, ws: Workspace) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for p in ws.files(cfg.prod, cfg.prod_ext):
        for clause in REALISES.findall(ws.read(p)):
            for uc in cfg.uc_re.findall(clause):
                out[uc].add(p)
    return out


def _run(cfg: Config, ws: Workspace) -> Run:
    """The recorded test run, when the config names one (`results`); otherwise nothing, and the text is all there is."""
    return read_run(cfg.results, ws.read(cfg.results) if cfg.results and ws.exists(cfg.results) else None)


def _python_tests(cfg: Config, path: str, text: str, run: Run):
    """The structural reading of a Python test file, or None for any other file (or one that does not parse)."""
    if not path.endswith(".py"):
        return None
    return read_python_tests(cfg, text, VERIFIES, path, (lambda name: run.outcome(path, name)) if cfg.results else None)


def collect_verified(cfg: Config, ws: Workspace) -> dict[str, set[tuple[str, str]]]:
    """uc -> (test file, rung). In Python a tag counts only in a docstring with a real test behind it."""
    out: dict[str, set[tuple[str, str]]] = defaultdict(set)
    run = _run(cfg, ws)
    for p in ws.files(cfg.tests, cfg.test_ext):
        text = ws.read(p)
        parsed = _python_tests(cfg, p, text, run)
        clauses = [c for c, backed in parsed.clauses if backed] if parsed else VERIFIES.findall(text)
        for clause in clauses:
            rung = _rung_of(clause)
            for uc in cfg.uc_re.findall(clause):
                out[uc].add((p, rung))
    return out


def collect_hollow_verified(cfg: Config, ws: Workspace) -> dict[str, set[str]]:
    """uc -> test files that say `Verifies` in a docstring but have no real test behind it."""
    out: dict[str, set[str]] = defaultdict(set)
    run = _run(cfg, ws)
    for p in ws.files(cfg.tests, cfg.test_ext):
        parsed = _python_tests(cfg, p, ws.read(p), run)
        for clause, backed in parsed.clauses if parsed else ():
            if not backed:
                for uc in cfg.uc_re.findall(clause):
                    out[uc].add(p)
    return out


def check_rungs(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    realised, verified = collect_realised(cfg, ws), collect_verified(cfg, ws)
    if matrix:
        rows = ["| Use case | Realised in | Verified by (rung) |", "| --- | --- | --- |"]
        for uc in sorted(realised, key=natural_key):
            prod = "<br>".join(sorted(realised[uc]))
            tests = verified.get(uc)
            cell = (
                "<br>".join(f"{p} ({r})" for p, r in sorted(tests, key=lambda t: t[0]))
                if tests
                else "**OPEN: no test**"
            )
            rows.append(f"| {uc} | {prod} | {cell} |")
        return Result("rungs", True, rows)

    hollow = collect_hollow_verified(cfg, ws)
    open_ = sorted((u for u in realised if u not in verified), key=natural_key)
    untagged = untagged_production(cfg, ws, realised)
    if open_ or untagged:
        if open_:
            lines = ["Verification check FAILED: use cases with code but no test that verifies them:", ""]
        else:
            lines = ["Verification check FAILED:", ""]
        for uc in open_:
            where = ", ".join(sorted(realised[uc]))
            lines.append(f"  - {uc}: realised in {where}, but no test `Verifies {uc}`.")
            for f in sorted(hollow.get(uc, ())):
                lines.append(f"      {f} says it, but no real test stands behind the docstring (a test that asserts).")
        if untagged:
            lines += ["", "Production code that realises no use case (code nobody asked for passes every gate):"]
            lines += [f"  - {p}: no `Realises UC-…` tag." for p in untagged]
        lines.append("")
        if open_:
            lines.append(
                f"{len(open_)} open rung(s). Add a `Verifies {open_[0]} · <rung> rung.` docstring to the "
                "covering test, or write the missing test."
            )
        if untagged:
            lines.append(
                f"{len(untagged)} untagged file(s). Tag the code `Realises UC-…`, delete it, or list it under "
                "`untagged_ok` in .vbench/config.toml (a package `__init__.py` is always allowed)."
            )
        return Result("rungs", False, lines)
    return Result("rungs", True, [f"rungs: all {len(realised)} realised use case(s) have a verifying test."])


def untagged_production_files(cfg: Config, ws: Workspace, realised: dict[str, set[str]]) -> list[str]:
    tagged = {p for files in realised.values() for p in files}
    return [
        p
        for p in ws.files(cfg.prod, cfg.prod_ext)
        if p not in tagged
        and posixpath.basename(p) != "__init__.py"
        and not any(fnmatch(p, g) for g in cfg.untagged_ok)
    ]


untagged_production = untagged_production_files


# ----------------------------------------------------------------------------- acs
def collect_declared(cfg: Config, ws: Workspace) -> tuple[dict[str, str], set[str]]:
    declared: dict[str, str] = {}
    planned: set[str] = set()
    for md in ws.files([cfg.specs], [".md"]):
        for m in cfg.ac_decl_re.finditer(ws.read(md)):
            ac, rest = m.group(1), m.group(2)
            declared[ac] = md
            if PLANNED in rest.lower():
                planned.add(ac)
    return declared, planned


def collect_unspecified(cfg: Config, ws: Workspace) -> set[str]:
    """AC rows still marked TBD: declared by the scaffold but not yet written by `/vbench:v-1-requirements`."""
    out: set[str] = set()
    for md in ws.files([cfg.specs], [".md"]):
        for m in cfg.ac_decl_re.finditer(ws.read(md)):
            if "tbd" in m.group(2).lower():
                out.add(m.group(1))
    return out


def _marked(cfg: Config, ws: Workspace) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """(AC -> files with a real test marking it, AC -> `file::test` entries marking it with a hollow one)."""
    real: dict[str, set[str]] = defaultdict(set)
    hollow: dict[str, set[str]] = defaultdict(set)
    run = _run(cfg, ws)
    for p in ws.files(cfg.tests, cfg.test_ext):
        text = ws.read(p)
        parsed = _python_tests(cfg, p, text, run)
        if parsed is None:
            for call in cfg.ac_mark_re.findall(text):
                for ac in cfg.ac_re.findall(call):
                    real[ac].add(p)
            continue
        for fn in parsed.functions:
            for ac in fn.acs:
                if fn.real:
                    real[ac].add(p)
                else:
                    hollow[ac].add(f"{p}::{fn.name} ({fn.why})")
    return real, hollow


def collect_referenced(cfg: Config, ws: Workspace) -> dict[str, set[str]]:
    """AC -> test files. In Python the marker counts only on a real test function (see `domain/pytests.py`)."""
    return _marked(cfg, ws)[0]


def collect_hollow(cfg: Config, ws: Workspace) -> dict[str, set[str]]:
    return _marked(cfg, ws)[1]


def check_acs(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    declared, planned = collect_declared(cfg, ws)
    referenced = collect_referenced(cfg, ws)
    if matrix:
        rows = ["| Acceptance criterion | Declared in | Validated by |", "| --- | --- | --- |"]
        for ac in sorted(declared, key=natural_key):
            tests = referenced.get(ac)
            if tests:
                cell = "<br>".join(sorted(tests))
            elif ac in planned:
                cell = "_(planned: not yet enforced)_"
            else:
                cell = "**UNCOVERED: no test**"
            rows.append(f"| {ac} | {declared[ac]} | {cell} |")
        return Result("acs", True, rows)

    uncovered = sorted((a for a in declared if a not in referenced and a not in planned), key=natural_key)
    orphans = sorted((a for a in referenced if a not in declared), key=natural_key)
    if uncovered or orphans:
        lines = ["Acceptance-criteria coverage check FAILED:", ""]
        hollow = collect_hollow(cfg, ws)
        for a in uncovered:
            lines.append(f"  - UNCOVERED {a}: declared in {declared[a]}, no test marks it.")
            for h in sorted(hollow.get(a, ())):
                lines.append(f"      marked only on {h}: that does not count.")
        for a in orphans:
            where = ", ".join(sorted(referenced[a]))
            lines.append(f"  - ORPHAN {a}: marked in {where}, but no spec declares it (typo? deleted?).")
        lines += [
            "",
            f'{len(uncovered)} uncovered, {len(orphans)} orphan. Add `{cfg.ac_marker}("AC-…")` to the '
            "covering test, or fix the id.",
        ]
        return Result("acs", False, lines)
    enforced = len(declared) - len(planned)
    return Result(
        "acs",
        True,
        [f"acs: all {enforced} enforced criterion(s) validated by a test ({len(planned)} planned, skipped)."],
    )


# ---------------------------------------------------------------------------------------------------- fakes
def check_fakes(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    """A `# FAKE:` marker is a scaffolded stand-in: code holding one is not finished, whatever its tests say."""
    found: list[tuple[str, int, str]] = []
    for p in ws.files(cfg.prod, cfg.prod_ext):
        for n, line in enumerate(ws.read(p).splitlines(), start=1):
            if m := FAKE.search(line):
                found.append((p, n, m.group(1).strip()))
    if matrix:
        rows = ["| File | Line | Stands in for |", "| --- | --- | --- |"]
        rows += [f"| {p} | {n} | {what or '-'} |" for p, n, what in found]
        return Result("fakes", True, rows)
    if not found:
        return Result("fakes", True, ["fakes: no scaffolded stand-in is left in the production code."])
    lines = ["Fake check FAILED: production code still holds scaffolded stand-ins (`# FAKE:`):", ""]
    lines += [f"  - {p}:{n}: {what or 'a fake'}" for p, n, what in found]
    lines += ["", f"{len(found)} fake(s). Replace each with the real step (test first), then remove the marker."]
    return Result("fakes", False, lines)


# ------------------------------------------------------------------------------------------- requirements
def check_requirements(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    """A requirement marked built (✅) must have a criterion that a real test validates, or the mark is a claim."""
    doc = read_requirements(cfg, ws)
    criteria = read_criteria(cfg, ws)
    referenced = collect_referenced(cfg, ws)
    hollow = collect_hollow(cfg, ws)
    rows = ["| Requirement | Marked | Criteria validated by a real test |", "| --- | --- | --- |"]
    problems: list[str] = []
    for fr in doc.functional:
        mine = sorted((a for a, c in criteria.items() if fr.id in c.satisfies), key=natural_key)
        validated = [a for a in mine if a in referenced]
        rows.append(f"| {fr.id} | {fr.maturity or '-'} | {', '.join(validated) or '**none**'} |")
        if BUILT not in fr.maturity or validated:
            continue
        if not mine:
            problems.append(f"  - {fr.id} is marked built, but no acceptance criterion satisfies it.")
        else:
            problems.append(f"  - {fr.id} is marked built, but no real test validates {', '.join(mine)}.")
            problems += [f"      {a}: marked only on {h}" for a in mine for h in sorted(hollow.get(a, ()))]
    if matrix:
        return Result("requirements", True, rows)
    if problems:
        lines = ["Requirements check FAILED: marked built (✅) with nothing verifying them:", "", *problems]
        lines += ["", "Write the test, or set the mark back to 🟡 or ⚪ until it exists."]
        return Result("requirements", False, lines)
    built = sum(BUILT in fr.maturity for fr in doc.functional)
    return Result(
        "requirements", True, [f"requirements: all {built} requirement(s) marked built have a validated criterion."]
    )


# ----------------------------------------------------------------------- diagrams
DIAGRAMS_ROW = re.compile(r"^\|\s*\*\*Diagrams\*\*\s*\|(.*)\|\s*$", re.MULTILINE)
RIGOR_ROW = re.compile(r"^\|\s*\*\*Rigor\*\*\s*\|\s*([A-Za-z]+)", re.MULTILINE)
KINDS = ("sequence", "class", "state")
REQUIRED_BY_RIGOR = {"light": (), "standard": ("sequence",), "full": ("sequence", "class")}


def _diagram_re(cfg: Config) -> re.Pattern[str]:
    return re.compile(rf"^(?P<stem>{cfg.uc_pattern}-[\w-]+)-(?P<kind>{'|'.join(KINDS)})(?:\.\d+)?\.puml$")


def _diagram_files(cfg: Config, ws: Workspace) -> tuple[dict[str, dict[str, list[str]]], list[str]]:
    """({spec stem: {kind: [paths]}}, [paths whose names fit no spec]). `_`-prefixed files are shared includes."""
    stems = {
        posixpath.basename(p)[:-3]
        for p in ws.files([cfg.specs], [".md"])
        if posixpath.basename(p).startswith("UC-") and cfg.uc_re.match(posixpath.basename(p))
    }
    by_stem: dict[str, dict[str, list[str]]] = {s: {k: [] for k in KINDS} for s in stems}
    stray: list[str] = []
    rx = _diagram_re(cfg)
    for path in ws.files([cfg.specs], [".puml"]):
        name = posixpath.basename(path)
        if name.startswith("_"):
            continue
        m = rx.match(name)
        if m and m.group("stem") in by_stem:
            by_stem[m.group("stem")][m.group("kind")].append(path)
        else:
            stray.append(path)
    return by_stem, stray


def _designed(tasks: dict[str, tuple[str, list[str]]], spec: SpecInfo) -> bool:
    """Has this use case a task that names a criterion? A task belongs to the spec that declares it."""
    return any(acs for path, acs in tasks.values() if path == spec.path)


def required_kinds(spec: SpecInfo) -> tuple[str, ...]:
    """The diagram kinds this use case must have: its rigor tier's, plus the state diagram when it has a lifecycle."""
    kinds = REQUIRED_BY_RIGOR.get(spec.rigor, ())
    return (*kinds, "state") if spec.lifecycle == "yes" else kinds


def missing_diagrams(cfg: Config, ws: Workspace) -> dict[str, list[str]]:
    """uc -> the diagram kinds it must have that are not on disk. Only for designed use cases."""
    by_stem, _ = _diagram_files(cfg, ws)
    tasks, out = collect_tasks(cfg, ws), {}
    for s in read_specs(cfg, ws):
        if s.stem not in by_stem or not _designed(tasks, s):
            continue
        need = [k for k in required_kinds(s) if not by_stem[s.stem][k]]
        if need:
            out[s.uc] = need
    return out


def lifecycle_undecided(cfg: Config, ws: Workspace) -> set[str]:
    """Designed use cases at the full tier whose `Lifecycle` row is still a placeholder: `yes` needs a state diagram,
    `none` says there is no lifecycle. The full tier makes the decision explicit rather than leaving it to review."""
    tasks = collect_tasks(cfg, ws)
    return {s.uc for s in read_specs(cfg, ws) if s.rigor == "full" and not s.lifecycle and _designed(tasks, s)}


def _designed_specs(cfg: Config, ws: Workspace):
    tasks = collect_tasks(cfg, ws)
    return [s for s in read_specs(cfg, ws) if _designed(tasks, s)]


def missing_system_diagrams(cfg: Config, ws: Workspace) -> dict[str, list[str]]:
    """uc -> the system-level diagrams still owed: the domain model of its context at the full tier, and the
    context map once two or more contexts have designed use cases. Only for designed use cases."""
    designed = _designed_specs(cfg, ws)
    contexts = {s.context for s in designed if s.context}
    files, out = context_files(cfg, ws), {}
    map_missing = len(contexts) >= 2 and not ws.exists(at(cfg, CONTEXT_MAP))
    for s in designed:
        owed = []
        if s.rigor == "full" and s.context and slug(s.context) not in files:
            owed.append(f"domain model for context {s.context}")
        if map_missing and s.context:
            owed.append("context map")
        if owed:
            out[s.uc] = owed
    return out


def check_diagrams(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    """PlantUML companions: named `<spec>-<kind>.puml`, present as the rigor tier requires, linked from the spec,
    and well formed. Proves the files exist and have the right shape, never that the diagram is right."""
    by_stem, stray = _diagram_files(cfg, ws)
    missing = missing_diagrams(cfg, ws)
    specs = {
        posixpath.basename(p)[:-3]: p for p in ws.files([cfg.specs], [".md"]) if posixpath.basename(p)[:-3] in by_stem
    }
    if matrix:
        rows = ["| Use case | Rigor | Lifecycle | Required | Present |", "| --- | --- | --- | --- | --- |"]
        info = {s.stem: s for s in read_specs(cfg, ws)}
        for stem in sorted(specs, key=natural_key):
            s = info[stem]
            present = [k for k in KINDS if by_stem[stem][k]]
            rows.append(
                f"| {stem} | {s.rigor} | {s.lifecycle or 'undecided'} | {', '.join(required_kinds(s)) or '-'} "
                f"| {', '.join(present) or '-'} |"
            )
        return Result("diagrams", True, rows)

    errors = [f"{p}: name fits no spec; expected `<spec-file-name>-{'|'.join(KINDS)}[.n].puml`" for p in stray]
    errors += [
        f"{uc}: the full tier needs a Lifecycle decision: set the Lifecycle row to `yes` (and draw the state diagram) "
        "or to `none`"
        for uc in sorted(lifecycle_undecided(cfg, ws), key=natural_key)
    ]
    designed = _designed_specs(cfg, ws)
    for uc, owed in sorted(missing_system_diagrams(cfg, ws).items(), key=lambda kv: natural_key(kv[0])):
        errors.append(
            f'{uc}: still owes {", ".join(owed)}: `vbench new context --name "<Context>"` / `vbench new context-map`'
        )
    names = {s.context for s in designed if s.context}
    cmap = at(cfg, CONTEXT_MAP)
    if len(names) >= 2 and ws.exists(cmap):
        text = ws.read(cmap).lower()
        errors += [f"{cmap}: does not mention context {n}" for n in sorted(names) if n.lower() not in text]
    for path in [*context_files(cfg, ws).values(), *([cmap] if ws.exists(cmap) else [])]:
        text = ws.read(path)
        if "@startuml" not in text or "@enduml" not in text:
            errors.append(f"{path}: missing @startuml / @enduml")
    umap = at(cfg, USECASE_MAP)
    if by_stem:
        if not ws.exists(umap):
            errors.append(f"{umap}: missing; run `vbench sync`")
        elif ws.read(umap) != render_usecase_map(cfg, ws):
            errors.append(f"{umap}: out of date with the specs; run `vbench sync`")
    for uc, kinds in sorted(missing.items(), key=lambda kv: natural_key(kv[0])):
        errors.append(f"{uc}: its rigor tier requires a {', '.join(kinds)} diagram (see `/vbench:v-2-design`)")
    for stem, kinds in by_stem.items():
        row = DIAGRAMS_ROW.search(ws.read(specs[stem]))
        for paths in kinds.values():
            for p in paths:
                name = posixpath.basename(p)
                if not row or name not in row.group(1):
                    errors.append(f"{specs[stem]}: the Diagrams row does not link {name}")
                text = ws.read(p)
                if "@startuml" not in text or "@enduml" not in text:
                    errors.append(f"{p}: missing @startuml / @enduml")
    if errors:
        lines = ["Diagram check FAILED:", ""] + [f"  - {e}" for e in errors]
        return Result("diagrams", False, [*lines, "", f"{len(errors)} problem(s)."])
    n = sum(len(v) for k in by_stem.values() for v in k.values())
    return Result(
        "diagrams", True, [f"diagrams: {n} diagram(s) named, linked and well formed; none missing for the rigor tiers."]
    )


# ---------------------------------------------------------------------------- steps
def collect_step_rows(cfg: Config, ws: Workspace) -> tuple[list[StepRow], list[str]]:
    """Every step a sequence diagram declares, with the tasks, code and tests that cite it, in diagram order, and
    the problems met on the way: an id declared twice, or cited where it does not exist or belongs elsewhere."""
    problems: list[str] = []
    by_stem, _ = _diagram_files(cfg, ws)
    rows: dict[str, StepRow] = {}
    for stem in sorted(by_stem, key=natural_key):
        uc = cfg.uc_re.match(stem).group(0)  # type: ignore[union-attr]
        for path in sorted(by_stem[stem]["sequence"]):
            for st in declared(cfg, uc, path, ws.read(path)):
                if st.id in rows and rows[st.id].step.path != path:
                    problems.append(
                        f"{st.id}: declared in both {rows[st.id].step.path} and {path}; a step id is unique"
                    )
                elif st.id not in rows:
                    rows[st.id] = StepRow(st)

    def known(sid: str, uc_ids: list[str], where: str) -> bool:
        if sid not in rows:
            problems.append(f"{where}: {sid} is in no sequence diagram")
            return False
        if uc_ids and rows[sid].step.uc not in uc_ids:
            problems.append(f"{where}: {sid} belongs to {rows[sid].step.uc}, not {', '.join(uc_ids)}")
            return False
        return True

    owner = {path: uc for uc, path in spec_files(cfg, ws).items()}
    for md in ws.files([cfg.specs], [".md"]):
        for m in cfg.task_decl_re.finditer(ws.read(md)):
            for sid in cfg.step_re.findall(m.group(2)):
                if known(sid, [owner[md]] if md in owner else [], f"{md}: task {m.group(1)}"):
                    rows[sid].tasks.append(m.group(1))
    for p in ws.files(cfg.prod, cfg.prod_ext):
        for n, line in enumerate(ws.read(p).splitlines(), 1):
            m = REALISES.search(line)
            if m:
                ucs, sids = cited(cfg, m.group(1))
                for sid in sids:
                    if known(sid, ucs, f"{p}:{n}"):
                        rows[sid].code.append((p, n))
    run = _run(cfg, ws)
    for p in ws.files(cfg.tests, cfg.test_ext):
        text = ws.read(p)
        parsed = _python_tests(cfg, p, text, run)
        for clause, backed in parsed.clauses if parsed else [(c, True) for c in VERIFIES.findall(text)]:
            ucs, sids = cited(cfg, clause)
            for sid in sids:
                if known(sid, ucs, p):
                    mine = rows[sid].tests if backed else rows[sid].hollow
                    if p not in mine:
                        mine.append(p)
    return list(rows.values()), problems


def step_rows_of(cfg: Config, ws: Workspace, uc: str) -> list[StepRow]:
    """The steps of one use case in diagram order, for `vbench trace`."""
    return [r for r in collect_step_rows(cfg, ws)[0] if r.step.uc == uc]


def check_steps(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    """Step ids tie a use case's sequence diagram to its tasks, code and tests. A diagram opts in by numbering its
    messages; from then on every step must be cited by a task, and once the use case has code, tagged in the code
    and driven by a real test. A step marked `(planned)` owes no code or test yet. Existence, not quality."""
    rows, errors = collect_step_rows(cfg, ws)
    if matrix:
        table = ["| Step | Use case | Message | Task | Code | Test |", "| --- | --- | --- | --- | --- | --- |"]
        for r in rows:
            s = r.step
            table.append(
                f"| {s.id} | {s.uc} | {s.label}{' (planned)' if s.planned else ''} | {', '.join(r.tasks) or '-'} "
                f"| {'<br>'.join(f'{p}:{n}' for p, n in r.code) or '-'} | {'<br>'.join(r.tests) or '-'} |"
            )
        return Result("steps", True, table)

    realised, tasks = collect_realised(cfg, ws), collect_tasks(cfg, ws)
    specs = {s.uc: s for s in read_specs(cfg, ws)}
    for r in rows:
        s = r.step
        if s.planned:
            continue
        if s.uc in specs and _designed(tasks, specs[s.uc]) and not r.tasks:
            errors.append(f"{s.id} ({s.uc}): no task row cites it; name it in the Delivery tasks table")
        if s.uc in realised and not r.code:
            errors.append(f"{s.id} ({s.uc}): the use case has code, but nothing says `Realises {s.uc} · {s.id}`")
        if s.uc in realised and not r.tests:
            why = f" ({', '.join(r.hollow)} says it, but no real test stands behind the docstring)" if r.hollow else ""
            errors.append(f"{s.id} ({s.uc}): no test says `Verifies {s.uc} · {s.id} · <rung> rung.`{why}")
    if errors:
        lines = ["Step check FAILED:", ""] + [f"  - {e}" for e in errors]
        return Result(
            "steps", False, [*lines, "", f"{len(errors)} problem(s). `vbench trace <UC>` shows each step's chain."]
        )
    ucs = {r.step.uc for r in rows}
    if not rows:
        return Result("steps", True, ["steps: no sequence diagram numbers its messages yet (optional until one does)."])
    return Result(
        "steps",
        True,
        [f"steps: {len(rows)} step(s) in {len(ucs)} use case(s), each cited and, where built, tagged and tested."],
    )


# ----------------------------------------------------------------------- vocabulary
def check_vocabulary(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    """A diagram does not draw a word the vocabulary says is not the project's term (`Not to be confused with`).
    Only that direction is judged: a name with no term is allowed, since a diagram also draws infrastructure."""
    terms = read_terms(cfg, ws)
    skip = at(cfg, USECASE_MAP)
    errors = []
    for path in ws.files([cfg.docs], [".puml"]):
        if posixpath.basename(path).startswith("_") or path == skip:
            continue
        for name, bad, term in confusions(terms, names_in_diagram(ws.read(path))):
            errors.append(f'{path}: "{name}" uses "{bad}", which the vocabulary says is not "{term}"')
    if matrix:
        rows = ["| Term | Context | Not to be confused with |", "| --- | --- | --- |"]
        rows += [f"| {t.name} | {t.context or '-'} | {', '.join(t.confusable) or '-'} |" for t in terms]
        return Result("vocabulary", True, rows)
    if errors:
        lines = ["Vocabulary check FAILED:", ""] + [f"  - {e}" for e in errors]
        return Result(
            "vocabulary", False, [*lines, "", f"{len(errors)} problem(s). Use the project's term, or fix the table."]
        )
    return Result(
        "vocabulary", True, [f"vocabulary: {len(terms)} term(s); no diagram draws a word the vocabulary rules out."]
    )


def check_ontology(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    """The generated ontology files that exist match a fresh render. Writing them is optional."""
    from .ontology import FORMATS, build_ontology, file_name, render  # imports this module, so it is read late

    present = [f for f in FORMATS if ws.exists(f"{cfg.ontology}/{file_name(f)}")]
    if matrix:
        rows = ["| Format | File | State |", "| --- | --- | --- |"]
        rows += [
            f"| {f} | {cfg.ontology}/{file_name(f)} | {'present' if f in present else 'not generated'} |"
            for f in FORMATS
        ]
        return Result("ontology", True, rows)
    if not present:
        return Result("ontology", True, ["ontology: not generated (optional; `vbench ontology --write`)."])
    fresh = build_ontology(cfg, ws)
    stale = [
        f"{cfg.ontology}/{file_name(f)}"
        for f in present
        if ws.read(f"{cfg.ontology}/{file_name(f)}") != render(fresh, f)
    ]
    if stale:
        lines = ["Ontology check FAILED:", ""] + [f"  - {p} is out of date with the project" for p in stale]
        return Result("ontology", False, [*lines, "", "Run `vbench ontology --write` (or `vbench sync`)."])
    return Result("ontology", True, [f"ontology: {len(present)} generated file(s) match the project."])


# ---------------------------------------------------------------------------- docs
def check_docs(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    """Generated blocks in the requirements and backlog docs match the specs they are derived from."""
    stale = stale_blocks(cfg, ws)
    if matrix:
        rows = ["| Document | Block | State |", "| --- | --- | --- |"]
        rows += [f"| {d} | {n} | stale |" for d, n in stale] or ["| (all generated blocks) | | up to date |"]
        return Result("docs", True, rows)
    if stale:
        lines = ["Generated-docs check FAILED:", ""]
        lines += [f"  - {d}: block `{n}` is out of date with the specs" for d, n in stale]
        return Result(
            "docs",
            False,
            [*lines, "", f"{len(stale)} stale block(s). Run `vbench sync`; do not edit inside the markers."],
        )
    return Result("docs", True, ["docs: every generated block matches the specs."])


# --------------------------------------------------------------------------- links
def check_links(cfg: Config, ws: Workspace, matrix: bool = False) -> Result:
    """Every `Depends on` names a use case that has a spec, none names itself, and there is no cycle."""
    deps = read_links(cfg, ws)
    if matrix:
        wave, back = waves(deps), enables(deps)
        rows = ["| Use case | Wave | Depends on | Enables |", "| --- | --- | --- | --- |"]
        for uc in sorted(deps, key=lambda u: (wave[u], natural_key(u))):
            rows.append(
                f"| {uc} | {wave[uc]} | {', '.join(deps[uc]) or '-'} "
                f"| {', '.join(sorted(back[uc], key=natural_key)) or '-'} |"
            )
        return Result("links", True, rows)

    errors: list[str] = []
    for uc in sorted(deps, key=natural_key):
        for d in deps[uc]:
            if d == uc:
                errors.append(f"{uc}: depends on itself")
            elif d not in deps:
                errors.append(f"{uc}: depends on {d}, which has no spec under {cfg.specs}")
    cycle = find_cycle(deps)
    if cycle:
        errors.append("dependency cycle: " + " -> ".join(cycle))
    if errors:
        lines = ["Use-case dependency check FAILED:", ""] + [f"  - {e}" for e in errors]
        lines += ["", f"{len(errors)} problem(s). Fix the `Depends on` row in the spec header."]
        return Result("links", False, lines)
    edges = sum(len(v) for v in deps.values())
    return Result(
        "links", True, [f"links: {len(deps)} use case(s), {edges} dependency link(s), no cycles or dangling ids."]
    )


diagram_files = _diagram_files  # the public name, used by the V view

CHECKS = {
    "refs": check_refs,
    "rungs": check_rungs,
    "acs": check_acs,
    "requirements": check_requirements,
    "fakes": check_fakes,
    "links": check_links,
    "diagrams": check_diagrams,
    "steps": check_steps,
    "vocabulary": check_vocabulary,
    "ontology": check_ontology,
    "docs": check_docs,
}


# ------------------------------------------------------------------------ commits
SKIPPED_SUBJECTS = ("Merge ", "Revert ", "fixup! ", "squash! ")
RELEASE_BRANCH = re.compile(r"^release/[\w.-]+$")


def collect_tasks(cfg: Config, ws: Workspace) -> dict[str, tuple[str, list[str]]]:
    """Declared tasks: id -> (spec path, the AC ids the task closes)."""
    out: dict[str, tuple[str, list[str]]] = {}
    for md in ws.files([cfg.specs], [".md"]):
        for m in cfg.task_decl_re.finditer(ws.read(md)):
            out[m.group(1)] = (md, cfg.ac_re.findall(m.group(2)))
    return out


def spec_files(cfg: Config, ws: Workspace) -> dict[str, str]:
    """Use case id -> the path of its spec, from the file names under the specs folder."""
    return {
        m.group(0): p
        for p in ws.files([cfg.specs], [".md"])
        if posixpath.basename(p).startswith("UC-") and (m := cfg.uc_re.match(posixpath.basename(p)))
    }


def _owns(tasks: dict[str, tuple[str, list[str]]], spec_path: str, task: str) -> bool:
    return task in tasks and tasks[task][0] == spec_path


def check_commits(cfg: Config, ws: Workspace, subjects: list[str], branch: str = "") -> Result:
    """Commit subjects and the branch name follow the convention, and cite specs and tasks that exist."""
    tasks = collect_tasks(cfg, ws)
    specs = spec_files(cfg, ws)
    shape = f"<{'|'.join(cfg.commit_types)}>(<UC-id>[/<TSK-id>])[!]: <description>"
    errors: list[str] = []

    if branch and branch != cfg.base_branch and not RELEASE_BRANCH.match(branch) and not cfg.branch_re.match(branch):
        errors.append(f"branch `{branch}`: expected `<type>/<slug>` with type one of {', '.join(cfg.commit_types)}")
    for subject in subjects:
        if subject.startswith(SKIPPED_SUBJECTS):
            continue
        m = cfg.commit_re.match(subject)
        if not m:
            errors.append(f"`{subject}`: does not match {shape}")
            continue
        g = m.groupdict()
        uc, task = g.get("uc"), g.get("task")
        if g.get("type") != "chore" and not uc:
            errors.append(f"`{subject}`: only chore may omit the use-case id")
        elif uc and uc not in specs:
            errors.append(f"`{subject}`: no spec for {uc} under {cfg.specs}")
        elif uc and task and not _owns(tasks, specs[uc], task):
            errors.append(f"`{subject}`: {task} is not in {uc}'s task table; add the row first")

    if errors:
        lines = ["Commit and branch convention check FAILED:", ""]
        lines += [f"  - {e}" for e in errors]
        lines += ["", f"{len(errors)} problem(s). Reword the commit (`git rebase -i`) or fix the spec, then re-run."]
        return Result("commits", False, lines)
    return Result("commits", True, [f"commits: {len(subjects)} commit(s) and the branch follow the convention."])
