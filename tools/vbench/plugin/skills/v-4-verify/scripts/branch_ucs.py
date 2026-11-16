#!/usr/bin/env python3
"""List the use cases a branch touches, with the evidence for each.

A use case counts as touched when, between the base and HEAD, any of these mention it:
  - a changed file path (e.g. the spec `UC-A-001-log-in.md`),
  - an added line with a `Realises` / `Verifies` tag,
  - a commit subject.

    branch_ucs.py                 base = base_branch from .vbench/config.toml
    branch_ucs.py --base origin/main
    branch_ucs.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

CONFIG = Path(".vbench") / "config.toml"
TAG_LINE = re.compile(r"^\+.*\b(Realises|Verifies)\b")


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


def settings() -> tuple[re.Pattern[str], str]:
    for d in [Path.cwd(), *Path.cwd().parents]:
        if (d / CONFIG).is_file():
            s = tomllib.loads((d / CONFIG).read_text(encoding="utf-8")).get("vbench", {})
            return re.compile(s.get("uc_pattern", r"UC-[A-Z]-\d{3}")), s.get("base_branch", "main")
    sys.exit(f"branch_ucs: no {CONFIG.as_posix()} found. Run `vbench init` first.")


def natural(s: str) -> list:
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", help="base ref (default: base_branch from config, then origin/<it>)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    uc_re, default_base = settings()
    base = next(
        (
            b
            for b in ([args.base] if args.base else [default_base, f"origin/{default_base}"])
            if git("rev-parse", "--verify", "--quiet", b).returncode == 0
        ),
        None,
    )
    if not base:
        sys.exit(f"branch_ucs: cannot resolve base `{args.base or default_base}`. Pass --base, or fetch full history.")

    found: dict[str, set[str]] = defaultdict(set)
    for path in git("diff", "--name-only", f"{base}...HEAD").stdout.splitlines():
        for uc in uc_re.findall(path):
            found[uc].add(f"file {path}")
    for line in git("diff", "-U0", f"{base}...HEAD").stdout.splitlines():
        if TAG_LINE.match(line) and not line.startswith("+++"):
            for uc in uc_re.findall(line):
                found[uc].add("tag")
    for subject in git("log", "--format=%s", f"{base}..HEAD").stdout.splitlines():
        for uc in uc_re.findall(subject):
            found[uc].add(f"commit `{subject}`")

    ucs = sorted(found, key=natural)
    if args.json:
        print(json.dumps({"base": base, "ucs": {u: sorted(found[u]) for u in ucs}}, indent=2))
    elif not ucs:
        print(f"No use cases touched between {base} and HEAD.")
    else:
        print(f"Use cases touched between {base} and HEAD:")
        for u in ucs:
            print(f"  {u}  ({len(found[u])} signal(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
