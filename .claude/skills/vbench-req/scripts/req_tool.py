#!/usr/bin/env python3
"""Search, check and edit a project's requirements and acceptance criteria.

The requirements are tables in docs/requirements/requirements.md, and their acceptance criteria are a
table in docs/requirements/acceptance-criteria.md (markdown, so a person can read them). This script
reads them (and the permissions, rule inventory, vocabulary and decisions log beside them, which are
CSV) so a check for "is this already here?" does not depend on memory, and it edits the two files safely.

Where the files live comes from vbench.json (see _vbench/config.py); with none, the paths above.

Commands (run from the repo root, or pass --root):

  search "text"           find existing requirements, criteria, rules, permissions and decisions that
                          overlap with the text, and check its shape and wording
  init                    create the empty requirements and acceptance criteria files (a fresh repo)
  convert                 turn requirements.csv and acceptance-criteria.csv into the markdown files
                          (once, when a repo moves from CSV; the CSV files are left in place)
  next-ids                show the next free FR-, NFR- and AC- numbers
  validate                check both files (unique ids, "shall" wording, complete scenarios, links)
  append requirements     add rows from JSON on stdin (an object or a list), with new ids
  append acceptance       add acceptance criteria from JSON on stdin
  update ID               change fields of one row, from a JSON object on stdin
  duplicates              read only: list likely duplicate requirements, criteria and use cases
                          (--threshold N, --kind requirements|acceptance|usecases); always exits 0
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
import mdtables  # noqa: E402

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
    """The rows of a file. A .md file is the requirements or the criteria as markdown tables, anything
    else is a CSV (permissions, vocabulary, the rule inventory, retired ids)."""
    if not Path(path).exists():
        return []
    if str(path).endswith(".md"):
        return mdtables.read_md(Path(path).read_text(encoding="utf-8"))
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def line_ending(path):
    """Keep the file's own line ending, so an edit does not rewrite every line."""
    if Path(path).exists() and b"\r\n" in Path(path).read_bytes():
        return "\r\n"
    return "\n"


def write_rows(path, cols, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if str(path).endswith(".md"):
        if cols == REQ_COLS:
            text = mdtables.requirements_md(rows)
        elif cols == AC_COLS:
            text = mdtables.criteria_md(rows)
        else:
            raise SystemExit("A markdown file holds the requirements or the acceptance criteria only.")
        Path(path).write_bytes(text.replace("\n", line_ending(path)).encode("utf-8"))
        return
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

def cmd_convert(root):
    """One time: requirements.csv and acceptance-criteria.csv become the markdown tables."""
    done = []
    for key, cols in (("req", REQ_COLS), ("ac", AC_COLS)):
        md = root / PATHS[key]
        old = md.with_suffix(".csv")
        if md.exists():
            print(f"skipped {PATHS[key]}: it already exists")
            continue
        if not old.exists():
            print(f"skipped {PATHS[key]}: no {old.name} to convert")
            continue
        with open(old, newline="", encoding="utf-8") as f:
            rows = [{c: (r.get(c) or "") for c in cols} for r in csv.DictReader(f)]
        write_rows(md, cols, rows)
        done.append(f"{old.name} -> {md.name} ({len(rows)} rows)")
    print("Converted " + "; ".join(done) + ". The CSV files are still there: delete them when you are happy." if done
          else "Nothing converted.")
    return 0


def cmd_init(root):
    made = []
    for key, cols in (("req", REQ_COLS), ("ac", AC_COLS)):
        path = root / PATHS[key]
        if not path.exists():
            write_rows(path, cols, [])
            made.append(PATHS[key])
    print("Created " + ", ".join(made) if made else "Nothing to do: both files already exist.")
    return 0


# ----------------------------------------------------------------------------- duplicates

DUP_DEFAULTS = {"requirements": 0.55, "acceptance": 0.65, "usecases": 0.5}
SAME_THEN = 0.8
MIN_THEN_WORDS = 3   # "then it is refused" is too generic to say two criteria are the same behaviour


def parse_use_case(text):
    """id, name, criteria, satisfies and the first paragraph of the description of a use case file,
    or None when the file has no yaml block with an id."""
    m = re.search(r"```yaml\n(.*?)```", text, re.S)
    if not m:
        return None
    uc = {"id": "", "name": "", "criteria": [], "satisfies": []}
    key = None
    for line in m.group(1).splitlines():
        top = re.match(r"([A-Za-z_]+):\s*(.*)$", line)
        if top:
            key = top.group(1)
            if key in ("id", "name"):
                uc[key] = top.group(2).strip()
            continue
        item = re.match(r"\s+-\s+id:\s*(\S+)", line)
        if item and key in ("criteria", "satisfies"):
            uc[key].append(item.group(1))
    if not uc["id"]:
        return None
    d = re.search(r"^## Description\s*\n+(.*?)(?:\n\s*\n|\n## |\Z)", text, re.S | re.M)
    uc["description"] = " ".join(d.group(1).split()) if d else ""
    return uc


def read_use_cases(root):
    out = []
    for f in sorted((root / PATHS["usecases"]).glob("UC-*.md")):
        try:
            uc = parse_use_case(f.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            uc = None
        if uc:
            out.append(uc)
    return out


def scored_pairs(items, text_of, threshold):
    pairs = []
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            score = similarity(tokens(text_of(a)), tokens(text_of(b)))
            if score >= threshold:
                pairs.append((score, a, b))
    return sorted(pairs, key=lambda p: (-p[0], p[1]["id"], p[2]["id"]))


def show_pair(a, b, score, ta, tb, note=""):
    print("  %s  %s  %.2f%s" % (a, b, score, note))
    print("    %s: %s" % (a, ta))
    print("    %s: %s" % (b, tb))


def cut(text, n=160):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n - 3] + "..."


def dup_requirements(root, threshold):
    rows = [r for r in read_rows(root / PATHS["req"]) if r.get("status") != "retired"]
    pairs = scored_pairs(rows, lambda r: r.get("name", "") + " " + r.get("statement", ""), threshold)
    print("REQUIREMENTS: likely duplicates (name and statement, similarity >= %.2f, retired skipped): %d" % (threshold, len(pairs)))
    for score, a, b in pairs:
        show_pair(a["id"], b["id"], score, cut(a.get("statement")), cut(b.get("statement")))
    print()


def dup_acceptance(root, threshold):
    rows = [r for r in read_rows(root / PATHS["ac"]) if r.get("status") != "retired"]
    pairs = scored_pairs(rows, lambda r: " ".join(r.get(k, "") for k in ("given", "when", "then")), threshold)
    print("ACCEPTANCE CRITERIA: likely duplicates (given, when, then, similarity >= %.2f, retired skipped): %d" % (threshold, len(pairs)))
    for score, a, b in pairs:
        show_pair(a["id"], b["id"], score, cut("Given %s, when %s, then %s" % (a["given"], a["when"], a["then"])),
                  cut("Given %s, when %s, then %s" % (b["given"], b["when"], b["then"])))
    same = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            ta, tb = tokens(a.get("then", "")), tokens(b.get("then", ""))
            if min(len(ta), len(tb)) < MIN_THEN_WORDS:
                continue
            score = similarity(ta, tb)
            ra, rb = set(split_ids(a.get("requirements", ""))), set(split_ids(b.get("requirements", "")))
            if score >= SAME_THEN and ra != rb:
                same.append((score, a, b))
    same.sort(key=lambda p: (-p[0], p[1]["id"], p[2]["id"]))
    print()
    print("ACCEPTANCE CRITERIA: same behaviour, different requirement (then-clauses similarity >= %.2f, at least %d words): %d" % (SAME_THEN, MIN_THEN_WORDS, len(same)))
    for score, a, b in same:
        show_pair(a["id"], b["id"], score, cut("[%s] then %s" % (a["requirements"], a["then"])),
                  cut("[%s] then %s" % (b["requirements"], b["then"])))
    print()


def split_ids(text):
    return [x for x in re.split(r"[\s,;]+", text or "") if x]


def dup_usecases(root, threshold):
    ucs = read_use_cases(root)
    pairs = scored_pairs(ucs, lambda u: u["name"] + " " + u["description"], threshold)
    print("USE CASES: likely duplicates (name and description, similarity >= %.2f): %d" % (threshold, len(pairs)))
    for score, a, b in pairs:
        show_pair(a["id"], b["id"], score, cut("%s. %s" % (a["name"], a["description"])),
                  cut("%s. %s" % (b["name"], b["description"])))
    print()
    shared = []
    for i, a in enumerate(ucs):
        for b in ucs[i + 1:]:
            common = sorted(set(a["criteria"]) & set(b["criteria"]))
            smaller = min(len(set(a["criteria"])), len(set(b["criteria"])))
            if common and smaller and len(common) * 2 >= smaller:
                shared.append((len(common) / smaller, a, b, common))
    shared.sort(key=lambda p: (-p[0], p[1]["id"], p[2]["id"]))
    print("USE CASES: sharing at least half of the smaller one's criteria: %d" % len(shared))
    for score, a, b, common in shared:
        show_pair(a["id"], b["id"], score, "%s (%d criteria) shares: %s" % (a["name"], len(a["criteria"]), ", ".join(common)),
                  "%s (%d criteria)" % (b["name"], len(b["criteria"])))
    print()
    owners = {}
    for u in ucs:
        for c in dict.fromkeys(u["criteria"]):
            owners.setdefault(c, []).append(u["id"])
    multi = {c: o for c, o in owners.items() if len(o) > 1}
    print("USE CASES: criteria listed by more than one use case (a criterion should normally belong to one): %d" % len(multi))
    for c in sorted(multi, key=lambda x: [int(n) if n.isdigit() else n for n in re.split(r"(\d+)", x)]):
        print("  %s  listed by %s" % (c, ", ".join(multi[c])))
    print()


def cmd_duplicates(root, threshold, kind):
    kinds = [kind] if kind else ["requirements", "acceptance", "usecases"]
    for k in kinds:
        th = threshold if threshold is not None else DUP_DEFAULTS[k]
        {"requirements": dup_requirements, "acceptance": dup_acceptance, "usecases": dup_usecases}[k](root, th)
    print("This is a prompt for a person, not a verdict: the tool never edits, retires or merges anything.")
    print("Safe options for each pair: retire one with status retired, merge keeping one id, move it to")
    print("another level (a criterion to a unit or integration test, a use case into another), or defer with an R2 note.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="the repo root (default: found from the current folder)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("text")
    s.add_argument("--top", type=int, default=4)
    sub.add_parser("init")
    sub.add_parser("convert")
    sub.add_parser("next-ids")
    sub.add_parser("validate")
    a = sub.add_parser("append")
    a.add_argument("what", choices=["requirements", "acceptance"])
    a.add_argument("--dry-run", action="store_true")
    u = sub.add_parser("update")
    u.add_argument("id")
    u.add_argument("--dry-run", action="store_true")
    d = sub.add_parser("duplicates")
    d.add_argument("--threshold", type=float, help="override the similarity threshold")
    d.add_argument("--kind", choices=["requirements", "acceptance", "usecases"])
    args = ap.parse_args(argv)
    root = Path(args.root).resolve() if args.root else find_root()
    use_config(root)
    if args.cmd == "duplicates":
        return cmd_duplicates(root, args.threshold, args.kind)
    if args.cmd == "init":
        return cmd_init(root)
    if args.cmd == "convert":
        return cmd_convert(root)
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
