#!/usr/bin/env python3
"""Check a branch before it becomes a pull request.

Usage:
  check_pr.py                      check the current branch and its commits
  check_pr.py --title "UC-P1: Create a project"   also check a PR title
  check_pr.py --base main          compare against another base branch

It reuses the branch checker and the commit message checker, so the rules stay
in one place each. Exit code 0 when everything is valid, 1 when something is not.
The rules are in _vbench/standards/conventions.md; the base branch, id prefix and limits come from
vbench.json (see _vbench/config.py).
"""
import argparse
import importlib.util
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True  # do not leave __pycache__ folders in the skills

SKILLS = pathlib.Path(__file__).resolve().parents[2]

sys.path.insert(0, str(SKILLS / "_vbench"))
import config  # noqa: E402


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, SKILLS / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


branch_rules = load("check_branch", "vbench-branch/scripts/check_branch.py")
message_rules = load("check_message", "vbench-commit/scripts/check_message.py")


def git(*args: str) -> str:
    done = subprocess.run(["git", *args], capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else ""


def title_problems(title: str, cfg: dict | None = None) -> list[str]:
    cfg = cfg or config.load()
    prefix = cfg["id_prefix"]
    types = dict.fromkeys([*cfg["commit_types"], *cfg["branch_types"], "feat"])
    uc_title = re.compile(rf"^{re.escape(prefix)}-[A-Z][0-9]+: \S.*$")
    plain_title = re.compile(rf"^(?:{'|'.join(types)}): [a-z].*$")
    found = []
    if not (uc_title.match(title) or plain_title.match(title)):
        found.append(
            f"The title must be '{prefix}-P1: Create a project' for a use case, "
            "or 'docs: add something' (lowercase) for work with no use case."
        )
    if len(title) > cfg["max_title"]:
        found.append(f"The title is {len(title)} characters. Keep it to {cfg['max_title']} or fewer.")
    if title.endswith("."):
        found.append("Do not end the title with a full stop.")
    if "—" in title or "–" in title:
        found.append("Do not use em dashes or en dashes in the title.")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--base", help="the branch the PR targets (default: vbench.json base_branch, else detected)")
    parser.add_argument("--title")
    args = parser.parse_args()
    cfg = config.load()
    args.base = args.base or config.base_branch(cfg)

    branch = git("branch", "--show-current")
    results = []  # (label, list of problems)

    if not branch:
        print("Not on a branch (detached HEAD). Switch to a branch first.")
        return 1
    if branch == args.base:
        print(f"You are on {args.base}. A pull request needs its own branch.")
        return 1

    results.append((f"Branch name: {branch}", branch_rules.problems(branch)))

    subjects = git("log", f"{args.base}..HEAD", "--no-merges", "--format=%s").splitlines()
    if not subjects:
        print(f"No commits on {branch} that are not already on {args.base}.")
        return 1
    for subject in subjects:
        results.append((f"Commit: {subject}", message_rules.problems(subject)))

    if args.title:
        results.append((f"Title: {args.title}", title_problems(args.title)))

    failed = False
    for label, found in results:
        if found:
            failed = True
            print(f"NOT VALID  {label}")
            for item in found:
                print(f"    - {item}")
        else:
            print(f"valid      {label}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
