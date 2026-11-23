#!/usr/bin/env python3
"""card.py: a report card of the V for this repo's use cases, as a table (read-only, standard library only).

  card.py            one row for every use case: the three layers of the V, then what sits beside it
  card.py UC-A7      one use case in full: a layer to a row, the specification beside its proof, with what the script says

It runs vcycle.py (this repo's V cycle trace) and lays its rows onto the V. The shape of each dot says the state, so it
reads the same with colour off: ● finished, ◐ in progress, ○ not started, ✕ failing. The pairing of levels onto the V
is an interpretation (layer 1 requirements and criteria, layer 2 design, layer 3 slices); integration is not tracked by
the script, and the card says so instead of showing a state it has not earned.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

VCYCLE = Path(__file__).resolve().parents[2] / "vbench-vcycle" / "scripts" / "vcycle.py"
SHAPE = {"ok": "●", "na": "●", "warn": "◐", "FAIL": "✕", "legacy": "○"}
NOT_STARTED = re.compile(r"^(0\b|no\b|none\b)")  # "0 criteria", "no criterion listed", "no rules listed"
UNTRACKED = ("○", "not tracked", "")


def shape(row: dict | None) -> str:
    if row is None:
        return "○"
    if row["status"] == "warn" and NOT_STARTED.match(row["detail"].strip()):
        return "○"
    return SHAPE.get(row["status"], "◐")


def cell(rows: dict, level: str, use_proof: bool, detail: bool = False) -> str:
    row = rows.get(level)
    if row is None:
        return "○ not tracked"
    text = f"{shape(row)} {level}"
    if detail:
        fact = row["proof"] if use_proof else row["spec"]
        return f"{text}  {fact}: {row['detail']}" if row["detail"] else f"{text}  {fact}"
    return text


def overview(use_cases: list[dict]) -> list[str]:
    out = [
        "| Use case | 1 Requirements ↔ Criteria | 2 Design ↔ Integration | 3 Slices | Beside the V: Analysis · Rules · Security · Review |",
        "| --- | --- | --- | --- | --- |",
    ]
    for u in use_cases:
        r = {x["level"]: x for x in u["rows"]}
        out.append(
            f"| {u['uc']} {u['name']} | {cell(r, 'Requirements', False)} ↔ {cell(r, 'Criteria', True)} "
            f"| {cell(r, 'Design', False)} ↔ {UNTRACKED[0]} {UNTRACKED[1]} | {cell(r, 'Slices', False)} "
            f"| {shape(r.get('Analysis'))} · {shape(r.get('Rules'))} · {shape(r.get('Security'))} · {shape(r.get('Review'))} |"
        )
    out += ["", "● finished  ◐ in progress  ○ not started  ✕ failing"]
    return out


def detail(u: dict) -> list[str]:
    r = {x["level"]: x for x in u["rows"]}
    out = [
        f"{u['uc']} {u['name']}",
        "",
        "| Layer | Specification | Verification |",
        "| --- | --- | --- |",
        f"| 1 | {cell(r, 'Requirements', False, True)} | {cell(r, 'Criteria', True, True)} |",
        f"| 2 | {cell(r, 'Design', False, True)} | {UNTRACKED[0]} Integration  not tracked |",
        f"| 3 | {cell(r, 'Slices', False, True)} | {cell(r, 'Slices', True, True)} |",
        "",
        "| Beside the V | State |",
        "| --- | --- |",
    ]
    out += [f"| {lvl} | {cell(r, lvl, False, True)} |" for lvl in ("Analysis", "Rules", "Security", "Review")]
    out += ["", "● finished  ◐ in progress  ○ not started  ✕ failing"]
    return out


def main(argv: list[str]) -> int:
    asked = [a for a in argv if a.startswith("UC-")]
    run = subprocess.run([sys.executable, str(VCYCLE), "--all", "--json"], capture_output=True, text=True)
    try:
        data = json.loads(run.stdout)
    except json.JSONDecodeError:
        print(f"card.py: vcycle.py gave no readable answer.\n{run.stderr.strip()}", file=sys.stderr)
        return 2
    cases = data["use_cases"]
    if asked:
        match = [u for u in cases if u["uc"] == asked[0]]
        if not match:
            print(f"card.py: no use case {asked[0]}. Use cases: {', '.join(u['uc'] for u in cases)}.", file=sys.stderr)
            return 2
        print("\n".join(detail(match[0])))
        return 0
    print("\n".join(overview(cases)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
