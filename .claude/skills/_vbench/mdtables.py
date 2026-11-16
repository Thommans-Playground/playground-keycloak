"""Read and write the requirements and acceptance criteria as markdown tables.

The two files are meant to be read by people, so they are markdown, not CSV:

  requirements.md          Functional requirements, then Quality / constraint / process requirements.
                           Each part is split by area (### Area A) and holds one table. The long notes sit
                           under each table as bullets: `- **FR-1:** text`.
  acceptance-criteria.md   One table of Given, When, Then scenarios.

The tools still see the same flat rows (a dict for each requirement or criterion, with the old CSV column
names), so nothing else has to know about the layout. A column that is empty on every row is left out of
the table, and it comes back when a row uses it.

Only the standard library is used.
"""

import re

REQ_HEADERS = {
    "ID": "id", "Kind": "kind", "Name": "name", "Statement": "statement",
    "Quality attribute": "quality", "Stimulus": "stimulus", "Environment": "environment",
    "Response": "response", "Measure": "measure", "Verified by": "verification",
    "Release": "release", "Built": "today", "Status": "status", "Objects": "objects",
    "Rules": "rules", "Satisfies": "satisfies", "Sources": "sources",
}
AC_HEADERS = {
    "ID": "id", "Proves": "requirements", "Given": "given", "When": "when", "Then": "then",
    "Level": "test_level", "Status": "status", "Notes": "notes",
}
REQ_COLS = ["id", "kind", "group", "area", "name", "statement", "quality", "stimulus", "environment",
            "response", "measure", "verification", "release", "today", "status", "objects", "rules",
            "satisfies", "sources", "notes"]
AC_COLS = ["id", "requirements", "given", "when", "then", "test_level", "status", "notes"]

SCENARIO = ["quality", "stimulus", "environment", "response", "measure"]

# column order in the two requirement tables: (header, key, always shown)
FUNCTIONAL = [("ID", "id", True), ("Name", "name", True), ("Statement", "statement", True),
              ("Verified by", "verification", True), ("Release", "release", True), ("Built", "today", True),
              ("Status", "status", True), ("Objects", "objects", False), ("Rules", "rules", False),
              ("Satisfies", "satisfies", False), ("Sources", "sources", False)]
OTHER = [("ID", "id", True), ("Kind", "kind", True), ("Name", "name", True), ("Statement", "statement", True),
         ("Quality attribute", "quality", False), ("Stimulus", "stimulus", False),
         ("Environment", "environment", False), ("Response", "response", False),
         ("Measure", "measure", False), ("Verified by", "verification", True), ("Release", "release", True),
         ("Built", "today", True), ("Status", "status", True), ("Objects", "objects", False),
         ("Rules", "rules", False), ("Satisfies", "satisfies", False), ("Sources", "sources", False)]
CRITERIA = [("ID", "id", True), ("Proves", "requirements", True), ("Given", "given", True),
            ("When", "when", True), ("Then", "then", True), ("Level", "test_level", True),
            ("Status", "status", True), ("Notes", "notes", False)]

NOTE = re.compile(r"^- \*\*((?:FR|NFR|AC)-\d+):\*\* ?(.*)$")
AREA = re.compile(r"^### Area (.+?)\s*$")
NO_AREA = "No area"


# ----------------------------------------------------------------------------- cells

def esc(value):
    return str(value).replace("\r\n", "\n").replace("|", "\\|").replace("\n", "<br>")


def unesc(cell):
    return cell.strip().replace("<br>", "\n").replace("\\|", "|")


def split_row(line):
    parts = re.split(r"(?<!\\)\|", line.strip())
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [unesc(p) for p in parts]


def built_in(value):
    return {"yes": "built", "no": "not built"}.get(value, value)


def built_out(value):
    return {"built": "yes", "not built": "no"}.get(value, value)


# ----------------------------------------------------------------------------- reading

def read_md(text):
    """Return the flat rows of a requirements or an acceptance criteria file."""
    area = ""
    header = None
    tables = []          # (headers, rows, area)
    notes = {}
    for raw in text.splitlines():
        line = raw.rstrip()
        m = AREA.match(line)
        if m:
            area = "" if m.group(1) == NO_AREA else m.group(1)
            header = None
            continue
        if line.startswith("## ") or line.startswith("# "):
            area = "" if line.startswith("## ") else area
            header = None
            continue
        if line.startswith("|"):
            cells = split_row(line)
            if header is None:
                header = cells
                tables.append((header, [], area))
            elif all(re.fullmatch(r":?-{3,}:?", c.strip()) for c in cells if c.strip()) and cells:
                continue
            else:
                tables[-1][1].append(cells)
            continue
        header = None
        n = NOTE.match(line)
        if n:
            notes[n.group(1)] = n.group(2).replace("<br>", "\n")
    out = []
    for headers, rows, table_area in tables:
        if "Statement" in headers:
            mapping, cols, kind = REQ_HEADERS, REQ_COLS, "Kind" not in headers
        elif "Given" in headers:
            mapping, cols, kind = AC_HEADERS, AC_COLS, False
        else:
            continue
        for cells in rows:
            row = {c: "" for c in cols}
            for h, cell in zip(headers, cells):
                if h in mapping:
                    row[mapping[h]] = cell
            if mapping is REQ_HEADERS:
                if kind:
                    row["kind"] = "functional"
                row["today"] = built_in(row["today"])
                row["area"] = table_area
                row["group"] = "process" if row["kind"] == "process" else "product"
            out.append(row)
    for row in out:
        if row["id"] in notes:
            row["notes"] = notes[row["id"]]
    return out


# ----------------------------------------------------------------------------- writing

def table(columns, rows):
    shown = [(h, k) for h, k, always in columns if always or any(r.get(k, "") for r in rows)]
    lines = ["| " + " | ".join(h for h, _ in shown) + " |",
             "|" + "|".join("---" for _ in shown) + "|"]
    for r in rows:
        cells = [esc(built_out(r.get(k, "")) if k == "today" else r.get(k, "")) for _, k in shown]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def by_area(rows):
    order, groups = [], {}
    for r in rows:
        a = r.get("area", "")
        if a not in groups:
            groups[a] = []
            order.append(a)
        groups[a].append(r)
    return [(a, groups[a]) for a in order]


def notes_block(rows):
    lines = []
    for r in rows:
        if r.get("notes", ""):
            lines.append(f"- **{r['id']}:** " + str(r["notes"]).replace("\r\n", "\n").replace("\n", "<br>"))
    return ["", "**Notes**", ""] + lines if lines else []


def section(title, columns, rows):
    lines = [f"## {title}", ""]
    if not rows:
        return lines + ["_None yet._", ""]
    for a, group in by_area(rows):
        lines += [f"### Area {a or NO_AREA}", ""] + table(columns, group) + notes_block(group) + [""]
    return lines


def requirements_md(rows):
    plain = [r for r in rows if r.get("kind") == "functional" and not any(r.get(k, "") for k in SCENARIO)]
    other = [r for r in rows if r not in plain]
    lines = ["# Requirements", "",
             "<!-- Read and written by req_tool.py. A hand edit of a cell is fine: keep the table headers and the",
             "     Notes bullets in the form `- **FR-1:** text`. An empty column is left out and comes back when used. -->",
             ""]
    lines += section("Functional requirements", FUNCTIONAL, plain)
    lines += section("Quality, constraint and process requirements", OTHER, other)
    return "\n".join(lines).rstrip() + "\n"


def criteria_md(rows):
    lines = ["# Acceptance criteria", "",
             "<!-- Read and written by req_tool.py. Each row is one scenario: Given, When, Then. -->", ""]
    if rows:
        lines += table(CRITERIA, rows)
    else:
        lines += ["_None yet._"]
    return "\n".join(lines).rstrip() + "\n"
