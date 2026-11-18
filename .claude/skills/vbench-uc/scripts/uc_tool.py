#!/usr/bin/env python3
"""Search, check and write use cases, linked to requirements and acceptance criteria.

A use case is a Markdown file in the use case folder (default docs/usecases/) named <ID>-<slug>.md. Its data is a fenced yaml block
at the top (see _vbench/conventions.md). It points up at the requirements it serves and the
acceptance criteria it runs, and each pointer carries a short hash of that row as it was when a person
last reviewed it. If the row changes, the hash no longer matches and the use case is SUSPECT.

Commands (run from the repo root, or pass --root):

  search "text"          use cases that read like the text, and the requirements behind the text
  impact ID [ID ...]     for requirement ids (FR-/NFR-) or use case ids (UC-): what is linked, what is
                         suspect, what has no use case. Every line is a recorded link, never a guess.
  coverage               requirements with no use case, grouped by release
  next-id AREA           the next free number in an area letter, for example E gives UC-E3. Retired ids
                         (docs/usecases/retired-ids.csv) are skipped and never reused. `create` also takes an
                         explicit "id" when it is free.
  validate               check every use case file
  create                 write a new use case file from JSON on stdin (--dry-run to preview)
  check-upstream UC-ID   read its flow against its requirements and criteria, and list what vbench-req
                         should propose (nothing is changed)
  diagram CONTEXT        the use case diagram (PlantUML) of one context, drawn from the files (--write to save);
                         `diagram overview` assembles the composite from the context files
  freeze UC-ID           record a hash of each analysis revision, so an edit to a frozen one is caught
  trace UC-ID            from each analysis element to what became of it in the design (nothing may be lost)
  sync UC-ID             refresh the copied text of its requirements and criteria from the requirements files
  stamp UC-ID            record that a person has reviewed it against the current rows (also syncs)

Uses only the standard library. Exit code 1 means a problem was found or a write was refused.
"""

import argparse
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "vbench-req" / "scripts"))
import req_tool as rq  # noqa: E402  (the requirements helper, reused for reading rows and matching)

# Settings come from vbench.json (see _vbench/config.py); use_config(root) fills these in for a repo.
# Empty AREAS, ACTORS and PROVIDERS mean "no restriction": any capital letter, actor or provider is accepted.
AREAS = {}
ACTORS = set()
PROVIDERS = set()
STATUS = {"draft", "accepted", "retired"}
PREFIX = "UC"
SYSTEM_NAME = "the system"
UC_DIR = rq.config.DEFAULTS["paths"]["usecases"]
RETIRED = rq.config.DEFAULTS["paths"]["retired"]
ONTOLOGY_DIR = rq.config.DEFAULTS["paths"]["ontology"]


def use_config(root):
    """Load the repo's settings into this module. Every command calls this once it knows the root."""
    global AREAS, ACTORS, PROVIDERS, PREFIX, SYSTEM_NAME, UC_DIR, RETIRED, ONTOLOGY_DIR
    cfg = rq.use_config(root)
    AREAS, ACTORS, PROVIDERS = dict(cfg["areas"]), set(cfg["actors"]), set(cfg["providers"])
    PREFIX = cfg["id_prefix"]
    SYSTEM_NAME = cfg["system_name"] or Path(root).name
    d = cfg["diagram"]
    for target, key in ((ACTOR_STYLE, "actor_style"), (ACTOR_COLOUR, "actor_colour"), (CONTEXT_COLOUR, "context_colour")):
        target.clear()
        target.update(d[key])
    IS_A[:] = [tuple(x) for x in d["actor_is_a"]]
    UC_DIR, RETIRED, ONTOLOGY_DIR = cfg["paths"]["usecases"], cfg["paths"]["retired"], cfg["paths"]["ontology"]
    return cfg


def area_letter(uid):
    return uid[len(PREFIX) + 1]


def id_re(area="[A-Z]"):
    return re.compile(rf"{re.escape(PREFIX)}-{area}\d+")


REQ_HASH_FIELDS = ["kind", "statement", "quality", "stimulus", "environment", "response", "measure"]
AC_HASH_FIELDS = ["given", "when", "then", "test_level"]
SECTIONS = [("description", "Description", "text"), ("preconditions", "Preconditions", "list"),
            ("main_flow", "Main flow", "numbered"), ("other_flows", "Other flows", "list"),
            ("postconditions", "Postconditions", "list"), ("slices", "Slices", "list"),
            ("not_in_this", "Not in this use case", "list")]


# ----------------------------------------------------------------------------- hashes

def row_hash(row, fields):
    """A short fingerprint of the parts of a row that change its meaning. Notes do not count."""
    return hashlib.sha1("\x1f".join(row.get(f, "") for f in fields).encode("utf-8")).hexdigest()[:7]


def req_hash(row):
    return row_hash(row, REQ_HASH_FIELDS)


def ac_hash(row):
    return row_hash(row, AC_HASH_FIELDS)


# ----------------------------------------------------------------------------- the header

def scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_header(text):
    """Read the first fenced yaml block. Supports the shapes the use case header uses:
    key: value, key: [a, b], a block list of values, and a block list of {id, reviewed} maps."""
    m = re.match(r"\s*```yaml\n(.*?)\n```", text, re.S)
    if not m:
        raise ValueError("no yaml block at the top of the file")
    data, key = {}, None
    for raw in m.group(1).splitlines():
        line = re.sub(r"\s+#.*$", "", raw).rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and not line.startswith("-"):
            k, _, v = line.partition(":")
            key = k.strip()
            v = v.strip()
            if v == "":
                data[key] = []
            elif v.startswith("[") and v.endswith("]"):
                data[key] = [scalar(x) for x in v[1:-1].split(",") if x.strip()]
            else:
                data[key] = scalar(v)
        elif line.strip().startswith("- "):
            item = line.strip()[2:]
            if key in ("satisfies", "criteria") and re.match(r"[A-Za-z_]+:\s", item + " "):
                k, _, v = item.partition(":")
                data[key].append({k.strip(): scalar(v)})
            else:
                data[key].append(scalar(item))
        else:  # continuation of a map item: "    reviewed: abc"
            k, _, v = line.strip().partition(":")
            data[key][-1][k.strip()] = scalar(v)
    return data


def ids_of(items):
    return [i["id"] if isinstance(i, dict) else i for i in items or []]


def load_ucs(root):
    out = []
    folder = root / UC_DIR
    if not folder.is_dir():
        return out
    for p in sorted(folder.glob(f"{PREFIX}-*.md")):
        text = p.read_text(encoding="utf-8")
        try:
            out.append((p, parse_header(text), text))
        except ValueError as e:
            out.append((p, {"_error": str(e)}, text))
    return out


def ontology_files(root):
    folder = root / ONTOLOGY_DIR
    names = {}
    if folder.is_dir():
        for p in folder.glob("*.md"):
            m = re.match(r"((?:OBJ|RULE|SET)-[A-Z]?\d+)-", p.name)
            if m:
                names[m.group(1)] = p
    return names


def object_context(root, oid):
    p = ontology_files(root).get(oid)
    if p:
        m = re.search(r"^context:\s*(\S+)", p.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    return None


# ----------------------------------------------------------------------------- shared lookups

def load(root):
    reqs = rq.read_rows(root / rq.PATHS["req"])
    acs = rq.read_rows(root / rq.PATHS["ac"])
    return reqs, acs, load_ucs(root)


def suspects(header, reqs_by_id, acs_by_id):
    """Pointers whose recorded hash no longer matches the row. Each is a recorded fact."""
    out = []
    for item in header.get("satisfies", []):
        r = reqs_by_id.get(item["id"])
        if r and item.get("reviewed") != req_hash(r):
            out.append(f"{item['id']} changed since review (recorded {item.get('reviewed') or 'none'}, now {req_hash(r)})")
    for item in header.get("criteria", []):
        a = acs_by_id.get(item["id"])
        if a and item.get("reviewed") != ac_hash(a):
            out.append(f"{item['id']} changed since review (recorded {item.get('reviewed') or 'none'}, now {ac_hash(a)})")
    return out


# ----------------------------------------------------------------------------- search

def cmd_search(root, text, top):
    reqs, acs, ucs = load(root)
    q = rq.tokens(text)
    print(f"Searching for: {text}\nMeaningful words: {', '.join(sorted(q)) or '(none)'}\n")

    print("REQUIREMENTS THE TEXT READS LIKE (by wording)")
    scored = sorted(((rq.similarity(q, rq.tokens(r["name"] + " " + r["statement"])), r) for r in reqs),
                    key=lambda x: -x[0])
    near = [(s, r) for s, r in scored if s >= 0.30][:top]
    if not near:
        print("  none close. Run vbench-req first: the requirement may not exist yet.")
    for s, r in near:
        holders = [p.name.split("-", 2)[0] + "-" + p.name.split("-", 2)[1] for p, h, _ in ucs
                   if r["id"] in ids_of(h.get("satisfies"))]
        print(f"  {r['id']} score {s:.2f} [{r['release'] or 'no release'}, {r['status']}]: {r['statement']}")
        print(f"      use cases: {', '.join(holders) if holders else 'none'}")
    print()

    print("EXISTING USE CASES THAT READ LIKE IT (by wording)")
    found = False
    for p, h, body in sorted(ucs, key=lambda x: -rq.similarity(q, rq.tokens(x[2]))):
        s = rq.similarity(q, rq.tokens(h.get("name", "") + " " + body))
        if s < 0.20:
            continue
        found = True
        print(f"  {h.get('id', p.name)} score {s:.2f} [{h.get('status', '?')}]: {h.get('name', '')}")
        print(f"      serves: {', '.join(ids_of(h.get('satisfies'))) or 'nothing'}")
    if not found:
        print("  none." + ("" if ucs else " There are no use case files yet."))
    print()
    strict, watch = rq.retired_words(text, rq.read_rows(root / rq.PATHS["vocab"]))
    print("WORDING")
    for e in strict:
        print(f"  retired word: {e}")
    for e in watch:
        print(f"  watch in context: {e}")
    if not (strict or watch):
        print("  no problems found")


# ----------------------------------------------------------------------------- impact

def cmd_impact(root, ids):
    reqs, acs, ucs = load(root)
    reqs_by_id, acs_by_id = {r["id"]: r for r in reqs}, {a["id"]: a for a in acs}
    files = ontology_files(root)
    ucs_by_id = {h.get("id"): (p, h) for p, h, _ in ucs if "_error" not in h}
    code = 0
    for i in ids:
        print(f"== {i}")
        if i.startswith(f"{PREFIX}-"):
            if i not in ucs_by_id:
                print("  no such use case file")
                code = 1
                continue
            p, h = ucs_by_id[i]
            print(f"  {h.get('name')}  [{h.get('status')}], actor {h.get('actor')}, {h.get('context')}")
            for rid in ids_of(h.get("satisfies")):
                r = reqs_by_id.get(rid)
                print(f"  serves {rid}: {r['statement'] if r else 'MISSING from requirements.md'}")
            for aid in ids_of(h.get("criteria")):
                print(f"  runs {aid}: {'present' if aid in acs_by_id else 'MISSING from acceptance-criteria.md'}")
            for s in suspects(h, reqs_by_id, acs_by_id):
                print(f"  SUSPECT: {s}")
            if h.get("flow_reviewed") and h["flow_reviewed"] != flow_hash(p.read_text(encoding="utf-8")):
                print("  FLOW CHANGED since the last stamp: run check-upstream")
            continue
        r = reqs_by_id.get(i)
        if not r:
            print("  no such requirement")
            code = 1
            continue
        print(f"  {r['statement']}  [{r['kind']}, release {r['release'] or 'none'}, {r['today']}, {r['status']}]")
        mine = [a for a in acs if i in [x.strip() for x in a["requirements"].split(";")]]
        print(f"  acceptance criteria: {', '.join(a['id'] for a in mine) or 'NONE (cannot be confirmed yet)'}")
        holders = [(p, h) for p, h, _ in ucs if "_error" not in h and i in ids_of(h.get("satisfies"))]
        if not holders:
            print("  use cases: NONE. Build a new use case, or attach this to an existing one.")
        for p, h in holders:
            sus = suspects(h, reqs_by_id, acs_by_id)
            print(f"  use case {h['id']} {h.get('name')}: {'SUSPECT, review it' if sus else 'up to date'}")
            for s in sus:
                print(f"      {s}")
            missing = [a["id"] for a in mine if a["id"] not in ids_of(h.get("criteria"))]
            if missing:
                print(f"      does not yet list criteria {', '.join(missing)}")
        objs = [x.strip() for x in r["objects"].split(";") if x.strip()]
        rules = [x.strip() for x in r["rules"].split(";") if x.strip()]
        for o in objs + rules:
            where = "file exists" if o in files else "no file yet (planned)"
            ctx = object_context(root, o) if o.startswith("OBJ-") else None
            print(f"  uses {o}: {where}{', ' + ctx if ctx else ''}")
        if not (objs or rules):
            print("  uses no object or rule (none recorded in the row)")
        shared = [x["id"] for x in reqs if x["id"] != i and
                  set(objs + rules) & {y.strip() for y in (x["objects"] + ";" + x["rules"]).split(";") if y.strip()}]
        if shared:
            print(f"  shares an object or rule with: {', '.join(shared[:12])}{' ...' if len(shared) > 12 else ''}")
    return code


def cmd_coverage(root):
    reqs, acs, ucs = load(root)
    served = set()
    for _, h, _ in ucs:
        served |= set(ids_of(h.get("satisfies")))
    groups = {}
    for r in reqs:
        if r["kind"] == "functional" and r["status"] != "retired" and r["id"] not in served:
            groups.setdefault(r["release"] or "none", []).append(r["id"])
    total = sum(len(v) for v in groups.values())
    print(f"{len(ucs)} use case file(s). Functional requirements with no use case: {total}")
    for rel in ["R1", "R2", "R3", "backlog", "parked", "none"]:
        if rel in groups:
            ids = groups[rel]
            print(f"  {rel} ({len(ids)}): {', '.join(ids[:20])}{' ...' if len(ids) > 20 else ''}")


# ----------------------------------------------------------------------------- ids and validate

def load_retired(root):
    """Ids that were issued or reserved and then retired. They are never handed out again."""
    return {r["id"]: r.get("reason", "") for r in rq.read_rows(root / RETIRED)}


def next_number(root, area, ucs):
    pat = rf"{re.escape(PREFIX)}-{area}(\d+)"
    used = [int(m.group(1)) for _, h, _ in ucs if (m := re.fullmatch(pat, h.get("id", "")))]
    used += [int(m.group(1)) for i in load_retired(root) if (m := re.fullmatch(pat, i))]
    return max(used, default=0) + 1


def cmd_next_id(root, area):
    area = area.upper()
    if not re.fullmatch(r"[A-Z]", area) or (AREAS and area not in AREAS):
        print(f"Area {area} is not one of {', '.join(sorted(AREAS))}" if AREAS else
              f"Area {area} must be one capital letter, for example {PREFIX}-P1 is area P")
        return 1
    print(f"{PREFIX}-{area}{next_number(root, area, load_ucs(root))}")
    return 0


def problems_in(root, ucs, reqs, acs):
    reqs_by_id, acs_by_id = {r["id"] for r in reqs}, {a["id"] for a in acs}
    files = ontology_files(root)
    p, seen = [], set()
    for path, h, text in ucs:
        name = path.name
        if "_error" in h:
            p.append(f"{name}: {h['_error']}")
            continue
        i = h.get("id", "")
        if i in seen:
            p.append(f"{name}: duplicate id {i}")
        seen.add(i)
        if not id_re().fullmatch(i) or not name.startswith(i + "-"):
            p.append(f"{name}: id '{i}' is not {PREFIX}-<area><n> or does not match the file name")
        elif AREAS and area_letter(i) not in AREAS:
            p.append(f"{name}: area letter {area_letter(i)} is not one of {sorted(AREAS)}")
        if i in load_retired(root):
            p.append(f"{name}: {i} is retired and may not be used again")
        if h.get("type") != "use-case":
            p.append(f"{i}: type must be use-case")
        if h.get("status") not in STATUS:
            p.append(f"{i}: status must be one of {sorted(STATUS)}")
        if not h.get("actor") or (ACTORS and h.get("actor") not in ACTORS):
            p.append(f"{i}: actor must be one of {sorted(ACTORS)}" if ACTORS else f"{i}: actor is missing")
        for who in h.get("provided_by", []):
            if PROVIDERS and who not in PROVIDERS:
                p.append(f"{i}: provided_by '{who}' must be one of {sorted(PROVIDERS)}")
        if not h.get("context"):
            p.append(f"{i}: context is missing")
        elif AREAS and h.get("context") not in AREAS.values():
            p.append(f"{i}: context must be one of {sorted(AREAS.values())}")
        elif AREAS and id_re().fullmatch(i) and AREAS.get(area_letter(i)) != h.get("context"):
            p.append(f"{i}: the area letter {area_letter(i)} belongs to {AREAS.get(area_letter(i))}, not {h.get('context')}")
        if not h.get("satisfies"):
            p.append(f"{i}: serves no requirement (satisfies is empty)")
        for item in h.get("satisfies", []):
            if not isinstance(item, dict) or "reviewed" not in item:
                p.append(f"{i}: each satisfies entry needs an id and a reviewed hash")
            elif item["id"] not in reqs_by_id:
                p.append(f"{i}: serves {item['id']}, which does not exist")
        for item in h.get("criteria", []):
            if not isinstance(item, dict) or "reviewed" not in item:
                p.append(f"{i}: each criteria entry needs an id and a reviewed hash")
            elif item["id"] not in acs_by_id:
                p.append(f"{i}: lists {item['id']}, which does not exist")
        for o in h.get("objects", []):
            if not re.fullmatch(r"OBJ-[A-Z]\d+", o):
                p.append(f"{i}: '{o}' is not an OBJ- id")
        for o in h.get("rules", []):
            if not re.fullmatch(r"RULE-[A-Z]\d+", o):
                p.append(f"{i}: '{o}' is not a RULE- id")
        if not h.get("effects"):
            p.append(f"{i}: effects is empty (what does it record or send?)")
        p += slice_findings(i, h, text)[0]
        p += trace_findings(i, h, text)[0]
    return p


def diagram_findings(root, uid, text):
    """Notes on the sequence diagrams of a use case (decision 9): an Analysis section needs an analysis sequence
    diagram (UC-<id>-<slug>-analysis-sequence.puml) or a single UC-<id>-<slug>-sequence.puml, and a .puml the
    text links to must exist."""
    out, folder = [], root / UC_DIR / "diagrams"
    if analysis_revisions(text) is not None:
        have = [p.name for p in folder.glob(f"{uid}-*sequence.puml")] if folder.is_dir() else []
        if not any(n.endswith("-analysis-sequence.puml") or
                   (n.endswith("-sequence.puml") and not n.endswith("-design-sequence.puml")) for n in have):
            out.append(f"{uid}: has an Analysis section but no {uid}-<slug>-analysis-sequence.puml "
                       f"(or a single {uid}-<slug>-sequence.puml) in {UC_DIR}/diagrams")
    for name in sorted(set(re.findall(r"[\w./-]*?(UC-[\w-]+\.puml)", text))):
        if not (folder / name).is_file():
            out.append(f"{uid}: links {name}, which does not exist in {UC_DIR}/diagrams")
    return out


def notes_in(root, ucs, reqs, acs):
    reqs_by_id, acs_by_id = {r["id"]: r for r in reqs}, {a["id"]: a for a in acs}
    files = ontology_files(root)
    out = []
    for _, h, text in ucs:
        if "_error" in h:
            continue
        out += diagram_findings(root, h["id"], text)
        out += slice_findings(h["id"], h, text)[1]
        out += trace_findings(h["id"], h, text)[1]
        block = mirror_block(text)
        want = mirror({"satisfies": [i for i in h.get("satisfies", []) if isinstance(i, dict)],
                       "criteria": [i for i in h.get("criteria", []) if isinstance(i, dict)]},
                      reqs_by_id, acs_by_id)
        if block is None:
            out.append(f"{h['id']}: the copied text of its requirements and criteria is missing, run sync")
        elif block != want:
            out.append(f"{h['id']}: the copied text is out of date with the requirements files, run sync")
        if h.get("flow_reviewed") and h["flow_reviewed"] != flow_hash(text):
            out.append(f"{h['id']}: FLOW CHANGED since the last stamp. Run check-upstream: the requirements "
                       "and criteria it serves may need an edit.")
        for s in suspects(h, reqs_by_id, acs_by_id):
            out.append(f"{h['id']}: SUSPECT, {s}")
        for o in h.get("objects", []) + h.get("rules", []):
            if o not in files:
                out.append(f"{h['id']}: {o} has no ontology file yet")
        served = set(ids_of(h.get("satisfies")))
        listed = set(ids_of(h.get("criteria")))
        for a in acs:
            if set(x.strip() for x in a["requirements"].split(";")) & served and a["id"] not in listed:
                out.append(f"{h['id']}: does not list {a['id']}, which proves {a['requirements']}")
    return out


def cmd_validate(root):
    reqs, acs, ucs = load(root)
    p, n = problems_in(root, ucs, reqs, acs), notes_in(root, ucs, reqs, acs)
    for x in p:
        print("PROBLEM  " + x)
    for x in n:
        print("note     " + x)
    print(f"{len(ucs)} use case file(s): {len(p)} problem(s), {len(n)} note(s)")
    return 1 if p else 0


# ----------------------------------------------------------------------------- diagram

# The look of generated use case diagrams: a colour for each actor and a pastel box for each context. The
# blocks in <usecases>/diagrams/_usecase-actors.puml carry the actor names. Actors and contexts not listed
# here still draw: they get a name from the actor id and a colour from the palette.
ACTOR_STYLE = {}    # actor id -> short block name; filled from vbench.json "diagram"
ACTOR_COLOUR = {}
PALETTE = ["#E65100", "#AD1457", "#00838F", "#5D4037", "#1565C0", "#6A1B9A", "#455A64"]
CONTEXT_COLOUR = {}
CONTEXT_PALETTE = ["#E8F0FE", "#FFFDE7", "#ECEFF1", "#FFF3E0", "#E8F5E9", "#EDE7F6", "#FBE9E7", "#F3E5F5"]
IS_A = []   # (child, parent) actor pairs, drawn as a generalisation arrow


def actor_style(a):
    return ACTOR_STYLE.get(a) or "".join(w.capitalize() for w in re.split(r"[_\W]+", a))


def actor_colour(a):
    return ACTOR_COLOUR.get(a) or PALETTE[sum(map(ord, a)) % len(PALETTE)]


def context_colour(c):
    return CONTEXT_COLOUR.get(c) or CONTEXT_PALETTE[sum(map(ord, c)) % len(CONTEXT_PALETTE)]


def ctx_slug(context):
    return (context[3:] if context.startswith("BC-") else context).lower()


def uc_node(uid):
    return "UC_" + uid[len(PREFIX) + 1:]


GENERATED = "Generated by vbench-uc"


def is_built(h, reqs_by_id):
    """Green when every requirement the use case serves is built today, grey otherwise."""
    rows = [reqs_by_id.get(i) for i in ids_of(h.get("satisfies"))]
    return bool(rows) and all(r and r["today"] == "built" for r in rows)


def diagram_text(context, ucs, reqs_by_id):
    """A context diagram, drawn from the use case files. It is a standalone diagram and also
    exposes BOX and LINKS blocks, so usecases-overview.puml can embed it with !includesub."""
    mine = [(p, h) for p, h, _ in ucs if "_error" not in h and h.get("context") == context]
    slug = ctx_slug(context)
    name = slug.capitalize()
    actors = sorted({h["actor"] for _, h in mine})
    L = [f"@startuml usecases-{slug}", "' page: landscape", "!include _usecase-style.puml",
         f"title {SYSTEM_NAME} use cases: {name} (draft)", "",
         f"' {GENERATED} (uc_tool.py diagram). Do not edit by hand: change the use case files.",
         "' Green is built, grey is not built, from the requirements each use case serves."]
    L += [f"!includesub _usecase-actors.puml!{actor_style(a).upper()}" for a in actors]
    L += ["", f'rectangle "{SYSTEM_NAME}" {{', "!startsub BOX",
          f'  rectangle "{name}  «{context}»" as {slug.upper()}BOX {context_colour(context)} {{']
    for _, h in mine:
        label = "\\n".join(textwrap.wrap(h["name"], 26))
        fill = "COLOR_PROVIDED" if h.get("provided_by") else ("COLOR_BUILT" if is_built(h, reqs_by_id) else "COLOR_TODO")
        L.append(f'    usecase "{h["id"]}\\n{label}" as {uc_node(h["id"])} {fill}')
    L += ["  }", "!endsub", "}", "", "!startsub LINKS"]
    al = [uc_node(h["id"]) for _, h in mine]
    rows = [al[i:i + 4] for i in range(0, len(al), 4)]
    for row in rows:
        L += [f"{x} -[hidden]right-> {y}" for x, y in zip(row, row[1:])]
    L += [f"{r1[0]} -[hidden]down-> {r2[0]}" for r1, r2 in zip(rows, rows[1:])]
    L += [f"{actor_style(x)} -[hidden]right-> {actor_style(y)}" for x, y in zip(actors, actors[1:])]
    L.append("")
    for _, h in mine:
        L.append(f'{actor_style(h["actor"])} -[{actor_colour(h["actor"])}]-> {uc_node(h["id"])}')
    for child, parent in IS_A:
        if child in actors and parent in actors:
            L.append(f"{actor_style(child)} -[{actor_colour(child)},norank]-|> {actor_style(parent)}")
    L += ["!endsub", "", "legend bottom",
          f"  <back:#A5D6A7>      </back> built    <back:#D9D9D9>      </back> not built, or no requirement yet    <back:#BBDEFB>      </back> provided by {provider_label()}",
          "endlegend", "@enduml", ""]
    return "\n".join(L)


def provider_label():
    return ", ".join(sorted(PROVIDERS)) or "a platform"


def overview_text(folder):
    """The composite: every context file in the folder, embedded. Needs only the files, not the use cases."""
    ctxs = sorted(p.stem[len("usecases-"):] for p in folder.glob("usecases-*.puml")
                  if p.stem != "usecases-overview" and "!startsub BOX" in p.read_text(encoding="utf-8"))
    actor_blocks = re.findall(r"!startsub (\w+)", (folder / "_usecase-actors.puml").read_text(encoding="utf-8"))
    L = ["@startuml usecases-overview", "' page: overview", "!include _usecase-style.puml", "!define OVERVIEW",
         "skinparam dpi 60", "left to right direction", f"title {SYSTEM_NAME} use cases: overview (draft)", "",
         f"' {GENERATED} (uc_tool.py diagram overview). A composite: it embeds each context file with !includesub.", ""]
    L += [f"!includesub _usecase-actors.puml!{b}" for b in actor_blocks]
    L += ["", f'rectangle "{SYSTEM_NAME}" {{'] + [f"!includesub usecases-{c}.puml!BOX" for c in ctxs] + ["}", ""]
    L += [f"!includesub usecases-{c}.puml!LINKS" for c in ctxs]
    L += ["", "legend bottom", f"  <back:#A5D6A7>      </back> built    <back:#D9D9D9>      </back> not built, or no requirement yet    <back:#BBDEFB>      </back> provided by {provider_label()}",
          "endlegend", "@enduml", ""]
    return "\n".join(L)


def cmd_diagram(root, ctx, write, force=False):
    folder = root / UC_DIR / "diagrams"
    if ctx.lower() == "overview":
        if not (folder / "_usecase-actors.puml").exists():
            print("No diagrams folder yet: nothing to embed.")
            return 0
        text, path = overview_text(folder), folder / "usecases-overview.puml"
    else:
        key = ctx.upper()
        ucs = load_ucs(root)
        known = set(AREAS.values()) | {h.get("context") for _, h, _ in ucs if h.get("context")}
        context = next((c for c in (AREAS.get(key), key, "BC-" + key) if c in known), None)
        if context is None:
            print(f"Context must be one of {sorted(known)}, an area letter, or overview")
            return 1
        if not any(h.get("context") == context for _, h, _ in ucs):
            print(f"No use cases in {context}: nothing to draw.")
            return 0
        missing = [f for f in ("_usecase-style.puml", "_usecase-actors.puml") if not (folder / f).exists()]
        if missing:
            print(f"Note: {', '.join(missing)} not in {folder}. The diagram includes them, so add them "
                  "(see vbench-puml) before rendering.", file=sys.stderr)
        text = diagram_text(context, ucs, {r["id"]: r for r in rq.read_rows(root / rq.PATHS["req"])})
        path = folder / f"usecases-{ctx_slug(context)}.puml"
    if not write:
        print(text)
        return 0
    if path.exists() and GENERATED not in path.read_text(encoding="utf-8") and not force:
        print(f"REFUSED  {path.name} was kept by hand (it is not generated). Use --force to replace it.")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path.relative_to(root)}")
    return 0


# ----------------------------------------------------------------------------- write

def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


BEGIN = "<!-- vbench-uc:begin mirror (generated from the requirements files, do not edit here: change the row, then run sync) -->"
END = "<!-- vbench-uc:end mirror -->"


def mirror(h, reqs_by_id, acs_by_id):
    """The text of the requirements and criteria this use case points at, so it reads on its own."""
    nr, nc = len(h["satisfies"]), len(h["criteria"])
    summary = (f"The requirements and criteria it runs, copied from docs/requirements "
               f"({nr} requirement{'' if nr == 1 else 's'}, {nc} criteri{'on' if nc == 1 else 'a'}). Do not edit.")
    # Collapsed, so a reader sees the flow first and opens the copy on purpose.
    lines = [BEGIN, "", "<details>", f"<summary>{summary}</summary>", "", "## What this serves", ""]
    for item in h["satisfies"]:
        r = reqs_by_id.get(item["id"])
        lines.append(f"**{item['id']}**: {r['statement'] if r else 'NOT FOUND in requirements.md'}")
        lines.append("")
    lines += ["## Acceptance criteria it runs", ""]
    if not h["criteria"]:
        lines += ["None listed yet. A requirement without criteria cannot be confirmed.", ""]
    for item in h["criteria"]:
        a = acs_by_id.get(item["id"])
        if not a:
            lines += [f"**{item['id']}**: NOT FOUND in acceptance-criteria.md", ""]
            continue
        lines += [f"**{item['id']}** ({a['test_level']}, proves {a['requirements']})", "",
                  f"- Given {a['given']}", f"- When {a['when']}", f"- Then {a['then']}", ""]
    lines += ["## How it is verified", ""]
    levels = {}
    for item in h["criteria"]:
        a = acs_by_id.get(item["id"])
        if a:
            levels.setdefault(a["test_level"], []).append(item["id"])
    if not levels:
        lines.append("Nothing verifies it yet: it lists no criteria.")
    for level in ["acceptance", "integration", "unit", "manual", "inspection", "future"]:
        if level in levels:
            lines.append(f"- {level}: {', '.join(levels[level])}")
    lines += ["", "Each criterion is run by a test tagged `Verifies AC-<n>`.", "", "</details>", "", END]
    return "\n".join(lines)


def mirror_block(text):
    m = re.search(r"<!-- vbench-uc:begin mirror[^>]*-->.*?" + re.escape(END), text, re.S)
    return m.group(0) if m else None


TAG = re.compile(r"\s*\(((?:FR|NFR|AC)-\d+(?:,\s*(?:FR|NFR|AC)-\d+)*)\)\s*$")


TRACE_HEADINGS = ["Analysis", "Design", "Changes from analysis to design"]


def written_text(text):
    """Everything after the generated block: the part a person writes."""
    return text.split(END, 1)[1].strip() if END in text else ""


def flow_text(text):
    """The written flow. The analysis, the design and the change log are kept apart: they have their own
    freeze and checks, so editing them is not a change to the flow."""
    body = written_text(text)
    for hd in TRACE_HEADINGS:
        body = re.sub(rf"^## {re.escape(hd)}\n.*?(?=^## |\Z)", "", body, flags=re.S | re.M)
    return body.strip()


def flow_hash(text):
    return hashlib.sha1(flow_text(text).encode("utf-8")).hexdigest()[:7]


def flow_lines(text, heading, full=False):
    """The lines of one section of the written flow, without their list marks."""
    body = written_text(text) if full else flow_text(text)
    m = re.search(rf"^## {re.escape(heading)}\n+(.*?)(?=^## |\Z)", body, re.S | re.M)
    if not m:
        return []
    return [re.sub(r"^(\d+\.|-)\s+", "", ln).strip() for ln in m.group(1).splitlines() if ln.strip()]


def split_tags(line):
    m = TAG.search(line)
    if not m:
        return line, []
    return line[:m.start()].strip(), [t.strip() for t in m.group(1).split(",")]


def slice_line(uid, k, sl):
    """One slice is one thin, testable piece of the use case, and becomes one Kanban card (a TSK id)."""
    area_n = uid[len(PREFIX) + 1:]
    rules = f", rules {', '.join(sl['rules'])}" if sl.get("rules") else ""
    proves = f" ({', '.join(sl['proves'])})" if sl.get("proves") else ""
    return f"TSK-{area_n}.{k}: {sl['name']}{rules}{proves}"


def slices_of(text):
    """The slices written in a file: id, text, the criteria it proves, the rules it carries."""
    out = []
    for line in flow_lines(text, "Slices"):
        body, tags = split_tags(line)
        m = re.match(r"(TSK-[A-Z]\d+\.\d+):", body)
        out.append({"id": m.group(1) if m else None, "line": line, "proves": [t for t in tags if t.startswith("AC-")],
                    "rules": re.findall(r"RULE-[A-Z]\d+", body)})
    return out


def slice_findings(uid, h, text):
    """(problems, notes) about the slices of one use case."""
    problems, notes = [], []
    slices = slices_of(text)
    listed, rules = ids_of(h.get("criteria")), h.get("rules", [])
    if not slices:
        return problems, [f"{uid}: no slices yet (the thin pieces that become cards)"]
    for n, sl in enumerate(slices, 1):
        want = f"TSK-{uid[len(PREFIX) + 1:]}.{n}"
        if sl["id"] != want:
            problems.append(f"{uid}: slice {n} should be numbered {want}, found '{sl['id']}'")
        for a in sl["proves"]:
            if a not in listed:
                problems.append(f"{uid}: slice {sl['id']} proves {a}, which the use case does not list")
    shown = {a for sl in slices for a in sl["proves"]}
    for a in listed:
        if a not in shown:
            notes.append(f"{uid}: {a} is listed but no slice proves it")
    carried = {r for sl in slices for r in sl["rules"]}
    for r in rules:
        if r not in carried:
            notes.append(f"{uid}: {r} is checked by this use case but no slice carries it. Put it in the first slice that needs it.")
    return problems, notes


def render(h, sections, reqs_by_id, acs_by_id):
    lines = ["```yaml", f"id: {h['id']}", "type: use-case", f"name: {h['name']}", f"status: {h['status']}",
             f"actor: {h['actor']}", f"context: {h['context']}"]
    if h.get("provided_by"):
        lines.append(f"provided_by: [{', '.join(h['provided_by'])}]")
    lines.append("satisfies:")
    for s in h["satisfies"]:
        lines += [f"  - id: {s['id']}", f"    reviewed: {s['reviewed']}"]
    lines.append("criteria:" if h["criteria"] else "criteria: []")
    for s in h["criteria"]:
        lines += [f"  - id: {s['id']}", f"    reviewed: {s['reviewed']}"]
    lines.append("parameters:" if h["parameters"] else "parameters: []")
    lines += [f"  - {x}" for x in h["parameters"]]
    lines.append(f"objects: [{', '.join(h['objects'])}]")
    lines.append(f"rules: [{', '.join(h['rules'])}]")
    lines.append("effects:")
    lines += [f"  - {x}" for x in h["effects"]]
    lines.append(f"evolved_from: [{', '.join(h['evolved_from'])}]")
    body = []
    for key, title, kind in SECTIONS:
        val = sections.get(key)
        if not val:
            continue
        body += [f"## {title}", ""]
        if kind == "text":
            body.append(val)
        elif kind == "numbered":
            body += [f"{n}. {x}" for n, x in enumerate(val, 1)]
        else:
            body += [f"- {x}" for x in val]
        body.append("")
    body_text = "\n".join(body).strip()
    lines.append(f"flow_reviewed: {hashlib.sha1(body_text.encode('utf-8')).hexdigest()[:7]}")
    lines += ["```", "", f"# {h['name']}", "", mirror(h, reqs_by_id, acs_by_id), "", body_text, ""]
    return "\n".join(lines)


def cmd_create(root, dry):
    data = json.loads(sys.stdin.read() or "{}")
    reqs, acs, ucs = load(root)
    reqs_by_id, acs_by_id = {r["id"]: r for r in reqs}, {a["id"]: a for a in acs}
    area = str(data.get("area", "")).upper()
    if not re.fullmatch(r"[A-Z]", area) or (AREAS and area not in AREAS):
        print(f"REFUSED  area must be one of {sorted(AREAS)}" if AREAS else "REFUSED  area must be one capital letter")
        return 1
    context = AREAS.get(area) or data.get("context", "")
    if not context:
        print("REFUSED  this repo has no areas in vbench.json, so give a context name in the JSON (\"context\")")
        return 1
    uid = f"{PREFIX}-{area}{next_number(root, area, ucs)}"
    if data.get("id"):
        want = str(data["id"]).upper()
        taken = {h.get("id") for _, h, _ in ucs}
        if not re.fullmatch(rf"{re.escape(PREFIX)}-{area}\d+", want):
            print(f"REFUSED  id {want} does not belong to area {area}")
            return 1
        if want in taken or want in load_retired(root):
            print(f"REFUSED  id {want} is already used or retired. Ids are never reused.")
            return 1
        uid = want
    sat = [{"id": x, "reviewed": req_hash(reqs_by_id[x]) if x in reqs_by_id else "?"} for x in data.get("satisfies", [])]
    crit = [{"id": x, "reviewed": ac_hash(acs_by_id[x]) if x in acs_by_id else "?"} for x in data.get("criteria", [])]
    h = {"id": uid, "name": data.get("name", ""), "status": "draft", "actor": data.get("actor", ""),
         "context": context, "satisfies": sat, "criteria": crit, "parameters": data.get("parameters", []),
         "objects": data.get("objects", []), "rules": data.get("rules", []), "effects": data.get("effects", []),
         "evolved_from": data.get("evolved_from", []), "provided_by": data.get("provided_by", [])}
    if data.get("slices"):
        data["slices"] = [slice_line(uid, k, sl) for k, sl in enumerate(data["slices"], 1)]
    text = render(h, data, reqs_by_id, acs_by_id)
    path = root / UC_DIR / f"{uid}-{slug(h['name'])}.md"
    probs = problems_in(root, [(path, parse_header(text), text)], reqs, acs)
    if not h["name"]:
        probs.append("a use case needs a name")
    if probs:
        for x in probs:
            print("REFUSED  " + x)
        return 1
    print(f"{'would write' if dry else 'wrote'} {path.relative_to(root)}")
    if dry:
        print(text)
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return 0


def cmd_check_upstream(root, uid):
    """From the use case up to its requirements and criteria. Reports recorded facts only; edits nothing."""
    reqs, acs, ucs = load(root)
    for path, h, text in ucs:
        if h.get("id") != uid:
            continue
        served, listed = ids_of(h.get("satisfies")), ids_of(h.get("criteria"))
        steps = [split_tags(x) for x in flow_lines(text, "Main flow")]
        others = [split_tags(x) for x in flow_lines(text, "Other flows")]
        tagged = {t for _, tags in steps + others for t in tags}
        print(f"{uid} {h.get('name')}: reading its flow against {len(served)} requirement(s) and {len(listed)} criteria\n")
        todo = []
        for rid in served:
            if rid not in tagged:
                todo.append(f"{rid}: no step or other flow is tagged with it. Is it really served, or is a step missing?")
        for aid in listed:
            if aid not in tagged:
                todo.append(f"{aid}: listed, but no flow is tagged with it. Add the flow it proves, or drop it.")
        for line, tags in others:
            if line.startswith("Open:"):
                continue
            if not any(t.startswith("AC-") for t in tags):
                todo.append(f"other flow has no criterion recorded: \"{line}\". Propose one in vbench-req.")
        for line, tags in steps:
            if not tags:
                todo.append(f"step has no requirement recorded: \"{line}\". Which requirement does it serve, or is one missing?")
        for _, tags in steps + others:
            for t in tags:
                if t not in served and t not in listed:
                    todo.append(f"{t}: tagged in the flow but this use case does not serve or list it.")
        for note in slice_findings(uid, h, text)[1]:
            todo.append(note.split(": ", 1)[1])
        table_missing = [a["id"] for a in acs if a["id"] not in listed and
                       set(x.strip() for x in a["requirements"].split(";")) & set(served)]
        for aid in table_missing:
            todo.append(f"{aid}: proves a requirement this use case serves, but is not listed here.")
        if h.get("flow_reviewed") and h["flow_reviewed"] != flow_hash(text):
            print("The flow has been edited since the last stamp.\n")
        if not todo:
            print("Nothing to hand to vbench-req: every step, flow, requirement and criterion is linked.")
        else:
            print("FOR vbench-req (nothing has been changed):")
            for t in sorted(dict.fromkeys(todo)):
                print(f"  - {t}")
        return 0
    print(f"No use case {uid}.")
    return 1


def refresh(path, h, text, reqs_by_id, acs_by_id):
    want = mirror({"satisfies": h.get("satisfies", []), "criteria": h.get("criteria", [])}, reqs_by_id, acs_by_id)
    block = mirror_block(text)
    if block is None:
        return re.sub(r"(\n# [^\n]*\n)", lambda m: m.group(1) + "\n" + want + "\n", text, count=1)
    return text.replace(block, want)


def cmd_sync_all(root):
    """Refresh the copied text of every use case. Review hashes are never touched."""
    reqs, acs, ucs = load(root)
    reqs_by_id, acs_by_id = {r["id"]: r for r in reqs}, {a["id"]: a for a in acs}
    for path, h, text in ucs:
        new = refresh(path, h, text, reqs_by_id, acs_by_id)
        if new == text:
            print(f"{h.get('id')}: already matches")
        else:
            path.write_text(new, encoding="utf-8")
            print(f"{h.get('id')}: copied text refreshed (still suspect until stamped)")
    return 0


def cmd_sync(root, uid):
    reqs, acs, ucs = load(root)
    reqs_by_id, acs_by_id = {r["id"]: r for r in reqs}, {a["id"]: a for a in acs}
    for path, h, text in ucs:
        if h.get("id") == uid:
            new = refresh(path, h, text, reqs_by_id, acs_by_id)
            if new == text:
                print(f"{uid}: copied text already matches the requirements files")
            else:
                path.write_text(new, encoding="utf-8")
                print(f"{uid}: copied text refreshed. Review hashes are NOT changed: it stays suspect until stamped.")
            return 0
    print(f"No use case {uid}.")
    return 1


# ----------------------------------------------------------------------------- analysis, design, changes
# A use case file may carry three more sections: Analysis (frozen, in revisions), Design, and a log of what
# changed from the analysis to the design. Element ids are local to the file: A1, A2 for the analysis and
# D1, D2 for the design, written UC-V1/A3 from outside. Nothing in the analysis may be lost: every analysis
# element has to be accounted for in the log.

ELEMENT = re.compile(r"^([AD])(\d+) \(([^)]+)\): (.+)$")
CHANGE = re.compile(r"^(A\d+) (kept|renamed|became|split|merged|moved|dropped)(?: -> (D\d+(?:, D\d+)*))?(?:: (.+))?$")
ADDED = re.compile(r"^\+ (D\d+) added: (.+)$")


def section_raw(text, heading):
    m = re.search(rf"^## {re.escape(heading)}\n+(.*?)(?=^## |\Z)", written_text(text), re.S | re.M)
    return m.group(1) if m else None


def analysis_revisions(text):
    raw = section_raw(text, "Analysis")
    if raw is None:
        return None
    parts = re.split(r"(?m)^### Revision (\d+)\s*$", raw)
    return [(int(parts[i]), parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]


def revision_hash(body):
    return hashlib.sha1(body.encode("utf-8")).hexdigest()[:7]


def elements_of(body, prefix):
    out = []
    for ln in body.splitlines():
        m = ELEMENT.match(re.sub(r"^-\s+", "", ln.strip()))
        if m and m.group(1) == prefix:
            out.append((m.group(1) + m.group(2), m.group(3), m.group(4)))
    return out


def trace_parse(uid, text):
    """The three sections as data. Returns (analysis ids with text, design ids with text, changes, added, bad)."""
    revs = analysis_revisions(text)
    a, d, changes, added, bad = {}, {}, [], {}, []
    for _, body in revs or []:
        for i, kind, t in elements_of(body, "A"):
            a[i] = (kind, t)
    d_raw = section_raw(text, "Design") or ""
    for i, kind, t in elements_of(d_raw, "D"):
        d[i] = (kind, t)
    for ln in flow_lines(text, "Changes from analysis to design", full=True):
        if ln.startswith("```") or not ln:
            continue
        m = CHANGE.match(ln)
        if m:
            changes.append((m.group(1), m.group(2), re.findall(r"D\d+", m.group(3) or ""), m.group(4) or ""))
            continue
        m = ADDED.match(ln)
        if m:
            added[m.group(1)] = m.group(2)
            continue
        bad.append(ln)
    return a, d, changes, added, bad


def trace_findings(uid, h, text):
    """(problems, notes) about the analysis, the design and the change log of one use case."""
    problems, notes = [], []
    revs = analysis_revisions(text)
    has_design = section_raw(text, "Design") is not None
    has_log = section_raw(text, "Changes from analysis to design") is not None
    if revs is None:
        if has_design or has_log:
            problems.append(f"{uid}: a design or a change log with no analysis")
        else:
            notes.append(f"{uid}: no analysis yet")
        return problems, notes
    if not revs:
        problems.append(f"{uid}: the Analysis section needs a '### Revision 1' heading")
        return problems, notes
    frozen = h.get("analysis_frozen", [])
    if isinstance(frozen, str):
        frozen = [frozen] if frozen else []
    for n, (num, body) in enumerate(revs):
        if n < len(frozen):
            if revision_hash(body) != frozen[n]:
                problems.append(f"{uid}: analysis revision {num} was edited after the freeze. "
                                "Leave it as it was and add a new revision that says what changed")
        else:
            notes.append(f"{uid}: analysis revision {num} is not frozen yet")
    if len(frozen) > len(revs):
        problems.append(f"{uid}: a frozen analysis revision was removed. Revisions are append only")
    a, d, changes, added, bad = trace_parse(uid, text)
    seen = set()
    for _, body in revs:
        for i, _, _ in elements_of(body, "A"):
            if i in seen:
                problems.append(f"{uid}/{i}: used twice. Element ids are append only across revisions")
            seen.add(i)
    if not has_design and not changes:
        notes.append(f"{uid}: design not started")
        return problems, notes
    for ln in bad:
        problems.append(f"{uid}: cannot read the change line \"{ln}\"")
    covered, targeted = set(), set()
    for src, word, targets, reason in changes:
        if src not in a:
            problems.append(f"{uid}: the log names {src}, which is not in the analysis")
        covered.add(src)
        if word == "dropped":
            if targets:
                problems.append(f"{uid}/{src}: dropped, so it has no design element")
            if not reason:
                problems.append(f"{uid}/{src}: dropped with no reason")
        else:
            if not targets:
                problems.append(f"{uid}/{src}: {word}, but no design element is named (use -> D<n>)")
            for t in targets:
                if t not in d:
                    problems.append(f"{uid}/{src}: points at {t}, which is not in the design")
                targeted.add(t)
    for i in a:
        if i not in covered:
            problems.append(f"{uid}/{i}: LOST. Nothing in the change log says what happened to it")
    for i in d:
        if i not in targeted and i not in added:
            problems.append(f"{uid}/{i}: a design element with no source. Say where it came from, or log it as added with a reason")
    for i in added:
        if i not in d:
            problems.append(f"{uid}: the log adds {i}, which is not in the design")
    return problems, notes


def cmd_trace(root, uid):
    """From each analysis element to what became of it in the design. Facts only."""
    for path, h, text in load_ucs(root):
        if h.get("id") != uid:
            continue
        revs = analysis_revisions(text)
        if revs is None:
            print(f"{uid}: no analysis yet")
            return 0
        a, d, changes, added, bad = trace_parse(uid, text)
        print(f"{uid} {h.get('name')}: {len(a)} analysis element(s), {len(d)} design element(s)\n")
        done = {}
        for src, word, targets, reason in changes:
            done.setdefault(src, []).append((word, targets, reason))
        for i, (kind, t) in a.items():
            print(f"  {i} ({kind}) {t}")
            if i not in done:
                print("      LOST: nothing says what happened to it")
            for word, targets, reason in done.get(i, []):
                dest = ", ".join(f"{x} ({d[x][0]}) {d[x][1]}" if x in d else f"{x} (missing)" for x in targets) or "no design element"
                print(f"      {word} -> {dest}" + (f"  [{reason}]" if reason else ""))
        for i, reason in added.items():
            print(f"  + {i} ({d[i][0]}) {d[i][1]}  [added: {reason}]" if i in d else f"  + {i} (missing)")
        return 0
    print(f"No use case {uid}.")
    return 1


def cmd_freeze(root, uid):
    """Record a hash of each analysis revision, so an edit to a frozen one is caught."""
    for path, h, text in load_ucs(root):
        if h.get("id") != uid:
            continue
        revs = analysis_revisions(text)
        if not revs:
            print(f"{uid}: there is no analysis revision to freeze.")
            return 1
        hashes = [revision_hash(b) for _, b in revs]
        line = f"analysis_frozen: [{', '.join(hashes)}]"
        if re.search(r"(?m)^analysis_frozen: .*$", text):
            new = re.sub(r"(?m)^analysis_frozen: .*$", line, text, count=1)
        else:
            new = re.sub(r"(?m)^(flow_reviewed: .*)$", r"\1\n" + line, text, count=1)
        path.write_text(new, encoding="utf-8")
        print(f"{uid}: froze {len(hashes)} analysis revision(s).")
        return 0
    print(f"No use case {uid}.")
    return 1


def cmd_stamp(root, uid):
    reqs, acs, ucs = load(root)
    reqs_by_id, acs_by_id = {r["id"]: r for r in reqs}, {a["id"]: a for a in acs}
    for path, h, text in ucs:
        if h.get("id") != uid:
            continue

        def fix(m):
            kind = reqs_by_id if m.group(2) in reqs_by_id else acs_by_id
            row = kind.get(m.group(2))
            if row is None:
                return m.group(0)
            new = req_hash(row) if kind is reqs_by_id else ac_hash(row)
            return f"{m.group(1)}{m.group(2)}\n    reviewed: {new}"
        new_text = re.sub(r"(  - id: )((?:FR|NFR|AC)-\d+)\n    reviewed: \S+", fix, text)
        new_text = refresh(path, h, new_text, reqs_by_id, acs_by_id)
        new_text = re.sub(r"(?m)^flow_reviewed: \S+$", f"flow_reviewed: {flow_hash(new_text)}", new_text, count=1)
        if new_text == text:
            print(f"{uid}: already up to date")
        else:
            path.write_text(new_text, encoding="utf-8")
            print(f"{uid}: review hashes updated to the current rows")
        return 0
    print(f"No use case {uid}.")
    return 1


# ----------------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("text")
    s.add_argument("--top", type=int, default=4)
    i = sub.add_parser("impact")
    i.add_argument("ids", nargs="+")
    sub.add_parser("coverage")
    n = sub.add_parser("next-id")
    n.add_argument("area")
    sub.add_parser("validate")
    c = sub.add_parser("create")
    c.add_argument("--dry-run", action="store_true")
    st = sub.add_parser("stamp")
    st.add_argument("id")
    fr = sub.add_parser("freeze")
    fr.add_argument("id")
    tr = sub.add_parser("trace")
    tr.add_argument("id")
    sy = sub.add_parser("sync")
    sy.add_argument("id", nargs="?")
    sy.add_argument("--all", action="store_true", help="refresh every use case")
    cu = sub.add_parser("check-upstream")
    cu.add_argument("id")
    dg = sub.add_parser("diagram")
    dg.add_argument("context")
    dg.add_argument("--write", action="store_true")
    dg.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve() if a.root else rq.find_root()
    use_config(root)
    if a.cmd == "search":
        cmd_search(root, a.text, a.top)
        return 0
    if a.cmd == "impact":
        return cmd_impact(root, a.ids)
    if a.cmd == "coverage":
        cmd_coverage(root)
        return 0
    if a.cmd == "next-id":
        return cmd_next_id(root, a.area)
    if a.cmd == "validate":
        return cmd_validate(root)
    if a.cmd == "create":
        return cmd_create(root, a.dry_run)
    if a.cmd == "freeze":
        return cmd_freeze(root, a.id)
    if a.cmd == "trace":
        return cmd_trace(root, a.id)
    if a.cmd == "sync":
        if a.all:
            return cmd_sync_all(root)
        if not a.id:
            print("Give a use case id, or --all to refresh every use case.")
            return 1
        return cmd_sync(root, a.id)
    if a.cmd == "diagram":
        return cmd_diagram(root, a.context, a.write, a.force)
    if a.cmd == "check-upstream":
        return cmd_check_upstream(root, a.id)
    return cmd_stamp(root, a.id)


if __name__ == "__main__":
    sys.exit(main())
