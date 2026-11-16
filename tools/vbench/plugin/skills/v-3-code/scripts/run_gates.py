#!/usr/bin/env python3
"""Run the project's gates and print one compact verdict.

Reads `[commands]` from `.vbench/config.toml` (test, lint, format, types, boundaries; an empty command is skipped),
runs each, then `vbench check` (refs, rungs, acs). Prints a table, then the tail of every failing gate's output.
Exit 0 only if every configured gate passed.

    run_gates.py                     all gates
    run_gates.py --only test,lint    just those
    run_gates.py --tail 40           show more output for failures
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

CONFIG = Path(".vbench") / "config.toml"
ORDER = ("test", "lint", "format", "types", "boundaries", "check")


def find_root() -> Path:
    for d in [Path.cwd(), *Path.cwd().parents]:
        if (d / CONFIG).is_file():
            return d
    sys.exit(f"run_gates: no {CONFIG.as_posix()} found here or in a parent. Run `vbench init` first.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help=f"comma-separated subset of: {', '.join(ORDER)}")
    ap.add_argument("--tail", type=int, default=15, help="lines of output to show per failing gate")
    args = ap.parse_args()

    only = [g.strip() for g in args.only.split(",")] if args.only else list(ORDER)
    unknown = [g for g in only if g not in ORDER]
    if unknown:
        sys.exit(f"run_gates: unknown gate(s): {', '.join(unknown)}. Choose from: {', '.join(ORDER)}")

    root = find_root()
    commands = dict(tomllib.loads((root / CONFIG).read_text(encoding="utf-8")).get("commands", {}))
    if not shutil.which("vbench"):
        commands["check"] = ""
        print(
            "run_gates: `vbench` is not on PATH; the check gate is skipped (uv tool install vbench).", file=sys.stderr
        )
    else:
        commands["check"] = "vbench check"

    rows, failures = [], []
    for gate in (g for g in ORDER if g in only):
        cmd = (commands.get(gate) or "").strip()
        if not cmd:
            rows.append((gate, "skipped", "not configured", ""))
            continue
        start = time.monotonic()
        r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
        secs = f"{time.monotonic() - start:.1f}s"
        ok = r.returncode == 0
        rows.append((gate, "PASS" if ok else "FAIL", cmd, secs))
        if not ok:
            failures.append((gate, (r.stdout + r.stderr).strip().splitlines()[-args.tail :]))

    print("| gate | result | command | time |\n| --- | --- | --- | --- |")
    for gate, result, cmd, secs in rows:
        print(f"| {gate} | {result} | `{cmd}` | {secs} |")
    for gate, tail in failures:
        print(f"\n--- {gate}: last {len(tail)} line(s) ---")
        print("\n".join(tail))
    ran = [r for r in rows if r[1] != "skipped"]
    print(
        f"\n{len(ran) - len(failures)}/{len(ran)} gates passed"
        + (" (some not configured)" if len(ran) < len(rows) else "")
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
