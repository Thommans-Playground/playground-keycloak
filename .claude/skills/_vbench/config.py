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
  git              where work is pushed and where pull requests go:
                     remote       the git remote to push to (default "origin")
                     repo         "<owner>/<name>" on the host, for links when `gh` is not available
                     base_branch  the branch pull requests target. Used when the top level base_branch is not set
                     pr           defaults for a new pull request: draft (true or false), labels, reviewers (lists)
  adoption         how far each area is brought in: {"default": "legacy", "A": "adopted"}. States: legacy (only observed),
                   adopting (must be traced, gaps warn), adopted (gaps fail). Default "adopted".
  packs            which parts the project uses: core, ddd, security, keycloak. A trace row of a pack that is off is skipped.
  results          a JUnit XML file (or a list) from the last test run; with it a criterion counts only when its test passed.
  id_patterns      regular expressions for criterion, rule, usecase and requirement ids. Defaults are this repo's own.
  gate             the commands that make up the whole gate, in order. null means scripts/test-stack.sh all.
  stacks           the code stacks of the repo, one entry for each app, by name:
                     path (required), language (required), framework, tests, typecheck, lint, build, database
                   `tests`, `typecheck`, `lint` and `build` are the commands to run, from the repo root.
"""
import copy
import json
import re
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
    "git": {"remote": "origin", "repo": None, "base_branch": None,
            "pr": {"draft": False, "labels": [], "reviewers": []}},
    "stacks": {},
    # How far each area of the code has been brought into the harness (a strangler): "legacy" is only observed, "adopting"
    # must be traced but its gaps warn, "adopted" has its gaps fail. `default` covers any area not named.
    "adoption": {"default": "adopted"},
    # Which parts of the harness this project uses. A trace row that belongs to a pack that is off is skipped, not warned.
    "packs": ["core", "ddd", "security", "keycloak"],
    # A JUnit XML file (or a list of them) from the last test run. With it, a criterion counts as tested only when its test passed.
    "results": None,
    # The shape of each kind of id, as regular expressions. The defaults are this repo's own.
    "id_patterns": {"criterion": r"AC-\d+", "rule": r"RULE-[A-Z]\d+", "usecase": r"UC-[A-Z]\d+",
                    "requirement": r"(?:FR|NFR)-\d+"},
    # The commands that make up the whole gate, in order. None means this repo's own: scripts/test-stack.sh all.
    "gate": None,
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


GIT_KEYS = {"remote", "repo", "base_branch", "pr"}
PR_KEYS = {"draft", "labels", "reviewers"}
STACK_KEYS = {"path", "language", "framework", "tests", "typecheck", "lint", "build", "database", "test_framework"}
ADOPTION_STATES = ("legacy", "adopting", "adopted")
PACKS = ("core", "ddd", "security", "keycloak")
ID_KINDS = ("criterion", "rule", "usecase", "requirement")


def _unknown(where, given, allowed, f):
    extra = sorted(set(given) - allowed)
    if extra:
        raise SystemExit(f"{f}: unknown key '{extra[0]}' in {where}. Known keys: {', '.join(sorted(allowed))}")


def check_git(v, f):
    if not isinstance(v, dict):
        raise SystemExit(f"{f}: 'git' must be an object")
    _unknown("git", v, GIT_KEYS, f)
    for k in ("remote", "repo", "base_branch"):
        if k in v and v[k] is not None and not isinstance(v[k], str):
            raise SystemExit(f"{f}: git.{k} must be text")
    pr = v.get("pr", {})
    if not isinstance(pr, dict):
        raise SystemExit(f"{f}: git.pr must be an object")
    _unknown("git.pr", pr, PR_KEYS, f)
    if "draft" in pr and not isinstance(pr["draft"], bool):
        raise SystemExit(f"{f}: git.pr.draft must be true or false")
    for k in ("labels", "reviewers"):
        if k in pr and not (isinstance(pr[k], list) and all(isinstance(x, str) for x in pr[k])):
            raise SystemExit(f"{f}: git.pr.{k} must be a list of text")


def check_stacks(v, f):
    if not isinstance(v, dict):
        raise SystemExit(f"{f}: 'stacks' must be an object with one entry for each app")
    for name, stack in v.items():
        if not isinstance(stack, dict):
            raise SystemExit(f"{f}: stacks.{name} must be an object")
        _unknown(f"stacks.{name}", stack, STACK_KEYS, f)
        for need in ("path", "language"):
            if not stack.get(need):
                raise SystemExit(f"{f}: stacks.{name} needs '{need}'")
        for k, val in stack.items():
            if not isinstance(val, str):
                raise SystemExit(f"{f}: stacks.{name}.{k} must be text")


def check_adoption(v, f):
    if not isinstance(v, dict):
        raise SystemExit(f"{f}: 'adoption' must be an object: {{\"default\": \"legacy\", \"A\": \"adopted\"}}")
    for area, state in v.items():
        if state not in ADOPTION_STATES:
            raise SystemExit(f"{f}: adoption.{area} must be one of {', '.join(ADOPTION_STATES)}, not '{state}'")


def check_packs(v, f):
    if not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
        raise SystemExit(f"{f}: 'packs' must be a list of text")
    bad = [x for x in v if x not in PACKS]
    if bad:
        raise SystemExit(f"{f}: unknown pack '{bad[0]}'. Known packs: {', '.join(PACKS)}")


def check_results(v, f):
    if v is not None and not (isinstance(v, str) or (isinstance(v, list) and all(isinstance(x, str) for x in v))):
        raise SystemExit(f"{f}: 'results' must be a path or a list of paths to JUnit XML files")


def check_id_patterns(v, f):
    if not isinstance(v, dict):
        raise SystemExit(f"{f}: 'id_patterns' must be an object")
    _unknown("id_patterns", v, set(ID_KINDS), f)
    for kind, rx in v.items():
        try:
            re.compile(rx)
        except (re.error, TypeError) as e:
            raise SystemExit(f"{f}: id_patterns.{kind} is not a valid regular expression: {e}")


def check_gate(v, f):
    if v is not None and not (isinstance(v, list) and v and all(isinstance(x, str) for x in v)):
        raise SystemExit(f"{f}: 'gate' must be a list of commands, in order")


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
                elif k == "git":
                    check_git(v, f)
                    pr = {**cfg["git"]["pr"], **v.get("pr", {})}
                    cfg["git"] = {**cfg["git"], **v, "pr": pr}
                elif k == "stacks":
                    check_stacks(v, f)
                    cfg["stacks"] = v
                elif k == "adoption":
                    check_adoption(v, f)
                    cfg["adoption"] = {**cfg["adoption"], **v}
                elif k == "packs":
                    check_packs(v, f)
                    cfg["packs"] = v
                elif k == "results":
                    check_results(v, f)
                    cfg["results"] = v
                elif k == "id_patterns":
                    check_id_patterns(v, f)
                    cfg["id_patterns"] = {**cfg["id_patterns"], **v}
                elif k == "gate":
                    check_gate(v, f)
                    cfg["gate"] = v
                elif k in cfg:
                    cfg[k] = v
                else:
                    raise SystemExit(f"{f}: unknown key '{k}'. Known keys: {', '.join(sorted(cfg))}")
            break
    if not cfg["base_branch"] and cfg["git"]["base_branch"]:
        cfg["base_branch"] = cfg["git"]["base_branch"]   # one place to say it is enough
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
