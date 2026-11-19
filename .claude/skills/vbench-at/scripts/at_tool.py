#!/usr/bin/env python3
"""Check the link between a project's acceptance criteria and its acceptance tests, and draft test skeletons.

An acceptance criterion is a Given, When, Then row in docs/requirements/acceptance-criteria.md. An acceptance
test is an automated test that runs ONE criterion through the front door (the API). It carries a tag in a
comment or its name:

    Verifies AC-12 [reviewed 7a2439b]

The hash is a short fingerprint of the criterion (given, when, then, test level) as a person last checked the
test against it. It is the same fingerprint vbench-uc keeps. If the criterion changes, the hash no longer
matches and the test is STALE until it is reviewed. Tests live in tests/acceptance by default.

Commands (run from the repo root, or pass --root):

  report                 which acceptance criteria have no test, which tests name a criterion that does not
                         exist, which tests are stale, and which use cases list a criterion with no test.
                         Every line is a recorded fact, never a guess. Exit code 1 if a test names an unknown
                         criterion or is stale.
  show AC-ID             one criterion, the requirements it proves, the use cases that run it, its tests
  skeleton AC-ID         draft a failing test from a criterion for a person to fill in (prints it; --write saves
                         it, and refuses to overwrite). It never invents an assertion.
  stamp AC-ID            record that a person has checked the tests of this criterion against its current text

Options: --tests-dir DIR (repeatable, default tests/acceptance), --release R1 (only criteria whose requirements
are planned for that release), --stack pytest|playwright|vitest for a skeleton (default: vbench.json
test_stack, else detected from the repo, else pytest).

Uses only the standard library. This tool never edits the two requirements files.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "vbench-uc" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "vbench-req" / "scripts"))
import req_tool as rq  # noqa: E402
import uc_tool as uc  # noqa: E402

TESTS_DIR = "tests/acceptance"   # default; vbench.json tests_dirs overrides it
DEFAULT_STACK = "pytest"
TAG = re.compile(r"Verifies\s+(AC-\d+(?:\s*,\s*AC-\d+)*)(?:\s*\[reviewed\s+([0-9a-f]{7})\])?")
# The pytest form: @pytest.mark.ac("AC-12") or @pytest.mark.ac("AC-12", reviewed="7a2439b"). One marker for each criterion.
MARK = re.compile(r"""mark\.ac\(\s*["'](AC-\d+)["']\s*(?:,\s*reviewed\s*=\s*["']([0-9a-f]{7})["']\s*)?\)""")
EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".java", ".kt", ".go", ".rb", ".cs", ".feature"}
SKIP = {"node_modules", ".git", "__pycache__", ".next", "dist", "build"}
STACKS = {
    "vitest": (".test.ts", "ac-{n}-{slug}"),
    "playwright": (".spec.ts", "ac-{n}-{slug}"),
    "pytest": (".py", "test_ac_{n}_{slug}"),
}


# ----------------------------------------------------------------------------- reading

def criteria(root):
    return {r["id"]: r for r in rq.read_rows(root / rq.PATHS["ac"])}


def scan(root, dirs):
    """Every `Verifies AC-n` tag and every `@pytest.mark.ac("AC-n")` marker in the test folders:
    (path, line number, ac id, recorded hash or None). A comment may list several ids (`Verifies AC-5, AC-63`);
    the recorded hash then belongs to none of them."""
    found = []
    for d in dirs:
        base = (root / d)
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix not in EXTENSIONS or any(part in SKIP for part in p.parts):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for n, line in enumerate(text.splitlines(), 1):
                for m in TAG.finditer(line):
                    ids = re.findall(r"AC-\d+", m.group(1))
                    for ac_id in ids:
                        found.append((p, n, ac_id, m.group(2) if len(ids) == 1 else None))
                for m in MARK.finditer(line):
                    found.append((p, n, m.group(1), m.group(2)))
    return found


def in_release(row, reqs_by_id, release):
    if not release:
        return True
    refs = [x.strip() for x in row["requirements"].split(";") if x.strip()]
    return any(reqs_by_id.get(r, {}).get("release") == release for r in refs)


def rel(root, p):
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


# ----------------------------------------------------------------------------- report

def cmd_report(root, dirs, release):
    acs = criteria(root)
    reqs_by_id = {r["id"]: r for r in rq.read_rows(root / rq.PATHS["req"])}
    tags = scan(root, dirs)
    tested = {}
    for p, n, ac, h in tags:
        tested.setdefault(ac, []).append((p, n, h))

    wanted = {i: r for i, r in acs.items()
              if r["test_level"] == "acceptance" and r["status"] != "retired" and in_release(r, reqs_by_id, release)}
    existing_dirs = [d for d in dirs if (root / d).is_dir()]
    scope = f" for release {release}" if release else ""
    print(f"{len(wanted)} acceptance criteria{scope}; tests are looked for in {', '.join(dirs)}"
          + ("" if existing_dirs else " (no such folder yet)"))
    print(f"{len(tags)} Verifies tag(s) found for {len(tested)} criterion(s)\n")

    problems, gaps = 0, 0

    missing = [i for i in wanted if i not in tested]
    gaps += len(missing)
    print(f"ACCEPTANCE CRITERIA WITH NO TEST ({len(missing)})")
    if not missing:
        print("  none")
    for i in missing[:60]:
        r = wanted[i]
        print(f"  {i} (proves {r['requirements']}): given {r['given']}; when {r['when']}; then {r['then']}")
    if len(missing) > 60:
        print(f"  ... and {len(missing) - 60} more")
    print()

    unknown = [(p, n, ac) for p, n, ac, _ in tags if ac not in acs]
    problems += len(unknown)
    print(f"TESTS THAT NAME A CRITERION THAT DOES NOT EXIST ({len(unknown)})")
    if not unknown:
        print("  none")
    for p, n, ac in unknown:
        print(f"  {rel(root, p)}:{n} says Verifies {ac}")
    print()

    stale, unreviewed = [], []
    for p, n, ac, h in tags:
        if ac not in acs:
            continue
        now = uc.ac_hash(acs[ac])
        if h is None:
            unreviewed.append((p, n, ac, now))
        elif h != now:
            stale.append((p, n, ac, h, now))
    problems += len(stale)
    print(f"STALE TESTS: THE CRITERION CHANGED SINCE THE TEST WAS REVIEWED ({len(stale)})")
    if not stale:
        print("  none")
    for p, n, ac, h, now in stale:
        print(f"  {rel(root, p)}:{n} {ac}: recorded {h}, now {now}. Check the test against the criterion, then stamp it")
    print()
    if unreviewed:
        print(f"TESTS WITH NO REVIEW HASH ({len(unreviewed)})")
        for p, n, ac, now in unreviewed:
            print(f"  {rel(root, p)}:{n} {ac}: add [reviewed {now}] once a person has checked it (stamp {ac})")
        print()

    other = sorted({ac for ac in tested if ac in acs and acs[ac]["test_level"] != "acceptance"})
    if other:
        print(f"TESTS FOR CRITERIA THAT ARE NOT ACCEPTANCE LEVEL ({len(other)})")
        for ac in other:
            print(f"  {ac} is a {acs[ac]['test_level']} criterion, but a test in {', '.join(dirs)} names it")
        print()

    ucs = uc.load_ucs(root)
    lines = []
    for path, h, _ in ucs:
        if "_error" in h:
            continue
        for ac in uc.ids_of(h.get("criteria")):
            r = acs.get(ac)
            if r and r["test_level"] == "acceptance" and ac not in tested:
                lines.append(f"  {h['id']} lists {ac}: no test")
    print(f"USE CASES THAT LIST A CRITERION WITH NO TEST ({len(lines)})")
    if not lines:
        print("  none" + ("" if ucs else " (there are no use case files yet)"))
    print("\n".join(lines))
    print()

    print(f"{problems} problem(s), {gaps} criteria with no test")
    return 1 if problems else 0


# ----------------------------------------------------------------------------- show

def cmd_show(root, dirs, ac_id):
    acs = criteria(root)
    r = acs.get(ac_id)
    if not r:
        print(f"No criterion {ac_id}.")
        return 1
    reqs_by_id = {x["id"]: x for x in rq.read_rows(root / rq.PATHS["req"])}
    print(f"{ac_id}  [{r['test_level']}, {r['status']}]  hash {uc.ac_hash(r)}")
    print(f"  given {r['given']}\n  when  {r['when']}\n  then  {r['then']}")
    if r["notes"]:
        print(f"  notes: {r['notes']}")
    for ref in [x.strip() for x in r["requirements"].split(";") if x.strip()]:
        q = reqs_by_id.get(ref)
        print(f"  proves {ref}: {q['statement'] if q else 'NOT FOUND in requirements.md'}")
    for path, h, _ in uc.load_ucs(root):
        if "_error" not in h and ac_id in uc.ids_of(h.get("criteria")):
            print(f"  run by {h['id']} {h.get('name')}")
    tags = [(p, n, h2) for p, n, ac, h2 in scan(root, dirs) if ac == ac_id]
    if not tags:
        print("  tests: none" + ("" if r["test_level"] == "acceptance" else f" (a {r['test_level']} criterion: not written here)"))
    for p, n, h2 in tags:
        state = "no review hash" if h2 is None else ("up to date" if h2 == uc.ac_hash(r) else f"STALE (recorded {h2})")
        print(f"  test {rel(root, p)}:{n}: {state}")
    return 0


# ----------------------------------------------------------------------------- skeleton

def slug(text, words=6, sep="-"):
    s = re.sub(r"[^a-z0-9]+", sep, " ".join(text.lower().split()[:words])).strip(sep)
    return s or "criterion"


def literal(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def skeleton_text(stack, row):
    n = row["id"].split("-")[1]
    h = uc.ac_hash(row)
    head = [f"Verifies {row['id']} [reviewed {h}]", "",
            f"Given {row['given']}", f"When  {row['when']}", f"Then  {row['then']}", "",
            "Drafted by vbench-at from the criterion. The steps and the checks are for a person to write."]
    title = f"{row['id']}: when {row['when']}, then {row['then']}"
    if stack in ("vitest", "playwright"):
        comment = "\n".join(("// " + ln).rstrip() for ln in head)
        if stack == "vitest":
            body = (f'import {{ describe, it }} from "vitest";\n\n'
                    f"describe({literal(row['id'])}, () => {{\n"
                    f"  it({literal('when ' + row['when'] + ', then ' + row['then'])}, async () => {{\n"
                    f"    throw new Error({literal(row['id'] + ' is not written yet')});\n  }});\n}});\n")
        else:
            body = (f'import {{ test }} from "@playwright/test";\n\n'
                    f"test({literal(title)}, async ({{ request }}) => {{\n"
                    f"  throw new Error({literal(row['id'] + ' is not written yet')});\n}});\n")
        return comment + "\n\n" + body
    comment = "\n".join(("# " + ln).rstrip() for ln in head)
    body = (f"import pytest\n\n\ndef test_ac_{n}_{slug(row['when'], 6, '_')}():\n"
            f"    pytest.fail({literal(row['id'] + ' is not written yet')})\n")
    return comment + "\n\n" + body


def cmd_skeleton(root, dirs, ac_id, stack, write):
    acs = criteria(root)
    r = acs.get(ac_id)
    if not r:
        print(f"No criterion {ac_id}.")
        return 1
    if r["test_level"] != "acceptance":
        print(f"REFUSED  {ac_id} is a {r['test_level']} criterion. Write it as a {r['test_level']} test, not an acceptance test.")
        return 1
    if stack not in STACKS:
        print(f"REFUSED  stack must be one of {sorted(STACKS)}. The default is {DEFAULT_STACK}.")
        return 1
    have = [(p, n) for p, n, ac, _ in scan(root, dirs) if ac == ac_id]
    if have:
        print(f"REFUSED  {ac_id} already has a test: {rel(root, have[0][0])}:{have[0][1]}")
        return 1
    ext, pattern = STACKS[stack]
    name = pattern.format(n=ac_id.split("-")[1], slug=slug(r["when"], 6, "_" if stack == "pytest" else "-")) + ext
    path = root / dirs[0] / name
    text = skeleton_text(stack, r)
    if not write:
        print(f"would write {rel(root, path)}\n")
        print(text)
        return 0
    if path.exists():
        print(f"REFUSED  {rel(root, path)} already exists")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {rel(root, path)}. It fails until a person writes it.")
    return 0


# ----------------------------------------------------------------------------- stamp

def cmd_stamp(root, dirs, ac_id):
    acs = criteria(root)
    r = acs.get(ac_id)
    if not r:
        print(f"No criterion {ac_id}.")
        return 1
    now = uc.ac_hash(r)
    files = sorted({p for p, n, ac, h in scan(root, dirs) if ac == ac_id})
    if not files:
        print(f"{ac_id}: no test carries this tag.")
        return 1
    pattern = re.compile(rf"Verifies\s+{re.escape(ac_id)}(?:\s*\[reviewed\s+[0-9a-f]{{7}}\])?")
    marker = re.compile(rf"""mark\.ac\(\s*["']{re.escape(ac_id)}["']\s*(?:,\s*reviewed\s*=\s*["'][0-9a-f]{{7}}["']\s*)?\)""")
    for p in files:
        with open(p, newline="", encoding="utf-8") as f:
            text = f.read()
        new = pattern.sub(f"Verifies {ac_id} [reviewed {now}]", text)
        new = marker.sub(f'mark.ac("{ac_id}", reviewed="{now}")', new)
        if new != text:
            with open(p, "w", newline="", encoding="utf-8") as f:
                f.write(new)
            print(f"{rel(root, p)}: reviewed hash set to {now}")
        else:
            print(f"{rel(root, p)}: already up to date")
    return 0


# ----------------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root")
    ap.add_argument("--tests-dir", action="append", help="where the acceptance tests live (default tests/acceptance)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report")
    r.add_argument("--release")
    s = sub.add_parser("show")
    s.add_argument("id")
    k = sub.add_parser("skeleton")
    k.add_argument("id")
    k.add_argument("--stack", help="pytest, playwright or vitest (default: detected)")
    k.add_argument("--write", action="store_true")
    st = sub.add_parser("stamp")
    st.add_argument("id")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else rq.find_root()
    cfg = rq.use_config(root)
    dirs = a.tests_dir or cfg["tests_dirs"] or [TESTS_DIR]
    if a.cmd == "report":
        return cmd_report(root, dirs, a.release)
    if a.cmd == "show":
        return cmd_show(root, dirs, a.id)
    if a.cmd == "skeleton":
        stack = a.stack or cfg["test_stack"] or rq.config.detect_stack(root)
        return cmd_skeleton(root, dirs, a.id, stack, a.write)
    return cmd_stamp(root, dirs, a.id)


if __name__ == "__main__":
    sys.exit(main())
