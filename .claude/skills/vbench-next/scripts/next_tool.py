#!/usr/bin/env python3
"""vbench-next: the front door. Says where a use case is on the V and the ONE next step. Reads only, writes nothing.

  next_tool.py next [UC-A1]    the one next step (no id: for the use case that most needs attention)
  next_tool.py all             every use case with its moment and next step, worst first
  --json                       the same, as data (after the command)
  --root DIR, --tests-dir DIR  passed to vcycle.py

It reads the trace of `vcycle.py` (levels Requirements, Criteria, Analysis, Rules, Design, Slices, Security, Review),
takes the first FAIL left to right, else the first warn, and maps it to one of three moments: say what, say the shape,
build. Statuses other than ok, warn and FAIL, and levels it does not know, are skipped."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VCYCLE = HERE.parents[1] / "vbench-vcycle" / "scripts" / "vcycle.py"
LEVELS = ["Requirements", "Criteria", "Analysis", "Rules", "Design", "Slices", "Security", "Review"]
MOMENTS = {"say_what": "SAY WHAT", "say_shape": "SAY THE SHAPE", "build": "BUILD"}
REVIEWERS = "vbench-spec-challenger, vbench-security-reviewer and vbench-design-reviewer, together"


def _step(moment, skill, command, then, will_not, phase=None):
    return {"moment": moment, "phase": phase or MOMENTS[moment].lower(), "skill": skill, "command": command,
            "then": then, "will_not": will_not}


def route(uid, level, status, detail):
    d = detail.lower()
    if level == "Requirements":
        return _step("say_what", "/vbench-req", f"/vbench-req {uid}", "", "It will not write a requirement for you without your answers.")
    if level == "Criteria":
        if "no criteria" in d:
            return _step("say_what", "/vbench-req", f"/vbench-req {uid}", "then /vbench-at",
                         "It will not invent a criterion: you say what must be true.")
        if "no assertion" in d or "failed in the last run" in d:
            return _step("build", "/vbench-tdd", f"/vbench-tdd {uid}", "",
                         "It will not edit the test to make it pass: red for the right reason, and you review each step.")
        if "stale test hash" in d:
            return _step("build", "/vbench-at", f"/vbench-at {uid}", "",
                         "It will not stamp a test for you: you check it against the criterion, then record that you did.")
        if status == "warn" or "stack run" in d and "no test" not in d:
            return _step("build", "/vbench-test-stack", "/vbench-test-stack", "",
                         "It will not edit code or tests: it only runs the stack and reports.", "prove it")
        return _step("build", "/vbench-at", f"/vbench-at {uid}", "then /vbench-tdd, red green refactor",
                     "It will not invent assertions: it drafts a failing skeleton and asks before writing it.")
    if level in ("Analysis", "Design", "Slices") or (level == "Rules" and "ontology" in d):
        return _step("say_shape", "/vbench-uc", f"/vbench-uc {uid}", f"then the reviewers: {REVIEWERS}",
                     "It will not freeze the analysis: only the owner does that.")
    if level == "Rules":
        if status == "warn":
            return _step("build", "/vbench-test-stack", "/vbench-test-stack", "",
                         "It will not edit code or tests: it only runs the stack and reports.", "prove it")
        return _step("build", "/vbench-tdd", f"/vbench-tdd {uid}", "",
                     "It will not skip the failing test: red first, and you review after each step.")
    if level == "Security":
        if status == "FAIL":
            return _step("build", "/vbench-tdd", f"/vbench-tdd {uid}", "",
                         "It will not skip the failing test: red first, and you review after each step.")
        if "stack run" in d:
            return _step("build", "/vbench-test-stack", "/vbench-test-stack", "",
                         "It will not edit code or tests: it only runs the stack and reports.", "prove it")
        return _step("build", "/vbench-security-test", f"/vbench-security-test {uid}", "",
                     "It will not fix anything or add a criterion by itself: it reports, and you approve each proposal.",
                     "try to break it")
    return _step("build", "the owner", f"read the diffs of {uid}, then run the review stamps yourself", "",
                 "It will not run a stamp or a freeze for you: only the owner reviews and stamps.", "owner review")


def decide(uid, rows, name="", tier=""):
    """The one next step for a use case, from its trace rows."""
    known = [r for r in rows if r.get("level") in LEVELS and r.get("status") in ("ok", "warn", "FAIL")]
    known.sort(key=lambda r: LEVELS.index(r["level"]))
    fails = [r for r in known if r["status"] == "FAIL"]
    warns = [r for r in known if r["status"] == "warn"]
    base = {"uc": uid, "name": name, "tier": tier, "fails": len(fails), "warnings": len(warns)}
    pick = (fails or warns or [None])[0]
    if pick is None:
        return {**base, "moment": None, "phase": None, "skill": None, "command": None, "then": "", "level": None,
                "reason": "every row of the trace is ok", "will_not": ""}
    out = route(uid, pick["level"], pick["status"], pick.get("detail", ""))
    return {**base, **out, "level": pick["level"], "reason": f"{pick['level']} {pick['status']}: {pick.get('detail', '')}"}


def render(s):
    head = f"{s['uc']} {s['name']}".strip() + (f"   (tier: {s['tier']})" if s.get("tier") else "")
    if s["skill"] is None:
        return f"{head}\nNothing is open: every row of the trace is ok."
    lines = [f"You are at: {MOMENTS[s['moment']]}" + (f" ({s['phase']})" if s["phase"] not in (None, MOMENTS[s['moment']].lower()) else ""),
             head, f"Why: {s['reason']}", f"Next: {s['skill']}", f"Command: {s['command']}"]
    if s["then"]:
        lines.append(f"After that: {s['then']}")
    lines.append(f"{s['warnings']} warning(s) and {s['fails']} failure(s) remain in the trace; no failure is not done.")
    lines.append(f"It will NOT do this for you: {s['will_not']}")
    return "\n".join(lines)


def tiers(root):
    """The optional `tier` field of each use case header (small or full), by id."""
    out = {}
    for p in sorted((Path(root) / "docs" / "usecases").glob("UC-*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        i = re.search(r"^\s*id:\s*(UC-[\w-]+)", text, re.M)
        t = re.search(r"^\s*tier:\s*(small|full)\s*$", text, re.M)
        if i and t:
            out[i.group(1)] = t.group(1)
    return out


def trace(root, tests_dirs, uid=None):
    cmd = [sys.executable, str(VCYCLE), "--json"] + (["--root", str(root)] if root else [])
    for d in tests_dirs or []:
        cmd += ["--tests-dir", d]
    cmd += [uid] if uid else ["--all"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except ValueError:
        return None, (p.stdout.strip() or p.stderr.strip())


def _rank(s):
    return (-s["fails"], -s["warnings"], s["uc"])


def main(argv=None):
    def flags(p, keep):  # the same flags before or after the command; a later default must not erase an earlier value
        d = {} if keep else {"default": argparse.SUPPRESS}
        p.add_argument("--json", action="store_true", **({"default": False} if keep else d))
        p.add_argument("--root", **d)
        p.add_argument("--tests-dir", action="append", **d)
        return p

    ap = flags(argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter), True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    nxt = flags(sub.add_parser("next"), False)
    nxt.add_argument("uc", nargs="?")
    flags(sub.add_parser("all"), False)
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else Path.cwd()
    data = trace(root, a.tests_dir, a.uc if a.cmd == "next" else None)
    if isinstance(data, tuple):
        print(data[1])
        return 1
    ucs = data["use_cases"] if "use_cases" in data else [data]
    t = tiers(root)
    steps = sorted((decide(x["uc"], x["rows"], x.get("name", ""), t.get(x["uc"], "")) for x in ucs), key=_rank)
    if not steps:
        print("No use cases found." if not a.json else json.dumps({"use_cases": []}))
        return 0
    if a.cmd == "next":
        s = steps[0]
        print(json.dumps(s, indent=2) if a.json else render(s))
    elif a.json:
        print(json.dumps({"use_cases": steps}, indent=2))
    else:
        for s in steps:
            tail = "nothing is open" if s["skill"] is None else f"{MOMENTS[s['moment']]}: {s['command']}  [{s['reason']}]"
            print(f"{s['uc']:<8}{s['warnings']} warn {s['fails']} fail  {tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
