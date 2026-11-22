#!/usr/bin/env python3
"""adopt_tool.py: look at an existing project and say how the harness could be adopted there, one area at a time.

  adopt_tool.py discover [ROOT]         what is there (stacks, tests, docs, ids, git habits, CI), a proposed vbench.json,
                                        and which steps of the adoption ladder can start now
  adopt_tool.py discover [ROOT] --json  the same as data

It only reads. It writes no file, in the project or anywhere else, and it makes no network call. The proposed
vbench.json is printed for a person to read and accept; the skill writes it only after they agree. It skips .git,
node_modules, virtual environments and build folders, and reads no file over 1 MB. Standard library only."""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SKIP = {".git", "node_modules", ".venv", "venv", "env", "dist", "build", "target", "vendor", "__pycache__", ".next", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache", "site-packages"}
MAX_FILES = 6000
MAX_BYTES = 1_000_000
DOC_WORDS = re.compile(r"requirement|prd|user[-_ ]?stor|use[-_ ]?case|usecase|epic|spec", re.I)
ID_FORM = re.compile(r"\b(FR|NFR|REQ|US|UC|AC|TC|STK)-\d+\b")


def files(root: Path):
    out, stack = [], [root]
    while stack and len(out) < MAX_FILES:
        d = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for p in entries:
            if p.name in SKIP or p.name.startswith(".") and p.name not in {".github", ".gitlab-ci.yml", ".importlinter", ".claude"}:
                continue
            if p.is_dir():
                stack.append(p)
            elif p.is_file():
                out.append(p)
    return out


def read(p: Path) -> str:
    try:
        if p.stat().st_size > MAX_BYTES:
            return ""
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def git(root: Path, *args) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=20)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def stacks(root: Path, fs: list) -> dict:
    found = {}
    for p in fs:
        depth = len(p.relative_to(root).parts)
        if depth > 3:
            continue
        name, folder = p.name, rel(root, p.parent) if p.parent != root else "."
        label = re.sub(r"[^a-z0-9]+", "-", (p.parent.name if p.parent != root else root.name).lower()).strip("-") or "app"
        if name == "pyproject.toml" or name == "requirements.txt":
            text = read(p) + read(p.parent / "pyproject.toml") + read(p.parent / "requirements.txt")
            fw = next((f for f in ("fastapi", "django", "flask") if re.search(rf"\b{f}\b", text, re.I)), None)
            s = found.setdefault(folder, {"name": label, "path": folder, "language": "python"})
            s["language"] = "python"
            if fw:
                s["framework"] = fw
            if re.search(r"pytest", text):
                s["tests"] = "pytest"
                s["test_framework"] = "pytest"
            if re.search(r"\bruff\b", text):
                s["lint"] = "ruff check ."
            if re.search(r"\bmypy\b", text):
                s["typecheck"] = "mypy ."
        elif name == "package.json":
            try:
                data = json.loads(read(p) or "{}")
            except ValueError:
                continue
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            scripts = data.get("scripts", {})
            s = found.setdefault(folder, {"name": label, "path": folder, "language": "typescript" if "typescript" in deps else "javascript"})
            fw = next((f for f in ("next", "react", "vue", "svelte", "express", "nestjs") if f in deps or f"@{f}/core" in deps), None)
            if fw:
                s["framework"] = fw
            test_script = scripts.get("test", "")
            for fw_name in ("playwright", "vitest", "jest"):
                if fw_name in test_script or fw_name in deps:
                    s["test_framework"] = fw_name
                    break
            else:
                if "node --test" in test_script:
                    s["test_framework"] = "node:test"
            for key, script in (("tests", "test"), ("lint", "lint"), ("typecheck", "typecheck"), ("build", "build")):
                if script in scripts:
                    s[key] = f"npm run {script}" if script != "test" else "npm test"
        elif name == "go.mod":
            found.setdefault(folder, {"name": label, "path": folder, "language": "go", "tests": "go test ./..."})
        elif name in ("pom.xml", "build.gradle", "build.gradle.kts"):
            found.setdefault(folder, {"name": label, "path": folder, "language": "java", "tests": "mvn test" if name == "pom.xml" else "gradle test"})
        elif name == "Cargo.toml":
            found.setdefault(folder, {"name": label, "path": folder, "language": "rust", "tests": "cargo test"})
    return found


def tests_of(root: Path, fs: list) -> dict:
    pats = {"python": re.compile(r"^(test_.*|.*_test)\.py$"), "js": re.compile(r".*\.(test|spec)\.[jt]sx?$"), "go": re.compile(r".*_test\.go$"), "java": re.compile(r".*Tests?\.java$")}
    counts, dirs = Counter(), Counter()
    tagged = Counter()
    for p in fs:
        for kind, rx in pats.items():
            if rx.match(p.name):
                counts[kind] += 1
                dirs[rel(root, p.parent).split("/")[0] if p.parent != root else "."] += 1
                text = read(p)
                if re.search(r"pytest\.mark\.\w+\(\s*[\"'](AC|REQ|FR|US|UC)-", text):
                    tagged["marker"] += 1
                if re.search(r"\b(Verifies|Covers|Requirement|Implements)\b[: ]+\s*(AC|REQ|FR|US|UC)-", text):
                    tagged["comment"] += 1
    return {"files": dict(counts), "folders": [d for d, _ in dirs.most_common(4)], "traced_to_ids": dict(tagged)}


def docs_of(root: Path, fs: list) -> dict:
    docs = [p for p in fs if p.suffix.lower() in (".md", ".rst", ".adoc")]
    folders = sorted({rel(root, p.parent).split("/")[0] for p in docs if p.parent != root and rel(root, p.parent).split("/")[0] in ("docs", "doc", "documentation", "design", "specs")})
    like = [rel(root, p) for p in docs if DOC_WORDS.search(p.name) or DOC_WORDS.search(p.parent.name)][:12]
    adr = sorted({rel(root, p.parent) for p in docs if re.match(r"^\d{3,4}[-_]", p.name) and "adr" in rel(root, p).lower() or "decision" in p.parent.name.lower()})[:4]
    api = [rel(root, p) for p in fs if re.match(r"^(openapi|swagger).*\.(ya?ml|json)$", p.name, re.I)][:4]
    ids = Counter()
    for p in docs[:400]:
        for m in ID_FORM.finditer(read(p)):
            ids[m.group(1)] += 1
    return {"readme": any(p.name.lower() == "readme.md" and p.parent == root for p in docs), "folders": folders, "requirement_like": like, "adr_folders": adr, "api_specs": api, "ids_in_docs": dict(ids.most_common(6))}


def git_of(root: Path) -> dict:
    if not (root / ".git").exists():
        return {"repo": False}
    subj = git(root, "log", "-n", "60", "--format=%s").splitlines()
    conv = sum(bool(re.match(r"^(feat|fix|docs|refactor|perf|test|build|ci|chore|style|revert)(\([^)]*\))?!?: ", s)) for s in subj)
    base = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").removeprefix("origin/") or next((b for b in ("main", "master") if git(root, "rev-parse", "--verify", "-q", b)), None)
    branches = [b.strip().removeprefix("* ") for b in git(root, "branch", "--format=%(refname:short)").splitlines()][:30]
    typed = sum(bool(re.match(r"^(feat|fix|chore|docs|refactor|hotfix)/", b)) for b in branches)
    return {"repo": True, "base_branch": base, "commits_sampled": len(subj), "conventional_commits": f"{conv} of {len(subj)}" if subj else "none", "typed_branches": f"{typed} of {len(branches)}" if branches else "none"}


def ci_of(root: Path, fs: list) -> list:
    out = []
    for p in fs:
        r = rel(root, p)
        if r.startswith(".github/workflows/") or r in (".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml", ".circleci/config.yml"):
            out.append(r)
    return out[:6]


def arch_of(root: Path, fs: list) -> list:
    out = []
    names = {p.name for p in fs}
    if ".importlinter" in names or any("importlinter" in read(p) for p in fs if p.name == "pyproject.toml"):
        out.append("import-linter")
    if any(n.startswith(".dependency-cruiser") for n in names):
        out.append("dependency-cruiser")
    if any(re.search(r"architecture", p.name, re.I) and re.search(r"test", p.name, re.I) for p in fs):
        out.append("an architecture test")
    if any("archunit" in read(p).lower() for p in fs if p.name in ("pom.xml", "build.gradle")):
        out.append("ArchUnit")
    return out


def discover(root: Path) -> dict:
    fs = files(root)
    st = dict(sorted(stacks(root, fs).items()))  # a stable order, so the report and the proposal do not change between runs
    tests = tests_of(root, fs)
    docs = docs_of(root, fs)
    g = git_of(root)
    ci = ci_of(root, fs)
    arch = arch_of(root, fs)
    has_harness = (root / "vbench.json").exists() or (root / ".claude/vbench.json").exists()
    prefix = next((p for p in ("UC", "US", "REQ", "FR") if p in docs["ids_in_docs"]), None)

    proposed = {"base_branch": g.get("base_branch"), "tests_dirs": tests["folders"] or [], "test_stack": next((x["test_framework"] for x in st.values() if x.get("test_framework") in ("pytest", "vitest", "playwright")), None),
                "stacks": {s["name"]: {k: v for k, v in s.items() if k != "name"} for s in st.values()}, "areas": {}, "adoption": {"default": "legacy"}}
    if prefix:
        proposed["id_prefix"] = prefix if prefix == "UC" else "UC"
    steps = [
        ("0 Observe", "this report", "done"),
        ("1 Mark the seams", "name the areas of the code and set each to legacy, adopting or adopted in vbench.json", "ready" if st else "needs a stack to be named first"),
        ("2 Hold the line", "record today's gaps as a baseline so only new gaps fail", "ready" if tests["files"] else "no tests found: start by writing characterisation tests for the area you will change"),
        ("3 New work follows the V", "requirements, criteria, reviewers, test first for new and changed work", "ready" if docs["folders"] or docs["requirement_like"] else "no requirement documents found: start with vbench-req on the first change"),
        ("4 Tighten", "move an area to adopted so its gaps fail instead of warn", "later"),
        ("5 Retire the old way", "when every area is adopted", "later"),
    ]
    gaps = []
    if not tests["files"]:
        gaps.append("no tests found")
    elif not tests["traced_to_ids"]:
        gaps.append("tests do not name a requirement or criterion, so none can be traced yet")
    if not docs["requirement_like"]:
        gaps.append("no requirement or use case documents found")
    if not ci:
        gaps.append("no CI configuration found")
    if not arch:
        gaps.append("no architecture test found (layers are not enforced)")
    if g.get("repo") and g.get("conventional_commits", "").startswith("0 "):
        gaps.append("commits are not in the conventional form")
    return {"root": str(root), "already_has_harness_config": has_harness, "git": g, "stacks": list(st.values()), "tests": tests, "docs": docs, "ci": ci, "architecture_checks": arch, "has_claude_config": (root / ".claude").is_dir() or (root / "CLAUDE.md").exists(), "proposed_vbench_json": proposed, "ladder": [{"step": a, "what": b, "state": c} for a, b, c in steps], "gaps": gaps}


def render(d: dict) -> str:
    g, t, dc = d["git"], d["tests"], d["docs"]
    L = [f"# What is in {Path(d['root']).name}", ""]
    if d["already_has_harness_config"]:
        L += ["A vbench.json already exists here. Read it before changing anything.", ""]
    L += ["## Found", ""]
    L += [f"- **Stacks:** " + ("; ".join(f"{s['path']} ({s['language']}{', ' + s['framework'] if s.get('framework') else ''}{', tests: ' + s['test_framework'] if s.get('test_framework') else ''})" for s in d["stacks"]) or "none recognised")]
    L += [f"- **Tests:** " + (", ".join(f"{n} {k} test files" for k, n in t["files"].items()) or "none found") + (f"; in {', '.join(t['folders'])}" if t["folders"] else "")]
    L += [f"- **Tests that name a requirement or criterion:** {sum(t['traced_to_ids'].values()) or 'none'}"]
    L += [f"- **Docs:** " + (", ".join(dc["folders"]) or "no docs folder") + (f"; requirement-like files: {len(dc['requirement_like'])}" if dc["requirement_like"] else "; no requirement-like files") + (f"; decision records in {', '.join(dc['adr_folders'])}" if dc["adr_folders"] else "") + (f"; API specs: {', '.join(dc['api_specs'])}" if dc["api_specs"] else "")]
    L += [f"- **Ids in the docs:** " + (", ".join(f"{k} x{v}" for k, v in dc["ids_in_docs"].items()) or "none")]
    L += [f"- **Git:** " + (f"base {g.get('base_branch')}, conventional commits {g['conventional_commits']}, typed branches {g['typed_branches']}" if g.get("repo") else "not a git repository")]
    L += [f"- **CI:** {', '.join(d['ci']) or 'none found'}", f"- **Architecture checks:** {', '.join(d['architecture_checks']) or 'none found'}", f"- **Claude config here:** {'yes' if d['has_claude_config'] else 'no'}", ""]
    if d["gaps"]:
        L += ["## Gaps the harness would help with", ""] + [f"- {x}" for x in d["gaps"]] + [""]
    L += ["## The adoption ladder, for this project", "", "| Step | What | State |", "|---|---|---|"] + [f"| {s['step']} | {s['what']} | {s['state']} |" for s in d["ladder"]] + [""]
    L += ["## A proposed vbench.json", "", "For a person to read and accept. Nothing was written.", "", "```json", json.dumps(d["proposed_vbench_json"], indent=2), "```"]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("discover")
    p.add_argument("root", nargs="?", default=".")
    p.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"{root} is not a folder", file=sys.stderr)
        return 2
    d = discover(root)
    print(json.dumps(d, indent=2) if args.json else render(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
