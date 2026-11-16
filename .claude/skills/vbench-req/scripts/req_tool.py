#!/usr/bin/env python3
"""Search, check and edit a project's requirements and acceptance criteria.

The requirements are rows in docs/requirements/requirements.csv, and their acceptance criteria are
rows in docs/requirements/acceptance-criteria.csv. This script reads them (and the permissions,
rule inventory, vocabulary and decisions log beside them) so a check for "is this already here?"
does not depend on memory, and it edits the two files safely.

Where the files live comes from vbench.json (see _vbench/config.py); with none, the paths above.

Commands (run from the repo root, or pass --root):

  search "text"           find existing requirements, criteria, rules, permissions and decisions that
                          overlap with the text, and check its shape and wording
  init                    create the empty requirements and acceptance criteria files (a fresh repo)
  next-ids                show the next free FR-, NFR- and AC- numbers
  validate                check both files (unique ids, "shall" wording, complete scenarios, links)
  append requirements     add rows from JSON on stdin (an object or a list), with new ids
  append acceptance       add acceptance criteria from JSON on stdin
  update ID               change fields of one row, from a JSON object on stdin
  Add --dry-run to append or update to show the result without writing.

It uses only the standard library. Exit code 1 means a problem was found or refused.
"""

import argparse
import csv
import io
import json
import math
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_vbench"))
import config  # noqa: E402

REQ_COLS = ["id", "kind", "group", "area", "name", "statement", "quality", "stimulus", "environment",
            "response", "measure", "verification", "release", "today", "status", "objects", "rules",
            "satisfies", "sources", "notes"]
AC_COLS = ["id", "requirements", "given", "when", "then", "test_level", "status", "notes"]

KINDS = {"functional", "quality", "constraint", "process"}
VERIFICATION = {"acceptance test", "integration test", "unit test", "inspection", "demonstration", "analysis"}
RELEASES = {"", "R1", "R2", "R3", "backlog", "parked"}
TODAY = {"built", "not built"}
STATUS = {"draft", "accepted", "retired"}
AC_LEVELS = {"unit", "integration", "acceptance", "manual", "inspection", "future"}
AC_STATUS = {"draft", "accepted", "open", "retired"}
SCENARIO = ["quality", "stimulus", "environment", "response", "measure"]

STOP = set("""the a an and or of to in for with is are be by on at as it its that this from shall should
must may can will system team person people""".split())
# retired words that are also everyday words: flag them as "watch in context", not as errors
COMMON = {"system", "check", "status", "response", "tell", "run", "job", "target", "model", "comment",
          "draft", "owner", "pin", "score", "mapping", "close", "delete", "phase", "scope", "task",
          "opened", "message", "channel", "audit", "ai", "bot", "highlight", "excerpt", "verified"}

PATHS = dict(config.DEFAULTS["paths"])   # relative to the root; use_config(root) applies vbench.json


def use_config(root):
    """Load the repo's settings and point PATHS at its files. Every tool calls this once it knows the root."""
    cfg = config.load(root)
    PATHS.update(cfg["paths"])
    return cfg


# ----------------------------------------------------------------------------- files

def find_root(start=None):
    return config.find_root(start)


def read_rows(path):
    if not Path(path).exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def line_ending(path):
    """Keep the file's own line ending, so an edit does not rewrite every line."""
    if Path(path).exists() and b"\r\n" in Path(path).read_bytes():
        return "\r\n"
    return "\n"


def write_rows(path, cols, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator=line_ending(path))
    w.writeheader()
    w.writerows(rows)
    Path(path).write_bytes(buf.getvalue().encode("utf-8"))


# ----------------------------------------------------------------------------- matching

def tokens(text):
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def similarity(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / math.sqrt(len(a) * len(b))


def shape_notes(text):
    notes = []
    t = text.strip()
    if not (t.startswith("The system shall") or t.startswith("The team shall")):
        notes.append('does not start with "The system shall" or "The team shall"')
    if re.search(r"\b(should|may|will|can)\b", t) and "shall" not in t:
        notes.append('uses should, may, will or can: "shall" says it is mandatory')
    n_and = len(re.findall(r"\band\b", t))
    if n_and:
        notes.append(f'contains "and" {n_and} time(s): check that it says one thing')
    return notes


def retired_words(text, vocab_rows):
    lower = text.lower()
    strict, watch = [], []
    for r in vocab_rows:
        if r.get("kind") != "retired word":
            continue
        for part in re.split(r",\s*", r["term"]):
            word = re.sub(r"\s*\(.*?\)\s*", "", part).strip().lower()
            if not word or len(word) < 3:
                continue
            if re.search(r"\b" + re.escape(word) + r"\b", lower):
                if word == "system" and "the system" in lower:
                    continue
                entry = f'"{word}" -> use {r["use_instead"] or "(none)"} ({r["meaning"]})'
                (watch if word in COMMON else strict).append(entry)
    return strict, watch


def decision_sections(path):
    if not Path(path).exists():
        return []
    text = Path(path).read_text(encoding="utf-8")
    parts = re.split(r"(?m)^## ", text)[1:]
    out = []
    for p in parts:
        title = p.splitlines()[0]
        out.append((title, tokens(p)))
    return out


def cmd_search(root, text, top):
    q = tokens(text)
    reqs = read_rows(root / PATHS["req"])
    acs = read_rows(root / PATHS["ac"])
    print(f"Searching for: {text}")
    print(f"Meaningful words: {', '.join(sorted(q)) or '(none)'}\n")

    scored = sorted(((similarity(q, tokens(r["name"] + " " + r["statement"])), r) for r in reqs),
                    key=lambda x: -x[0])
    close = [(s, r) for s, r in scored if s >= 0.30][:top] or [(s, r) for s, r in scored[:3] if s >= 0.15]
    print("EXISTING REQUIREMENTS")
    if not close:
        print("  none close. This looks new.")
    for s, r in close:
        flag = "likely the same" if s >= 0.6 else "overlaps"
        print(f"  {r['id']}  score {s:.2f} ({flag})  [{r['kind']}, release {r['release'] or 'none'}, "
              f"{r['today']}, {r['status']}]")
        print(f"      {r['statement']}")
        if r["notes"]:
            print(f"      notes: {r['notes']}")
        linked = [a for a in acs if r["id"] in [x.strip() for x in a["requirements"].split(";")]]
        print(f"      acceptance criteria: {len(linked)}"
              + (" (none: it cannot be confirmed yet)" if not linked else ""))
        for a in linked:
            print(f"        {a['id']} [{a['test_level']}] given {a['given']}; when {a['when']}; then {a['then']}")
    print()

    sa = sorted(((similarity(q, tokens(a["given"] + " " + a["when"] + " " + a["then"])), a) for a in acs),
                key=lambda x: -x[0])
    sa = [(s, a) for s, a in sa if s >= 0.35][:top]
    shown = {a["id"] for _, r in close for a in acs if r["id"] in [x.strip() for x in a["requirements"].split(";")]}
    sa = [(s, a) for s, a in sa if a["id"] not in shown]
    if sa:
        print("OTHER ACCEPTANCE CRITERIA THAT READ SIMILARLY")
        for s, a in sa:
            print(f"  {a['id']} (proves {a['requirements']}) score {s:.2f}: given {a['given']}; "
                  f"when {a['when']}; then {a['then']}")
        print()

    rules = read_rows(root / PATHS["rules"])
    rs = sorted(((similarity(q, tokens(r["statement"])), r) for r in rules), key=lambda x: -x[0])
    rs = [(s, r) for s, r in rs if s >= 0.30][:3]
    if rs:
        print("RULES THAT ALWAYS HOLD (rule inventory)")
        for s, r in rs:
            note = f"written as {r['rule_file']}" if r["rule_file"] else "not written as a RULE file yet"
            print(f"  {r['ref']} [{r['status']}] {r['statement']}  ({note})")
        print()

    perms = read_rows(root / PATHS["perm"])
    ps = sorted(((similarity(q, tokens(p["permission"])), p) for p in perms), key=lambda x: -x[0])
    ps = [(s, p) for s, p in ps if s >= 0.30][:2]
    if ps:
        print("PERMISSIONS THAT TOUCH IT")
        for s, p in ps:
            print(f"  {p['permission']}: administrator {p['administrator']}, auditor {p['auditor']}, "
                  f"project manager {p['project_manager']}, engineer {p['engineer']}  "
                  f"(requirements: {p['requirements'] or 'none'})")
        print()

    ds = sorted(((len(q & toks) / len(q) if q else 0.0, title) for title, toks in
                 decision_sections(root / PATHS["decisions"])), key=lambda x: -x[0])
    ds = [(s, t) for s, t in ds if s >= 0.40][:3]
    if ds:
        print("DECISIONS THAT MENTION THESE WORDS (read them before you go on)")
        for s, t in ds:
            print(f"  {t}  ({s:.0%} of your words appear)")
        print()

    strict, watch = retired_words(text, read_rows(root / PATHS["vocab"]))
    print("WORDING")
    for n in shape_notes(text):
        print(f"  shape: {n}")
    for e in strict:
        print(f"  retired word: {e}")
    for e in watch:
        print(f"  watch in context: {e}")
    if not (shape_notes(text) or strict or watch):
        print("  no problems found")


# ----------------------------------------------------------------------------- ids

def max_number(rows, prefix):
    nums = [int(m.group(1)) for r in rows if (m := re.fullmatch(prefix + r"-(\d+)", r["id"]))]
    return max(nums) if nums else 0


def next_ids(reqs, acs):
    return {"FR": max_number(reqs, "FR") + 1, "NFR": max_number(reqs, "NFR") + 1,
            "AC": max_number(acs, "AC") + 1}


def cmd_next_ids(root):
    n = next_ids(read_rows(root / PATHS["req"]), read_rows(root / PATHS["ac"]))
    print(f"next functional:     FR-{n['FR']}")
    print(f"next non-functional: NFR-{n['NFR']}  (quality, constraint or process)")
    print(f"next criterion:      AC-{n['AC']}")


# ----------------------------------------------------------------------------- validate

def problems_in(reqs, acs):
    p = []
    seen = set()
    for r in reqs:
        i = r["id"]
        if i in seen:
            p.append(f"{i}: duplicate id")
        seen.add(i)
        if not re.fullmatch(r"(FR|NFR)-\d+", i):
            p.append(f"{i}: id is not FR-<n> or NFR-<n>")
        if r["kind"] not in KINDS:
            p.append(f"{i}: kind '{r['kind']}' is not one of {sorted(KINDS)}")
        elif (r["kind"] == "functional") != i.startswith("FR-"):
            p.append(f"{i}: a functional requirement is FR-, the other kinds are NFR-")
        want_group = "process" if r["kind"] == "process" else "product"
        if r["group"] != want_group:
            p.append(f"{i}: group should be '{want_group}'")
        if not (r["statement"].startswith("The system shall") or r["statement"].startswith("The team shall")):
            p.append(f"{i}: statement does not start with 'The system shall' or 'The team shall'")
        if r["kind"] == "quality":
            missing = [k for k in SCENARIO if not r[k]]
            if missing:
                p.append(f"{i}: quality requirement is missing {missing}")
        if r["verification"] not in VERIFICATION:
            p.append(f"{i}: verification '{r['verification']}' is not one of {sorted(VERIFICATION)}")
        if r["release"] not in RELEASES:
            p.append(f"{i}: release '{r['release']}' is not one of {sorted(RELEASES - {''})} or empty")
        if r["today"] not in TODAY:
            p.append(f"{i}: today '{r['today']}' is not 'built' or 'not built'")
        if r["status"] not in STATUS:
            p.append(f"{i}: status '{r['status']}' is not one of {sorted(STATUS)}")
    ids = {r["id"] for r in reqs}
    seen_ac = set()
    for a in acs:
        i = a["id"]
        if i in seen_ac:
            p.append(f"{i}: duplicate id")
        seen_ac.add(i)
        if not re.fullmatch(r"AC-\d+", i):
            p.append(f"{i}: id is not AC-<n>")
        refs = [x.strip() for x in a["requirements"].split(";") if x.strip()]
        if not refs:
            p.append(f"{i}: proves no requirement")
        for ref in refs:
            if ref not in ids:
                p.append(f"{i}: proves {ref}, which does not exist")
        if not (a["given"] and a["when"] and a["then"]):
            p.append(f"{i}: needs given, when and then")
        if a["test_level"] not in AC_LEVELS:
            p.append(f"{i}: test_level '{a['test_level']}' is not one of {sorted(AC_LEVELS)}")
        if a["status"] not in AC_STATUS:
            p.append(f"{i}: status '{a['status']}' is not one of {sorted(AC_STATUS)}")
    return p


def warnings_in(reqs, acs):
    covered = set()
    for a in acs:
        covered |= {x.strip() for x in a["requirements"].split(";") if x.strip()}
    out = []
    for r in reqs:
        if r["release"] == "R1" and r["status"] != "retired" and r["id"] not in covered:
            out.append(f"{r['id']}: a Release 1 requirement with no acceptance criteria")
        if r["kind"] == "quality" and r["measure"] == "not decided":
            out.append(f"{r['id']}: quality requirement whose measure is not decided")
    return out


def cmd_validate(root):
    reqs, acs = read_rows(root / PATHS["req"]), read_rows(root / PATHS["ac"])
    p = problems_in(reqs, acs)
    w = warnings_in(reqs, acs)
    for x in p:
        print("PROBLEM  " + x)
    for x in w:
        print("note     " + x)
    print(f"{len(reqs)} requirements, {len(acs)} acceptance criteria: "
          f"{len(p)} problem(s), {len(w)} note(s)")
    return 1 if p else 0


# ----------------------------------------------------------------------------- edit

def read_json():
    text = sys.stdin.read().strip()
    if not text:
        raise SystemExit("Give the row as JSON on stdin.")
    return json.loads(text)


def cmd_append(root, what, dry):
    data = read_json()
    items = data if isinstance(data, list) else [data]
    reqs, acs = read_rows(root / PATHS["req"]), read_rows(root / PATHS["ac"])
    ids = next_ids(reqs, acs)
    added = []
    for it in items:
        if what == "requirements":
            row = {c: "" for c in REQ_COLS}
            row.update({k: str(v) for k, v in it.items() if k in REQ_COLS and k != "id"})
            kind = row["kind"]
            if kind not in KINDS:
                raise SystemExit(f"kind must be one of {sorted(KINDS)}")
            prefix = "FR" if kind == "functional" else "NFR"
            row["id"] = f"{prefix}-{ids[prefix]}"
            ids[prefix] += 1
            row["group"] = "process" if kind == "process" else "product"
            row["today"] = row["today"] or "not built"
            row["status"] = row["status"] or "draft"
            reqs.append(row)
        else:
            row = {c: "" for c in AC_COLS}
            rq = it.get("requirements", "")
            if isinstance(rq, list):
                rq = "; ".join(rq)
            row.update({k: str(v) for k, v in it.items() if k in AC_COLS and k != "id"})
            row["requirements"] = rq
            row["id"] = f"AC-{ids['AC']}"
            ids["AC"] += 1
            row["status"] = row["status"] or "draft"
            acs.append(row)
        added.append(row)
    p = problems_in(reqs, acs)
    if p:
        for x in p:
            print("REFUSED  " + x)
        return 1
    for row in added:
        print(f"{'would add' if dry else 'added'} {row['id']}: "
              f"{row.get('statement') or row.get('given', '')}")
    if not dry:
        if what == "requirements":
            write_rows(root / PATHS["req"], REQ_COLS, reqs)
        else:
            write_rows(root / PATHS["ac"], AC_COLS, acs)
    return 0


def cmd_update(root, rid, dry):
    changes = read_json()
    if "id" in changes:
        raise SystemExit("An id never changes. Retire the row and add a new one instead.")
    reqs, acs = read_rows(root / PATHS["req"]), read_rows(root / PATHS["ac"])
    for rows, cols in ((reqs, REQ_COLS), (acs, AC_COLS)):
        for r in rows:
            if r["id"] == rid:
                before = dict(r)
                for k, v in changes.items():
                    if k not in cols:
                        raise SystemExit(f"'{k}' is not a column of {rid}")
                    r[k] = "; ".join(v) if isinstance(v, list) else str(v)
                if "kind" in changes and rows is reqs:
                    r["group"] = "process" if r["kind"] == "process" else "product"
                p = problems_in(reqs, acs)
                if p:
                    for x in p:
                        print("REFUSED  " + x)
                    return 1
                for k in changes:
                    print(f"{'would change' if dry else 'changed'} {rid}.{k}: {before[k]!r} -> {r[k]!r}")
                if not dry:
                    write_rows(root / PATHS["req"], REQ_COLS, reqs)
                    write_rows(root / PATHS["ac"], AC_COLS, acs)
                return 0
    print(f"No row with id {rid}.")
    return 1


# ----------------------------------------------------------------------------- main

def cmd_init(root):
    made = []
    for key, cols in (("req", REQ_COLS), ("ac", AC_COLS)):
        path = root / PATHS[key]
        if not path.exists():
            write_rows(path, cols, [])
            made.append(PATHS[key])
    print("Created " + ", ".join(made) if made else "Nothing to do: both files already exist.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="the repo root (default: found from the current folder)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("text")
    s.add_argument("--top", type=int, default=4)
    sub.add_parser("init")
    sub.add_parser("next-ids")
    sub.add_parser("validate")
    a = sub.add_parser("append")
    a.add_argument("what", choices=["requirements", "acceptance"])
    a.add_argument("--dry-run", action="store_true")
    u = sub.add_parser("update")
    u.add_argument("id")
    u.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve() if args.root else find_root()
    use_config(root)
    if args.cmd == "init":
        return cmd_init(root)
    if args.cmd == "search":
        cmd_search(root, args.text, args.top)
        return 0
    if args.cmd == "next-ids":
        cmd_next_ids(root)
        return 0
    if args.cmd == "validate":
        return cmd_validate(root)
    if args.cmd == "append":
        return cmd_append(root, args.what, args.dry_run)
    return cmd_update(root, args.id, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
