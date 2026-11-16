"""Shared settings for every vbench skill, so the skills drop into any repo.

Nothing here is specific to one project. A repo may put a `vbench.json` at its root (or at
`.claude/vbench.json`) to change any key in DEFAULTS. Keys left out keep their default, and a
repo with no file at all works with the defaults.

Keys:
  id_prefix        use case id prefix, "UC" gives UC-P1. Also used in branch names, commit scopes, PR titles.
  use_case_ids     "required": feat branches, commit scopes and PR titles must carry a use case id (the
                   vbench way). "optional": a plain feat/<slug> and feat(<scope>) are accepted too.
  base_branch      branch pull requests go to. null means detect it (origin/HEAD, then main, then master).
  system_name      name shown in generated use case diagrams. null means the repo folder name.
  areas            {letter: context} for use case ids (UC-<letter><n>). Empty means any capital letter is
                   fine and the context is free text.
  actors           allowed actors in a use case. Empty means any.
  providers        allowed `provided_by` values in a use case. Empty means any.
  diagram          optional look of generated use case diagrams: actor_style {actor: block name},
                   actor_colour {actor: #hex}, context_colour {context: #hex}, actor_is_a [[child, parent]].
                   Anything not listed gets a name and a colour worked out from its id.
  tests_dirs       folders that hold acceptance tests.
  test_stack       pytest | vitest | playwright for drafted test skeletons. null means detect it from the repo.
  commit_types     allowed Conventional Commit types.
  branch_types     allowed non use case branch types (the use case type is always `feat`).
  max_branch, max_summary, max_title   length limits.
  paths            where the requirement, criteria, use case and domain files live, relative to the root.
"""
import copy
import json
import subprocess
from pathlib import Path

DEFAULTS = {
    "id_prefix": "UC",
    "use_case_ids": "required",
    "base_branch": None,
    "system_name": None,
    "areas": {},
    "actors": [],
    "providers": [],
    "diagram": {"actor_style": {}, "actor_colour": {}, "context_colour": {}, "actor_is_a": []},
    "tests_dirs": ["tests/acceptance"],
    "test_stack": None,
    "commit_types": ["feat", "fix", "test", "refactor", "docs", "style", "chore"],
    "branch_types": ["hotfix", "experiment", "chore", "docs"],
    "max_branch": 60,
    "max_summary": 72,
    "max_title": 72,
    "paths": {
        "req": "docs/requirements/requirements.md",
        "ac": "docs/requirements/acceptance-criteria.md",
        "perm": "docs/requirements/permissions.csv",
        "vocab": "docs/domain/vocabulary.csv",
        "rules": "docs/domain/ontology/rule-inventory.csv",
        "decisions": "docs/domain/decisions.md",
        "usecases": "docs/usecases",
        "retired": "docs/usecases/retired-ids.csv",
        "ontology": "docs/domain/ontology",
    },
}

CONFIG_NAMES = ("vbench.json", ".claude/vbench.json")


def git_root(start=None):
    here = Path(start or Path.cwd()).resolve()
    done = subprocess.run(["git", "-C", str(here), "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True)
    return Path(done.stdout.strip()) if done.returncode == 0 and done.stdout.strip() else None


def find_root(start=None):
    """The project root: the nearest folder up the tree with a vbench.json or docs/requirements,
    else the git top level, else the folder you are in. It never fails, so a fresh repo works."""
    here = Path(start or Path.cwd()).resolve()
    for p in [here, *here.parents]:
        if any((p / n).is_file() for n in CONFIG_NAMES) or (p / "docs" / "requirements").is_dir():
            return p
    return git_root(here) or here


def load(root=None):
    """The settings for this root: DEFAULTS with the repo's vbench.json laid over them."""
    root = Path(root) if root else find_root()
    cfg = copy.deepcopy(DEFAULTS)
    for name in CONFIG_NAMES:
        f = root / name
        if f.is_file():
            try:
                user = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{f} is not valid JSON: {e}")
            for k, v in user.items():
                if k in ("paths", "diagram"):
                    cfg[k].update(v)
                elif k in cfg:
                    cfg[k] = v
                else:
                    raise SystemExit(f"{f}: unknown key '{k}'. Known keys: {', '.join(sorted(cfg))}")
            break
    return cfg


def base_branch(cfg, root=None):
    """The branch pull requests target: the configured one, else the remote default, else main/master."""
    if cfg.get("base_branch"):
        return cfg["base_branch"]
    cwd = str(root or Path.cwd())

    def git(*a):
        done = subprocess.run(["git", "-C", cwd, *a], capture_output=True, text=True)
        return done.stdout.strip() if done.returncode == 0 else ""

    head = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD")  # origin/main
    if head:
        return head.split("/", 1)[1]
    for name in ("main", "master", "develop", "trunk"):
        if git("rev-parse", "--verify", "--quiet", f"refs/heads/{name}"):
            return name
    return git("branch", "--show-current") or "main"


def detect_stack(root):
    """pytest for a Python repo; playwright or vitest when package.json says so and there is no Python."""
    root = Path(root)
    python = any((root / n).exists() for n in ("pyproject.toml", "setup.py", "requirements.txt", "pytest.ini"))
    pkg = root / "package.json"
    if pkg.is_file() and not python:
        text = pkg.read_text(encoding="utf-8", errors="ignore")
        if "@playwright/test" in text:
            return "playwright"
        if "vitest" in text:
            return "vitest"
    return "pytest"
