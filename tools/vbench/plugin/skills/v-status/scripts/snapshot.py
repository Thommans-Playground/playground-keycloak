#!/usr/bin/env python3
"""One read-only snapshot of where the repo stands on the V-cycle.

Prints, in order: `vbench status` (per-UC progress and the gates), the git branch and working-tree state,
the commits ahead of the base, and, when there are any, the result of `vbench check commits`. It changes nothing.

    snapshot.py              whole project
    snapshot.py UC-A-001        narrow `vbench status` to a use case or an area letter
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

CONFIG = Path(".vbench") / "config.toml"


def run(*cmd: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except OSError as e:
        return subprocess.CompletedProcess(cmd, 127, "", str(e))


def base_branch() -> str:
    for d in [Path.cwd(), *Path.cwd().parents]:
        if (d / CONFIG).is_file():
            return tomllib.loads((d / CONFIG).read_text(encoding="utf-8")).get("vbench", {}).get("base_branch", "main")
    return "main"


def section(title: str, body: str) -> None:
    print(f"## {title}\n{body.strip() or '(nothing)'}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("uc", nargs="?", help="UC id or area letter to narrow `vbench status`")
    args = ap.parse_args()

    if not shutil.which("vbench"):
        sys.exit("snapshot: `vbench` is not on PATH (uv tool install vbench).")
    st = run("vbench", "status", *([args.uc] if args.uc else []))
    if st.returncode != 0:
        sys.exit(st.stderr.strip() or "snapshot: `vbench status` failed.")
    section("vbench status", st.stdout)

    if run("git", "rev-parse", "--git-dir").returncode != 0:
        section("git", "not a git repository")
        return 0
    branch = run("git", "branch", "--show-current").stdout.strip() or "(detached)"
    section("working tree", f"branch: {branch}\n{run('git', 'status', '--short').stdout}")

    base = base_branch()
    ref = next(
        (b for b in (base, f"origin/{base}") if run("git", "rev-parse", "--verify", "--quiet", b).returncode == 0), None
    )
    if ref and branch != base:
        ahead = run("git", "log", "--oneline", f"{ref}..HEAD").stdout
        section(f"commits ahead of {ref}", ahead)
        if ahead.strip():
            c = run("vbench", "check", "commits", "--base", ref)
            section("commit convention", c.stdout or c.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
