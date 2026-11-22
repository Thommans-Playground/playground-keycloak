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
from pathlib import Path

HERE = Path(__file__).resolve()
for skill in ("vbench-uc", "vbench-at", "vbench-req"):
    sys.path.insert(0, str(HERE.parents[2] / skill / "scripts"))
import at_tool as at  # noqa: E402
import req_tool as rq  # noqa: E402
import uc_tool as uc  # noqa: E402

OK, WARN, FAIL = "ok", "warn", "FAIL"


def _row(level, spec, proof, status, detail=""):
    return {"level": level, "spec": spec, "proof": proof, "status": status, "detail": detail}


def _commit(root):
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
        return out.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def check(root, uid, dirs):
    """The rows of the V for one use case, or None when there is no such use case."""
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
    rows = []

    # 1. requirements -> the criteria that prove them
    bare = [r for r in served if not any(r in [x.strip() for x in acs_by_id.get(c, {}).get("requirements", "").split(";")]
                                         for c in listed)]
    rows.append(_row("Requirements", ", ".join(served) or "none", f"{len(listed)} criteria",
                     WARN if bare or not served else OK,
                     (f"no criterion listed here proves {', '.join(bare)}" if bare else
                      "a use case that serves no requirement" if not served else "each has a criterion")))

    # 2. criteria -> tests
    state = {"tested": [], "stack run": [], "deferred": [], "no test": []}
    for c in listed:
        a = acs_by_id.get(c)
        if not a or a.get("status") == "retired":
            continue
        mine = [t for t in ac_tags if t.id == c]
        if mine:
            state["stack run" if all(t.stack for t in mine) else "tested"].append(c)
        elif a.get("notes", "").strip().upper().startswith("R2"):
            state["deferred"].append(c)
        else:
            state["no test"].append(c)
    status = FAIL if state["no test"] else WARN if state["stack run"] else OK
    detail = "; ".join(f"{k}: {', '.join(v)}" for k, v in state.items() if v)
    if state["stack run"]:
        detail += " (the stack run only: the default test run does not execute them)"
    rows.append(_row("Criteria", f"{len(listed)} listed", "tagged tests", status, detail or "no criteria listed"))
    if not listed:
        rows[-1]["status"] = FAIL
        rows[-1]["detail"] = "no criteria: nothing verifies this use case"

    # 3. flow and analysis -> the change log
    revisions = uc.analysis_revisions(text)
    if revisions is None:
        rows.append(_row("Analysis", "none", "-", WARN, "no analysis yet"))
    else:
        problems, notes = uc.trace_findings(uid, h, text)
        frozen = [n for n in notes if "not frozen" in n]
        if problems:
            rows.append(_row("Analysis", f"{len(revisions)} revision(s)", "change log", FAIL,
                             "; ".join(p.split(": ", 1)[-1] if "LOST" not in p else p.split(" ")[0].split("/")[-1].rstrip(":") + " lost"
                                       for p in problems[:4])))
        elif frozen:
            rows.append(_row("Analysis", f"{len(revisions)} revision(s)", "change log", WARN, "traced, but not frozen"))
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
    nodesign = uc.section_raw(text, "Design") is None if revisions is not None else False
    if notes or nodesign:
        rows.append(_row("Design", "diagrams", "files", WARN,
                         "; ".join([n.split(": ", 1)[-1] for n in notes] + (["no Design section"] if nodesign else []))))
    else:
        rows.append(_row("Design", "diagrams", "files", OK, "the linked diagrams exist"))

    # 6. slices
    sp, sn = uc.slice_findings(uid, h, text)
    rows.append(_row("Slices", f"{len(uc.slices_of(text))} slice(s)", "tests", FAIL if sp else WARN if sn else OK,
                     "; ".join((sp + sn)[:3]) or "each slice names its criteria"))

    # 7. security -> tests: the criteria whose Notes start with `security` (the abuse cases a security test proposed)
    def proves_served(a):
        return any(x.strip() in served for x in a.get("requirements", "").split(";"))

    secure = sorted(
        {a["id"] for a in acs
         if a.get("status") != "retired" and a.get("notes", "").strip().lower().startswith("security")
         and (a["id"] in listed or proves_served(a))})
    if not secure:
        rows.append(_row("Security", "none marked", "-", WARN,
                         f"not probed yet: no criterion here starts its Notes with `security`; run /vbench-security-test {uid}"))
    else:
        no_test = [c for c in secure if not any(t.id == c for t in ac_tags)]
        stack_only = [c for c in secure if c not in no_test and all(t.stack for t in ac_tags if t.id == c)]
        parts = []
        if no_test:
            parts.append(f"no test: {', '.join(no_test)}")
        if stack_only:
            parts.append(f"stack run only: {', '.join(stack_only)}")
        rows.append(_row("Security", f"{len(secure)} criteria", "tagged tests", FAIL if no_test else WARN if stack_only else OK,
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


def render(uid, name, commit, rows, strict):
    ok, fails, warns = verdict(rows, strict)
    out = [f"{uid} {name}   commit {commit}"]
    for r in rows:
        out.append(f"{r['level']:<13}{r['status']:<5} {r['spec']} -> {r['proof']}: {r['detail']}")
    out.append(f"RESULT {uid}: {'ok' if ok else 'FAILED'} ({fails} fail, {warns} warn" + (", strict" if strict else "") + ")")
    return "\n".join(out), ok


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root")
    ap.add_argument("--tests-dir", action="append")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("uc", nargs="?")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else rq.find_root()
    cfg = rq.use_config(root)
    dirs = a.tests_dir or cfg["tests_dirs"] or [at.TESTS_DIR]
    commit = _commit(root)
    if a.all:
        ids = [h["id"] for _, h, _ in uc.load_ucs(root) if "_error" not in h]
    elif a.uc:
        ids = [a.uc]
    else:
        ap.error("give a use case id, or --all")
    results, all_ok, failed, warned = [], True, 0, 0
    for uid in ids:
        rows = check(root, uid, dirs)
        if rows is None:
            print(f"No use case {uid}.")
            return 1
        name = next((h.get("name", "") for _, h, _ in uc.load_ucs(root) if h.get("id") == uid), "")
        ok, fails, warns = verdict(rows, a.strict)
        all_ok &= ok
        failed += not ok
        warned += warns > 0
        results.append({"uc": uid, "name": name, "ok": ok, "rows": rows, "commit": commit})
        if not a.json:
            print(render(uid, name, commit, rows, a.strict)[0] + "\n")
    if a.json:
        print(json.dumps(results[0] if len(results) == 1 and not a.all else
                         {"commit": commit, "ok": all_ok, "use_cases": results}, indent=2))
    elif a.all:
        print(f"USE CASES: {len(results)} checked, {failed} failed, {warned} with warnings")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
