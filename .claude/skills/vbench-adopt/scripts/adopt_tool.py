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
DOC_FOLDER = re.compile(r"^(docs?|documentation|design|specs?|study[-_ ]?guides?|reports?|notes?|wiki)$", re.I)
ID_FORM = re.compile(r"\b([A-Z]{2,4})-([A-Z]?\d+)\b")
ROLES = {"FR": "requirement", "NFR": "requirement", "REQ": "requirement", "STK": "requirement", "US": "story",
         "UC": "use case", "AC": "criterion", "TC": "test case"}
NOISE = {"UTF", "SHA", "ISO", "RFC", "CVE", "CWE", "MD", "HTTP", "TLS", "AES", "RSA", "PEP", "JDK", "ADR", "API", "OWASP", "ASVS"}
TAG_WORDS = r"(?:Verifies|Covers|Requirement|Implements|Validates)"
BRANCH_STYLES = [("feat/", r"^feat/"), ("feature/", r"^feature/"), ("fix/", r"^fix/"), ("bugfix/", r"^bugfix/"), ("hotfix/", r"^hotfix/"),
                 ("chore/", r"^chore/"), ("docs/", r"^docs/"), ("refactor/", r"^refactor/"), ("uc-", r"^uc-")]
SUPPORTED_TESTS = ("pytest", "vitest", "playwright")
LAYER_NAMES = ("domain", "application", "adapters", "ports")
EXT_LANG = {".swift": "swift", ".kt": "kotlin", ".cs": "csharp", ".rb": "ruby", ".php": "php", ".dart": "dart", ".scala": "scala", ".ex": "elixir"}
OVERLAP = re.compile(r"v-?model|ddd|domain|tdd|requirement|use-?case|acceptance|trace|adopt|vcycle", re.I)


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


def configured(text: str, tool: str) -> bool:
    """A tool is configured when it has its own table or file, or is a real dependency (not a word in a comment)."""
    return bool(re.search(rf"\[tool\.{tool}[\].]", text) or re.search(rf"(?m)^\s*[\"']?{tool}(?=[\s\"'<>=~!\[,;]|$)", text))


def at(path: str, cmd: str) -> str:
    return cmd if path == "." else cmd.replace("{p}", path)


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
            here = {q.name for q in p.parent.iterdir()} if p.parent.is_dir() else set()
            if re.search(r"pytest", text):
                s["tests"] = "pytest" if folder == "." else f"pytest {folder}"
                s["test_framework"] = "pytest"
                s.setdefault("test_frameworks", ["pytest"])
            if configured(text, "ruff") or {"ruff.toml", ".ruff.toml"} & here:
                s["lint"] = "ruff check ." if folder == "." else f"ruff check {folder}"
            if configured(text, "mypy") or {"mypy.ini", ".mypy.ini"} & here:
                s["typecheck"] = "mypy ." if folder == "." else f"mypy {folder}"
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
            used = [n for n in ("playwright", "vitest", "jest") if n in test_script or n in deps or f"@{n}/test" in deps]
            if used:
                s["test_framework"] = used[0] if used[0] != "playwright" or len(used) == 1 else used[1]
                s["test_frameworks"] = used
            elif "node --test" in test_script:
                s["test_framework"] = "node:test"
                s["test_frameworks"] = ["node:test"]
            pre = "npm" if folder == "." else f"npm --prefix {folder}"
            for key, script in (("tests", "test"), ("lint", "lint"), ("typecheck", "typecheck"), ("build", "build")):
                if script in scripts:
                    s[key] = f"{pre} test" if script == "test" else f"{pre} run {script}"
        elif name == "go.mod":
            found.setdefault(folder, {"name": label, "path": folder, "language": "go", "tests": "go test ./..."})
        elif name in ("pom.xml", "build.gradle", "build.gradle.kts"):
            found.setdefault(folder, {"name": label, "path": folder, "language": "java", "tests": "mvn test" if name == "pom.xml" else "gradle test"})
        elif name == "Cargo.toml":
            found.setdefault(folder, {"name": label, "path": folder, "language": "rust", "tests": "cargo test"})
        elif name == "Package.swift" or (name == "project.pbxproj" and p.parent.suffix == ".xcodeproj"):
            base = p.parent.parent if name == "project.pbxproj" else p.parent
            f2 = rel(root, base) if base != root else "."
            found.setdefault(f2, {"name": re.sub(r"[^a-z0-9]+", "-", (base.name if base != root else root.name).lower()).strip("-") or "app", "path": f2, "language": "swift"})
    langs = Counter(EXT_LANG[p.suffix] for p in fs if p.suffix in EXT_LANG)
    for lang, n in langs.items():
        if n >= 3 and not any(x["language"] == lang for x in found.values()):
            found.setdefault(".", {"name": re.sub(r"[^a-z0-9]+", "-", root.name.lower()).strip("-") or "app", "path": ".", "language": lang})
    return found


def pattern_of(family: str, samples) -> str:
    letter = [x for x in samples if re.match(r"^[A-Z]", x)]
    return rf"{family}-[A-Z]?\d+" if letter and len(letter) < len(samples) else rf"{family}-[A-Z]\d+" if letter else rf"{family}-\d+"


def tests_of(root: Path, fs: list) -> dict:
    pats = {"python": re.compile(r"^(test_.*|.*_test)\.py$"), "js": re.compile(r".*\.(test|spec)\.[jt]sx?$"), "go": re.compile(r".*_test\.go$"), "java": re.compile(r".*Tests?\.java$"), "swift": re.compile(r".*Tests?\.swift$")}
    counts, dirs = Counter(), Counter()
    tagged = Counter()
    fam = {}
    marker = re.compile(r"pytest\.mark\.\w+\(\s*[\"']([A-Z]{2,4})-([A-Z]?\d+)")
    comment = re.compile(rf"\b{TAG_WORDS}\b[: ]+(.*)")
    title = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)|\b(?:it|test|describe)(?:\.\w+)?\(\s*[\"'`]([^\"'`]*)")

    def hit(family, kind, ident):
        e = fam.setdefault(family, {"marker": 0, "comment": 0, "title": 0, "samples": set()})
        e[kind] += 1
        e["samples"].add(ident)
    for p in fs:
        for kind, rx in pats.items():
            if rx.match(p.name):
                counts[kind] += 1
                dirs[rel(root, p.parent).split("/")[0] if p.parent != root else "."] += 1
                text = read(p)
                kinds = set()
                for m in marker.finditer(text):
                    hit(m.group(1), "marker", m.group(2)); kinds.add("marker")
                for m in comment.finditer(text):
                    for f, n in ID_FORM.findall(m.group(1)):
                        hit(f, "comment", n); kinds.add("comment")
                for line in text.splitlines():
                    t = title.search(line)
                    if not t:
                        continue
                    if t.group(1):
                        for f, n in re.findall(r"(?<![a-z])([a-z]{2,4})_(\d+)(?!\d)", t.group(1)):
                            if f.upper() in ROLES:
                                hit(f.upper(), "title", n); kinds.add("title")
                    else:
                        for f, n in ID_FORM.findall(t.group(2) or ""):
                            hit(f, "title", n); kinds.add("title")
                for k in kinds:
                    tagged[k] += 1
    families = {f: {**{k: v for k, v in e.items() if k != "samples"}, "pattern": pattern_of(f, e["samples"])} for f, e in sorted(fam.items())}
    return {"files": dict(counts), "folders": [d for d, _ in dirs.most_common(4)], "traced_to_ids": dict(tagged), "id_families": families}


def docs_of(root: Path, fs: list) -> dict:
    docs = [p for p in fs if p.suffix.lower() in (".md", ".rst", ".adoc")]
    top = lambda p: rel(root, p).split("/")[0]
    doc_folders = Counter(top(p) for p in docs if p.parent != root and DOC_FOLDER.match(top(p)))
    like = [rel(root, p) for p in docs if DOC_WORDS.search(p.name) or DOC_WORDS.search(p.parent.name)][:12]
    adr = sorted({rel(root, p.parent) for p in docs if re.match(r"^\d{3,4}[-_]", p.name) and "adr" in rel(root, p).lower() or "decision" in p.parent.name.lower()})[:4]
    api = [rel(root, p) for p in fs if re.match(r"^(openapi|swagger).*\.(ya?ml|json)$", p.name, re.I)][:4]
    counts, samples = Counter(), {}
    for p in docs[:400]:
        for f, n in ID_FORM.findall(read(p)):
            counts[f] += 1
            samples.setdefault(f, set()).add(n)
    ids = {}
    for f, c in counts.most_common():
        if f in ROLES:
            role = ROLES[f]
        elif f not in NOISE and len(samples[f]) >= 3:
            role = "unknown"
        else:
            continue
        ids[f] = {"count": c, "distinct": len(samples[f]), "role": role, "pattern": pattern_of(f, samples[f])}
    return {"readme": any(p.name.lower() == "readme.md" and p.parent == root for p in docs), "folders": sorted(doc_folders), "doc_folders": dict(sorted(doc_folders.items())), "requirement_like": like, "adr_folders": adr, "api_specs": api, "ids_in_docs": ids}


def git_of(root: Path) -> dict:
    if not (root / ".git").exists():
        return {"repo": False}
    subj = git(root, "log", "-n", "60", "--format=%s").splitlines()
    conv = sum(bool(re.match(r"^(feat|fix|docs|refactor|perf|test|build|ci|chore|style|revert)(\([^)]*\))?!?: ", s)) for s in subj)
    base = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").removeprefix("origin/") or next((b for b in ("main", "master") if git(root, "rev-parse", "--verify", "-q", b)), None)
    raw = git(root, "branch", "-a", "--format=%(refname:short)").splitlines()
    branches = sorted({b.strip().removeprefix("origin/") for b in raw if b.strip() and b.strip() not in ("origin", "origin/HEAD")})[:200]
    styles = Counter()
    for b in branches:
        for name, rx in BRANCH_STYLES:
            if re.match(rx, b, re.I):
                styles[name] += 1
                break
    typed = sum(styles.values())
    return {"repo": True, "base_branch": base, "commits_sampled": len(subj), "conventional_commits": f"{conv} of {len(subj)}" if subj else "none", "typed_branches": f"{typed} of {len(branches)}" if branches else "none", "branch_styles": dict(styles.most_common()), "dominant_branch_style": styles.most_common(1)[0][0] if styles else None}


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


def layers_of(root: Path, fs: list) -> list:
    names = {part.lower() for p in fs for part in p.relative_to(root).parts[:-1][:5]}
    found = sorted(n for n in LAYER_NAMES if n in names)
    return found if "domain" in found and len(found) >= 2 else []


def skills_of(root: Path) -> dict:
    out = {}
    for d in (".claude/skills", ".agents/skills"):
        base = root / d
        if base.is_dir():
            out[d] = sorted(x.name for x in base.iterdir() if not x.name.startswith("."))
    return out


def keycloak_of(root: Path, fs: list) -> bool:
    return any(re.match(r"^(docker-)?compose.*\.ya?ml$", p.name) and "keycloak" in read(p).lower() for p in fs)


def discover(root: Path) -> dict:
    fs = files(root)
    st = dict(sorted(stacks(root, fs).items()))  # a stable order, so the report and the proposal do not change between runs
    tests = tests_of(root, fs)
    docs = docs_of(root, fs)
    g = git_of(root)
    ci = ci_of(root, fs)
    arch = arch_of(root, fs)
    has_harness = (root / "vbench.json").exists() or (root / ".claude/vbench.json").exists()
    layers = layers_of(root, fs)
    skills = skills_of(root)
    warnings = []
    foreign = sorted(n for names in skills.values() for n in names if not n.startswith("vbench-"))
    if foreign:
        hit = [n for n in foreign if OVERLAP.search(n)]
        warnings.append("skills already installed here (" + ", ".join(foreign[:8]) + ") may collide with the harness skills" + (f"; overlapping jobs likely: {', '.join(hit)}" if hit else "") + ". Compare names and jobs before adding the vbench skills.")

    used = sorted({f for x in st.values() for f in x.get("test_frameworks", []) if f in SUPPORTED_TESTS})
    unsupported = []
    for x in st.values():
        if not set(x.get("test_frameworks", [])) & set(SUPPORTED_TESTS):
            unsupported.append({"path": x["path"], "language": x["language"], "test_framework": x.get("test_framework"), "reason": "unsupported by the harness's test skeletons (it supports pytest, vitest, playwright); this is not a project gap"})
    test_stack_note = f"one framework in use: {used[0]}" if len(used) == 1 else ("none of pytest, vitest, playwright found" if not used else f"several in use ({', '.join(used)}), so test_stack is left out; set it per piece of work")

    fam_tags = {f: sum(v[k] for k in ("marker", "comment", "title")) for f, v in tests["id_families"].items() if ROLES.get(f) != "use case"}
    id_patterns = {}
    if fam_tags:
        top = max(fam_tags, key=lambda f: fam_tags[f])
        src = docs["ids_in_docs"].get(top, {}).get("pattern") or tests["id_families"][top]["pattern"]
        id_patterns["criterion"] = src
    elif "AC" in docs["ids_in_docs"]:
        id_patterns["criterion"] = docs["ids_in_docs"]["AC"]["pattern"]
    reqs = [v["pattern"] for f, v in docs["ids_in_docs"].items() if v["role"] == "requirement"]
    if reqs:
        id_patterns["requirement"] = reqs[0] if len(reqs) == 1 else "(?:" + "|".join(reqs) + ")"
    if "UC" in docs["ids_in_docs"]:
        id_patterns["usecase"] = docs["ids_in_docs"]["UC"]["pattern"]

    packs = ["core"] + (["ddd"] if arch else []) + (["keycloak"] if keycloak_of(root, fs) else [])
    allowed = {"path", "language", "framework", "tests", "typecheck", "lint", "build", "database", "test_framework"}
    proposed = {"base_branch": g.get("base_branch"), "tests_dirs": tests["folders"] or [],
                "stacks": {s["name"]: {k: v for k, v in s.items() if k in allowed} for s in st.values()}, "areas": {},
                "adoption": {"default": "legacy"}, "packs": packs}
    if len(used) == 1:
        proposed["test_stack"] = used[0]
    if id_patterns:
        proposed["id_patterns"] = id_patterns
    if "UC" in docs["ids_in_docs"]:
        proposed["id_prefix"] = "UC"
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
    if not arch and layers:
        gaps.append(f"layers present but no test enforces them ({', '.join(layers)})")
    elif not arch:
        gaps.append("no architecture test found and no layered folders (domain, application, adapters, ports)")
    if g.get("repo") and g.get("conventional_commits", "").startswith("0 "):
        gaps.append("commits are not in the conventional form")
    return {"root": str(root), "already_has_harness_config": has_harness, "git": g, "stacks": list(st.values()), "tests": tests, "docs": docs, "ci": ci, "architecture_checks": arch, "layers": layers, "agent_skills": skills, "warnings": warnings, "unsupported_stacks": unsupported, "test_stack_note": test_stack_note, "has_claude_config": (root / ".claude").is_dir() or (root / "CLAUDE.md").exists(), "proposed_vbench_json": proposed, "ladder": [{"step": a, "what": b, "state": c} for a, b, c in steps], "gaps": gaps}


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
