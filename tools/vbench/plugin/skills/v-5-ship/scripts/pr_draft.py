#!/usr/bin/env python3
"""Print the traceability table for a PR, built from `vbench status --json`.

One row per use case: tasks closed / declared, ACs covered / enforced, the production files that realise it,
and the tests that verify it with their rungs. The Maturity column is left for a human, because maturity is a
judgement about the code, not a count.

    pr_draft.py UC-A-001 UC-A-002          the named use cases
    pr_draft.py                      the use cases the branch touches (runs v-4-verify/scripts/branch_ucs.py)
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def vbench_json(*args: str):
    r = subprocess.run(["vbench", *args, "--json"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        sys.exit(f"pr_draft: `vbench {' '.join(args)} --json` gave no JSON: {(r.stderr or r.stdout).strip()[:200]}")


def branch_ucs() -> list[str]:
    script = Path(__file__).resolve().parents[2] / "v-4-verify" / "scripts" / "branch_ucs.py"
    r = subprocess.run([sys.executable, str(script), "--json"], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr.strip() or "pr_draft: could not list the branch's use cases; pass them as arguments.")
    return list(json.loads(r.stdout)["ucs"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ucs", nargs="*", help="use case ids; default: those the branch touches")
    args = ap.parse_args()
    if not shutil.which("vbench"):
        sys.exit("pr_draft: `vbench` is not on PATH (uv tool install vbench).")

    ucs = args.ucs or branch_ucs()
    rows = {r["uc"]: r for r in vbench_json("status")["useCases"]}

    print("| UC | Tasks | ACs covered | Realised in | Verified by (rung) | Maturity |")
    print("| --- | --- | --- | --- | --- | --- |")
    for uc in ucs:
        r = rows.get(uc)
        tasks = f"{r['tasksClosed']}/{r['tasks']}" if r else "?"
        acs = f"{r['covered']}/{r['enforced']}" if r else "?"
        code = "<br>".join(r["realisedIn"]) if r and r["realisedIn"] else "(none)"
        if r and r["verifiedBy"]:
            tests = "<br>".join(f"{t['file']} ({t['rung']})" for t in r["verifiedBy"])
        else:
            tests = "**OPEN: no test**" if r and r["realisedIn"] else "(none)"
        print(f"| {uc} | {tasks} | {acs} | {code} | {tests} | |")
    if not ucs:
        print("| (no use cases touched) | | | | | |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
