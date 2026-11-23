#!/usr/bin/env python3
"""vcycle.py: follow the recorded links of a use case down the left of the V (requirement, criterion, flow and
analysis, rule, design, slice) and up the right (the tests, the diagrams, the review), and say what is proved, what is
not, and what a person still has to do.

  vcycle.py UC-A1                one use case, a table with one row for each level of the V
  vcycle.py --all                every use case, and a summary
  vcycle.py UC-A1 --strict       warnings fail too (unstamped, stack run only, no analysis frozen)
  vcycle.py UC-A1 --json         the same, as data, with the commit it was run on (keep it as a record of the run)
  --tests-dir DIR                where the tests live (default: tests_dirs in vbench.json)

Each row is ok, warn or FAIL. FAIL: a criterion or listed rule or security criterion with no test, an analysis element with no log entry,
a stale review hash, a bad slice. warn: only the stack run covers it, not stamped, not frozen, a missing diagram.
The exit code is 1 when anything FAILS (with --strict, when anything warns too). It reads files and runs nothing: it
says that a tagged test EXISTS, not that it passes or that it is any good. Use it with the test runs, never instead.
It never edits a file. It uses only the standard library and the other vbench tools.
"""

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve()
for skill in ("vbench-uc", "vbench-at", "vbench-req"):
    sys.path.insert(0, str(HERE.parents[2] / skill / "scripts"))
import at_tool as at  # noqa: E402
import req_tool as rq  # noqa: E402
import uc_tool as uc  # noqa: E402

OK, WARN, FAIL = "ok", "warn", "FAIL"
# Why a criterion is or is not proved, and how each reason is shown. FAILING reasons fail the row; WARNING ones warn.
LABELS = {"tested": "tested", "stack run": "stack run", "deferred": "deferred", "no test": "no test",
          "stale": "stale test hash (the criterion changed since the test was reviewed)",
          "empty": "no assertion in the test", "combined": "covered only by a combined tag (one tag names several criteria)",
          "not live": "listed but retired or missing", "deferred, no decision": "deferred, no decision cited"}
FAILING = ("no test", "stale", "not live")
WARNING = ("stack run", "empty", "combined", "deferred, no decision")
LABELS.update({"failing": "the test failed in the last run",
               "no result": "no result for the test in the last run (or it was skipped)"})
FAILING = FAILING + ("failing",)
WARNING = WARNING + ("no result",)
# Which pack of the harness a row belongs to. A row of a pack that is off in vbench.json is left out, not warned.
PACK_OF = {"Requirements": "core", "Criteria": "core", "Analysis": "ddd", "Rules": "ddd", "Design": "ddd",
           "Slices": "core", "Security": "security", "Review": "core"}
BASELINE = ".claude/vbench-baseline.json"
LEGACY = "legacy"
SECURITY = re.compile(r"^\s*security\b|\bSEC-[A-Z]+-\d+\b", re.IGNORECASE)  # a note that starts `security`, or names a SEC- check


def _row(level, spec, proof, status, detail=""):
    return {"level": level, "spec": spec, "proof": proof, "status": status, "detail": detail}


def _commit(root):
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def load_results(root, paths):
    """The test cases of the JUnit XML file(s): [{classname, name, outcome}], or None when no file is configured."""
    if not paths:
        return None
    out, read = [], 0
    for path in ([paths] if isinstance(paths, str) else paths):
        f = Path(path) if Path(path).is_absolute() else root / path
        try:
            tree = ET.parse(f)
        except (OSError, ET.ParseError):
            continue  # a file that is not there yet is not a failing test: the trace falls back to existence only
        read += 1
        for case in tree.iter("testcase"):
            kind = "failed" if case.find("failure") is not None or case.find("error") is not None else \
                "skipped" if case.find("skipped") is not None else "passed"
            out.append({"classname": case.get("classname", ""), "name": case.get("name", ""), "outcome": kind})
    return out if read else None


def outcome_of(root, tag, results):
    """passed, failed, skipped, or None (no result) for the test a tag sits on."""
    hits = []
    if str(tag.path).endswith(".py"):
        try:
            mod = Path(tag.path).resolve().relative_to(root.resolve()).with_suffix("").as_posix().replace("/", ".")
        except ValueError:
            mod = Path(tag.path).stem
        for r in results:
            names = {r["classname"], r["classname"].rsplit(".", 1)[0]}
            if re.sub(r"\[.*\]$", "", r["name"]) == tag.name and any(mod == c or mod.endswith("." + c) for c in names if c):
                hits.append(r["outcome"])
    else:
        rx = re.compile(rf"(?<![A-Za-z0-9-]){re.escape(tag.id)}(?![A-Za-z0-9-])")
        hits = [r["outcome"] for r in results if rx.search(r["name"])]
    return "failed" if "failed" in hits else "passed" if "passed" in hits else "skipped" if hits else None


def area_of(uid):
    m = re.match(r"UC-([A-Z]+)", uid)
    return m.group(1) if m else ""


def adoption_of(cfg, uid):
    a = cfg.get("adoption") or {}
    return a.get(area_of(uid), a.get("default", "adopted"))


def settle(rows, uid, cfg, baseline):
    """The packs that are on, then the baseline (a known gap warns), then how far the area is adopted
    (legacy: observed only; adopting: a failure warns; adopted: as it is)."""
    packs = cfg.get("packs") or list(PACK_OF.values())
    rows = [r for r in rows if PACK_OF.get(r["level"], "core") in packs]
    known = (baseline or {}).get("gaps", {}).get(uid, {})
    state = adoption_of(cfg, uid)
    for r in rows:
        if r["status"] == FAIL and known.get(r["level"]) == r["detail"]:
            r["status"], r["detail"] = WARN, f"known gap (baseline): {r['detail']}"
        if state == "legacy" and r["status"] in (WARN, FAIL):
            r["status"], r["detail"] = LEGACY, f"legacy, observed only: {r['detail']}"
        elif state == "adopting" and r["status"] == FAIL:
            r["status"], r["detail"] = WARN, f"adopting: {r['detail']}"
    return rows


def check(root, uid, dirs, cfg=None, results=None):
    """The rows of the V for one use case, or None when there is no such use case."""
    cfg = cfg or rq.use_config(root)
    reqs, acs, ucs = uc.load(root)
    found = [(p, h, text) for p, h, text in ucs if h.get("id") == uid]
    if not found:
        return None
    _, h, text = found[0]
    acs_by_id = {a["id"]: a for a in acs}
    reqs_by_id = {r["id"]: r for r in reqs}
    tags = at.scan_all(root, dirs)
    ac_tags = [t for t in tags if t.kind == "ac"]
    rule_tags = [t for t in tags if t.kind == "rule"]
    served = uc.ids_of(h.get("satisfies"))
    listed = uc.ids_of(h.get("criteria"))
    small = str(h.get("tier", "")).strip().lower() == "small"  # a small change needs no separate analysis or freeze
    rows = []

    # 1. requirements -> the criteria that prove them
    bare = [r for r in served if not any(r in [x.strip() for x in acs_by_id.get(c, {}).get("requirements", "").split(";")]
                                         for c in listed)]
    rows.append(_row("Requirements", ", ".join(served) or "none", f"{len(listed)} criteria",
                     WARN if bare or not served else OK,
                     (f"no criterion listed here proves {', '.join(bare)}" if bare else
                      "a use case that serves no requirement" if not served else "each has a criterion")))

    # 2. criteria -> tests. One classification is shared by this row and the Security row, so they cannot disagree.
    def classify(c):
        """Why a listed criterion is, or is not, proved: one of the keys of LABELS."""
        a = acs_by_id.get(c)
        if a is None or a.get("status") == "retired":
            return "not live"
        mine = [t for t in ac_tags if t.id == c]
        notes = a.get("notes", "").strip()
        if not mine:
            if notes.upper().startswith("R2"):
                return "deferred" if "decision" in notes.lower() else "deferred, no decision"
            return "no test"
        if any(t.hash and t.hash != uc.ac_hash(a) for t in mine):
            return "stale"
        real = [t for t in mine if not t.empty]
        if not real:
            return "empty"
        if results is not None:
            outs = [outcome_of(root, t, results) for t in real]
            if "failed" in outs:
                return "failing"
            if "passed" not in outs:
                return "no result"
        if all(t.listed for t in real):
            return "combined"
        return "stack run" if all(t.stack for t in real) else "tested"

    state = {k: [] for k in LABELS}
    for c in listed:
        state[classify(c)].append(c)
    status = FAIL if any(state[k] for k in FAILING) else WARN if any(state[k] for k in WARNING) else OK
    detail = "; ".join(f"{LABELS[k]}: {', '.join(v)}" for k, v in state.items() if v)
    if state["stack run"]:
        detail += " (the stack run only: the default test run does not execute them)"
    rows.append(_row("Criteria", f"{len(listed)} listed", "tagged tests", status, detail or "no criteria listed"))
    if not listed:
        rows[-1]["status"] = FAIL
        rows[-1]["detail"] = "no criteria: nothing verifies this use case"
    elif len(state["not live"]) == len(listed):
        rows[-1]["status"] = FAIL
        rows[-1]["detail"] = "no live criterion remains: " + detail

    # 3. flow and analysis -> the change log
    revisions = uc.analysis_revisions(text)
    if revisions is None:
        rows.append(_row("Analysis", "none", "-", OK if small else WARN,
                         "small tier: one combined sequence, no separate analysis" if small else "no analysis yet"))
    else:
        problems, notes = uc.trace_findings(uid, h, text)
        frozen = [n for n in notes if "not frozen" in n]
        if problems:
            rows.append(_row("Analysis", f"{len(revisions)} revision(s)", "change log", FAIL,
                             "; ".join(p.split(": ", 1)[-1] if "LOST" not in p else p.split(" ")[0].split("/")[-1].rstrip(":") + " lost"
                                       for p in problems[:4])))
        elif frozen:
            rows.append(_row("Analysis", f"{len(revisions)} revision(s)", "change log", OK if small else WARN,
                             "small tier: no freeze needed" if small else "traced, but not frozen"))
        else:
            rows.append(_row("Analysis", f"{len(revisions)} revision(s)", "change log", OK, "traced and frozen"))

    # 4. rules -> unit tests
    rules = h.get("rules") or []
    if not rules:
        rows.append(_row("Rules", "none listed", "-", OK, "no rules listed"))
    else:
        files = uc.ontology_files(root)
        missing = [r for r in rules if not any(t.id == r for t in rule_tags)]
        stack_only = [r for r in rules if r not in missing and all(t.stack for t in rule_tags if t.id == r)]
        nofile = [r for r in rules if r not in files]
        status = FAIL if missing else WARN if stack_only or nofile else OK
        parts = []
        if missing:
            parts.append(f"no test: {', '.join(missing)}")
        if stack_only:
            parts.append(f"stack run only: {', '.join(stack_only)}")
        if nofile:
            parts.append(f"no ontology file: {', '.join(nofile)}")
        rows.append(_row("Rules", ", ".join(rules), "tagged tests", status, "; ".join(parts) or "each has a test"))

    # 5. design -> diagrams
    notes = uc.diagram_findings(root, uid, text)
    nodesign = uc.section_raw(text, "Design") is None
    if notes or nodesign:
        rows.append(_row("Design", "diagrams", "files", WARN,
                         "; ".join([n.split(": ", 1)[-1] for n in notes] + (["no Design section"] if nodesign else []))))
    else:
        rows.append(_row("Design", "diagrams", "files", OK, "the linked diagrams exist"))

    # 6. slices
    sp, sn = uc.slice_findings(uid, h, text)
    rows.append(_row("Slices", f"{len(uc.slices_of(text))} slice(s)", "tests", FAIL if sp else WARN if sn else OK,
                     "; ".join((sp + sn)[:3]) or "each slice names its criteria"))

    # 7. security -> tests: the criteria marked security in their Notes (the abuse cases a security test proposed)
    def proves_served(a):
        return any(x.strip() in served for x in a.get("requirements", "").split(";"))

    marked = [a for a in acs if SECURITY.search(a.get("notes", "")) and (a["id"] in listed or proves_served(a))]
    retired_sec = sorted(a["id"] for a in marked if a.get("status") == "retired")
    secure = sorted(a["id"] for a in marked if a.get("status") != "retired")
    if not marked:
        rows.append(_row("Security", "none marked", "-", WARN,
                         f"not probed yet: no criterion here is marked security; run /vbench-security-test {uid}"))
    else:
        sstate = {k: [] for k in LABELS}
        for c in secure:
            sstate[classify(c)].append(c)
        failing = any(sstate[k] for k in FAILING)
        warning = any(sstate[k] for k in WARNING) or bool(retired_sec)
        parts = [f"{LABELS[k]}: {', '.join(v)}" for k, v in sstate.items() if v and k not in ("tested", "deferred")]
        if retired_sec:
            parts.append(f"retired security criterion (a person should confirm): {', '.join(retired_sec)}")
        rows.append(_row("Security", f"{len(secure)} criteria", "tagged tests", FAIL if failing else WARN if warning else OK,
                         "; ".join(parts) or "each has a test (run /vbench-test-stack to see them pass)"))

    # 8. review: stamped and fresh
    stale, unstamped = [], []
    for s in uc.suspects(h, reqs_by_id, acs_by_id):
        ident = s.split(" ")[0]
        (unstamped if "recorded none" in s else stale).append(ident)
    unreviewed = len({t.id for t in ac_tags if t.id in listed and t.hash is None})
    if stale:
        rows.append(_row("Review", "stamps", "a person", FAIL,
                         f"stale: {', '.join(stale)} changed since they were reviewed" +
                         (f"; not stamped: {len(unstamped)}" if unstamped else "")))
    elif unstamped:
        rows.append(_row("Review", "stamps", "a person", WARN,
                         f"not stamped: {len(unstamped)} link(s), and {unreviewed} tagged criteria have no test review hash"))
    else:
        rows.append(_row("Review", "stamps", "a person", OK, "every link is stamped and fresh"))
    return rows


def verdict(rows, strict):
    fails = sum(r["status"] == FAIL for r in rows)
    warns = sum(r["status"] == WARN for r in rows)
    return (fails == 0 and not (strict and warns)), fails, warns


def render(uid, name, commit, rows, strict, results_on=False):
    ok, fails, warns = verdict(rows, strict)
    legacy = sum(r["status"] == LEGACY for r in rows)
    out = [f"{uid} {name}   commit {commit}"]
    for r in rows:
        out.append(f"{r['level']:<13}{r['status']:<5} {r['spec']} -> {r['proof']}: {r['detail']}")
    if not results_on:
        out.append("NOTE tests are checked for existence only: no test results are configured (vbench.json `results`, or --results).")
    word = ("FAILED" if not ok else f"ok with {warns} warning{'s' if warns != 1 else ''}" if warns else "ok")
    out.append(f"RESULT {uid}: {word} ({fails} fail, {warns} warn" + (f", {legacy} legacy" if legacy else "")
               + (", strict" if strict else "") + ")")
    return "\n".join(out), ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root")
    ap.add_argument("--tests-dir", action="append")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--results", action="append", help="a JUnit XML file from the last test run (repeatable); default: vbench.json results")
    ap.add_argument("--baseline", choices=["write"], help="write today's failing rows to .claude/vbench-baseline.json (an owner's act)")
    ap.add_argument("--no-baseline", action="store_true", help="ignore the baseline file")
    ap.add_argument("uc", nargs="?")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else rq.find_root()
    cfg = rq.use_config(root)
    dirs = a.tests_dir or cfg["tests_dirs"] or [at.TESTS_DIR]
    commit = _commit(root)
    results = load_results(root, a.results or cfg.get("results"))
    baseline = None
    if not a.no_baseline and a.baseline != "write" and (root / BASELINE).is_file():
        try:
            baseline = json.loads((root / BASELINE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            baseline = None
    gaps = {}
    broken = []
    if a.all:
        loaded = uc.load_ucs(root)
        ids = [h["id"] for _, h, _ in loaded if "_error" not in h]
        broken = [(path, h["_error"]) for path, h, _ in loaded if "_error" in h]
    elif a.uc:
        ids = [a.uc]
    else:
        ap.error("give a use case id, or --all")
    outcomes, all_ok, failed, warned = [], True, 0, 0
    for uid in ids:
        rows = check(root, uid, dirs, cfg, results)
        if rows is not None:
            gaps[uid] = {r["level"]: r["detail"] for r in rows if r["status"] == FAIL}
            rows = settle(rows, uid, cfg, baseline)
        if rows is None:
            print(f"No use case {uid}.")
            return 1
        name = next((h.get("name", "") for _, h, _ in uc.load_ucs(root) if h.get("id") == uid), "")
        ok, fails, warns = verdict(rows, a.strict)
        all_ok &= ok
        failed += not ok
        warned += warns > 0
        outcomes.append({"uc": uid, "name": name, "ok": ok, "adoption": adoption_of(cfg, uid), "rows": rows, "commit": commit})
        if not a.json:
            print(render(uid, name, commit, rows, a.strict, results is not None)[0] + "\n")
    for path, err in broken:  # a use case whose header cannot be read is a failure, never a silent omission
        rows = [_row("Header", Path(path).name, "-", FAIL, f"cannot be read: {err}")]
        failed += 1
        all_ok = False
        outcomes.append({"uc": Path(path).stem, "name": "", "ok": False, "rows": rows, "commit": commit})
        if not a.json:
            print(f"{Path(path).stem}   commit {commit}\nHeader       FAIL  {Path(path).name}: cannot be read: {err}\nRESULT {Path(path).stem}: FAILED (1 fail, 0 warn)\n")
    if a.all and not outcomes:
        all_ok = False  # nothing was checked, so nothing was proved
    if a.baseline == "write":
        (root / BASELINE).parent.mkdir(parents=True, exist_ok=True)
        (root / BASELINE).write_text(json.dumps({"commit": commit, "gaps": {u: g for u, g in gaps.items() if g}}, indent=2) + "\n", encoding="utf-8")
        print(f"baseline written: {sum(len(g) for g in gaps.values())} known gap(s) in {BASELINE}", file=sys.stderr)
    if a.json:
        print(json.dumps(outcomes[0] if len(outcomes) == 1 and not a.all else
                         {"commit": commit, "ok": all_ok, "use_cases": outcomes}, indent=2))
    elif a.all:
        print(f"USE CASES: {len(outcomes)} checked, {failed} failed, {warned} with warnings")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
