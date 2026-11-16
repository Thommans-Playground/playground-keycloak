#!/usr/bin/env python3
"""Check a branch name against the vbench branch format.

Usage: check_branch.py "feat/UC-P1-create-project"

Exit code 0 when the name is valid, 1 when it is not. Problems are printed in
plain words. The same rules are meant to run in CI later. The rules are in
_vbench/conventions.md, and the id prefix, allowed types and limits come from
vbench.json (see _vbench/config.py), so this works in any repo.
"""
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_vbench"))
import config  # noqa: E402

SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"


def problems(name: str, cfg: dict | None = None) -> list[str]:
    cfg = cfg or config.load()
    prefix = re.escape(cfg["id_prefix"])
    ex = f"{cfg['id_prefix']}-P1"
    other_types = tuple(cfg["branch_types"])
    optional = cfg["use_case_ids"] == "optional"
    max_length = cfg["max_branch"]

    if name in {cfg["base_branch"], "main", "master", "develop", "trunk"}:
        return []
    if "/" not in name:
        return [f"The name must look like type/slug, for example feat/{ex}-create-project."]

    kind, rest = name.split("/", 1)
    found = []

    if kind in ("feature", "fix", "bugfix"):
        found.append(f"Use 'feat/' for use case work or 'hotfix/' for a production fix, not '{kind}/'.")
    elif kind != "feat" and kind not in other_types:
        found.append(f"Type '{kind}' is not allowed. Use feat, {', '.join(other_types)}.")

    if kind == "feat":
        has_id = re.match(rf"^{prefix}-[A-Z][0-9]+-", rest)
        if has_id:
            if not re.match(rf"^feat/{prefix}-[A-Z][0-9]+-{SLUG}$", name):
                found.append("After the use case id, the description must be lowercase words joined by hyphens.")
        elif optional:
            if not re.match(rf"^feat/{SLUG}$", name):
                found.append("The description must be lowercase words joined by hyphens.")
        else:
            found.append(
                f"A feat branch needs a use case id first, like {ex}, with capitals "
                f"(for example feat/{ex}-create-project)."
            )
    elif kind in other_types and not re.match(rf"^{kind}/{SLUG}$", name):
        found.append("The description must be lowercase words joined by hyphens.")

    if len(name) > max_length:
        found.append(f"The name is {len(name)} characters. Keep it to {max_length} or fewer.")
    if "—" in name or "–" in name:
        found.append("Do not use em dashes or en dashes. Use a plain hyphen.")
    return found


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    name = sys.argv[1].strip()
    found = problems(name)
    if found:
        print("Not valid:")
        for item in found:
            print(f"  - {item}")
        return 1
    print("Valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
