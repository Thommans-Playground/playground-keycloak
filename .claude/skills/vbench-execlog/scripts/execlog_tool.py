#!/usr/bin/env python3
"""execlog_tool.py: checks the task files of the execution logs in docs/execution-logs/ (ADR 0022).

A task is one slice that can be built and tested on its own. A step is one behaviour inside it, with one failing test and the
code that makes it pass. A task file is a code-along: a header, a link to its entry in summary.md, the run command, and steps.

  execlog_tool.py check [PATH ...]   every task file (TSK-*.md) under the paths, default docs/execution-logs (exit 1 if not ok)
  execlog_tool.py shape              print the shape of a task file, to copy

A task file passes when: its header names the task, use case, criteria and the commit its code matches; it links to an entry
of summary.md that exists; it has steps numbered from 1; each step has a **Test** line naming its level (Unit, API,
Integration or Architecture) and a code block, a **Code** line and a code block, and a **Logic.** paragraph; each code block that
names a file is a word for word copy of part of that file (unless its first line says `stage N shape`); there is no em or en
dash. It cannot tell whether a test is a good one or the logic well explained: a person reads that.

It reads files and writes none. Standard library only."""

import argparse
import re
import sys
from pathlib import Path

LEVELS = ("Unit", "API", "Integration", "Architecture")
HEADER = ("Task ID", "Use Case", "Criteria", "Code matched at")
FENCE = re.compile(r"```[a-z]*\n(.*?)```", re.S)
SHAPE = """# Task P1.5: Check the name

**Task ID:** TSK-P1.5 · **Use Case:** UC-P1 · **Criteria:** AC-12 · **Code matched at:** `7481263`

What this does and why: [summary, task P1.5](summary.md#p15-check-the-name).

Run from `apps/api/`: `uv run pytest tests/test_projects_input.py -q`

## Step 1: the length rule (AC-12)

**Test** (Unit): one sentence on what the test pins.

```python
# apps/api/tests/test_projects_input.py
<the test, copied from the file>
```

**Code**:

```python
# apps/api/app/projects/domain/name.py
<the code, copied from the file>
```

**Logic.** The few lines that explain why it is written this way.
"""


def slug(heading: str) -> str:
    """The anchor GitHub gives a heading."""
    text = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return text.replace(" ", "-")


def find_file(root: Path, name: str):
    for base in (root, root / "apps" / "api", root / "apps" / "web"):
        if (base / name).is_file():
            return base / name
    return None


def check_blocks(root: Path, body: str, label: str) -> list:
    out = []
    for block in FENCE.findall(body):
        lines = block.splitlines()
        if not lines or not re.match(r"(#|//) \S", lines[0]):
            continue
        head = lines[0][2:].strip()
        name, _, rest = head.partition(",")
        if " " in name.strip() or "stage" in rest:
            continue
        path = find_file(root, name.strip())
        if path is None:
            continue
        text = path.read_text(encoding="utf-8")
        code = "\n".join(lines[1:]).strip("\n")
        if code and code not in text:
            out.append(f"{label}: the block for {name.strip()} differs from the file")
    return out


def check_task(root: Path, task: Path) -> list:
    label = task.name
    text = task.read_text(encoding="utf-8")
    out = []
    for field in HEADER:
        if f"**{field}:**" not in text:
            out.append(f"{label}: the header has no {field}")
    if "—" in text or "–" in text:
        out.append(f"{label}: an em or en dash (use a colon, a comma or brackets)")
    summary = task.parent / "summary.md"
    link = re.search(r"\]\(summary\.md#([^)]+)\)", text)
    if not link:
        out.append(f"{label}: no link to its entry in summary.md")
    elif not summary.is_file() or link.group(1) not in {
        slug(h) for h in re.findall(r"(?m)^#{2,6} (.+)$", summary.read_text(encoding="utf-8"))
    }:
        out.append(f"{label}: summary.md has no entry for #{link.group(1)}")
    parts = re.split(r"(?m)^## Step (\d+): ", text)
    steps = list(zip(parts[1::2], parts[2::2]))
    if not steps:
        out.append(f"{label}: no step (a '## Step 1: ...' heading)")
    for i, (num, body) in enumerate(steps, 1):
        where = f"{label} step {num}"
        if int(num) != i:
            out.append(f"{where}: the step number should be {i}")
        test = re.search(r"\*\*Test\*\* \(([^)]*)\)", body)
        code = body.find("**Code**")
        logic = re.search(r"\*\*Logic\.\*\*\s*\S", body)
        if not test:
            out.append(f"{where}: no **Test** line with a level, for example **Test** (Unit)")
        else:
            levels = [v.strip() for v in re.split(r",| and ", test.group(1)) if v.strip()]
            if not levels or any(v not in LEVELS for v in levels):
                out.append(f"{where}: the test level must be one of {', '.join(LEVELS)}")
        if code < 0:
            out.append(f"{where}: no **Code** line")
        if test and code >= 0:
            if not FENCE.search(body[test.end() : code]):
                out.append(f"{where}: no test block between **Test** and **Code**")
            if not FENCE.search(body[code : logic.start() if logic else len(body)]):
                out.append(f"{where}: no code block after **Code**")
        if not logic:
            out.append(f"{where}: no **Logic.** paragraph")
        out.extend(check_blocks(root, body, where))
    return out


def check(root: Path, paths=None) -> list:
    root = Path(root)
    bases = [Path(p) for p in paths] if paths else [root / "docs" / "execution-logs"]
    tasks = sorted(t for b in bases for t in (b.rglob("TSK-*.md") if b.is_dir() else [b]))
    out = []
    for t in tasks:
        out.extend(check_task(root, t))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check the task files")
    c.add_argument("paths", nargs="*")
    sub.add_parser("shape", help="print the shape of a task file")
    a = ap.parse_args(argv)
    if a.cmd == "shape":
        print(SHAPE)
        return 0
    root = Path(__file__).resolve().parents[4]
    problems = check(root, a.paths)
    for p in problems:
        print(p)
    print(f"{len(problems)} problem(s)" if problems else "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
