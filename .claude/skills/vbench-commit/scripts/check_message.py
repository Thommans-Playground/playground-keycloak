#!/usr/bin/env python3
"""Check a commit summary line against the vbench commit format.

Usage: check_message.py "feat(UC-P1): archive a project with a reason"

Exit code 0 when the line is valid, 1 when it is not. Problems are printed in
plain words. The same rules are meant to run in CI later.
"""
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_vbench"))
import config  # noqa: E402

PLAIN_SCOPE = re.compile(r"^[a-z][a-z0-9-]*$")
LINE = re.compile(r"^(?P<type>[A-Za-z]+)\((?P<scope>[^)]+)\): (?P<summary>.+)$")


def problems(line: str, cfg: dict | None = None) -> list[str]:
    cfg = cfg or config.load()
    TYPES = tuple(cfg["commit_types"])
    prefix = cfg["id_prefix"]
    USE_CASE = re.compile(rf"^{re.escape(prefix)}-[A-Z][0-9]+$")
    MAX_LENGTH = cfg["max_summary"]
    found = []
    match = LINE.match(line)
    if not match:
        return ["The line must look like: type(scope): summary"]

    kind, scope, summary = match["type"], match["scope"], match["summary"]

    if kind not in TYPES:
        found.append(f"Type '{kind}' is not allowed. Use one of: {', '.join(TYPES)}.")
    if not (USE_CASE.match(scope) or PLAIN_SCOPE.match(scope)):
        found.append(
            f"Scope '{scope}' must be a use case id like {prefix}-P1 "
            "or a plain lowercase word like ci."
        )
    if len(line) > MAX_LENGTH:
        found.append(f"The line is {len(line)} characters. Keep it to {MAX_LENGTH} or fewer.")
    if summary.endswith("."):
        found.append("Do not end the summary with a full stop.")
    if summary[0].isupper():
        found.append("Start the summary with a lowercase letter.")
    if "—" in line or "–" in line:
        found.append("Do not use em dashes or en dashes. Use a comma, colon or brackets.")
    return found


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    line = sys.argv[1].strip().splitlines()[0]
    found = problems(line)
    if found:
        print("Not valid:")
        for item in found:
            print(f"  - {item}")
        return 1
    print("Valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
