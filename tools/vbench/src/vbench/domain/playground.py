"""Reading a project written in the playground's own format (the auth app), as plain facts.

That format is older than vbench's three-part ids and is what `.claude/skills/vbench-*` write: ids are `UC-A1`,
`FR-1`, `NFR-1`, `AC-1`; a use case is a file with a YAML header (`id`, `name`, `satisfies`, `criteria`, `context`);
requirements are markdown tables in `docs/requirements/requirements.md` (a functional and a quality table);
criteria are a table in `docs/requirements/acceptance-criteria.md`. Nothing here touches the disk: functions take text.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

UC_ID = re.compile(r"\bUC-[A-Z]\d+\b")
AC_ID = re.compile(r"\bAC-\d+\b")
REQ_ID = re.compile(r"\b(?:FR|NFR)-\d+\b")
LIST_ITEM = re.compile(r"^\s*-\s*(?:id:\s*)?(\S+?)\s*(?:#.*)?$")
H1 = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
CELL_SPLIT = re.compile(r"(?<!\\)\|")
LEVELS = ("unit", "integration", "system", "acceptance")


@dataclass(frozen=True)
class Requirement:
    id: str
    kind: str  # FR or NFR
    name: str
    statement: str
    status: str = ""
    release: str = ""
    quality: str = ""  # NFR only, the quality attribute
    stimulus: str = ""
    environment: str = ""
    response: str = ""
    measure: str = ""


@dataclass(frozen=True)
class Criterion:
    id: str
    proves: tuple[str, ...]
    given: str
    when: str
    then: str
    level: str
    status: str
    notes: str

    @property
    def text(self) -> str:
        return f"Given {self.given}, when {self.when}, then {self.then}."

    @property
    def deferred(self) -> bool:
        return self.notes.strip().upper().startswith("R2")  # the same rule the V-cycle trace uses

    @property
    def retired(self) -> bool:
        return self.status == "retired"


@dataclass(frozen=True)
class UseCase:
    id: str
    name: str
    path: str
    status: str = ""
    actor: str = ""
    context: str = ""
    satisfies: tuple[str, ...] = ()
    criteria: tuple[str, ...] = ()
    rules: tuple[str, ...] = ()
    objects: tuple[str, ...] = ()


@dataclass(frozen=True)
class TestFn:
    file: str
    name: str
    line: int
    acs: tuple[str, ...] = ()
    docstring: str = ""


@dataclass
class _Table:
    header: list[str]
    rows: list[list[str]] = field(default_factory=list)


def _cells(line: str) -> list[str]:
    return [c.strip().replace("\\|", "|") for c in CELL_SPLIT.split(line.strip().strip("|"))]


def tables(text: str) -> list[_Table]:
    """Every markdown table in the text: a header row, a `---` separator row, then body rows."""
    out: list[_Table] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            t = _Table([c.lower() for c in _cells(lines[i])])
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                t.rows.append(_cells(lines[i]))
                i += 1
            out.append(t)
        else:
            i += 1
    return out


def _col(t: _Table, row: list[str], *names: str) -> str:
    for n in names:
        if n in t.header and t.header.index(n) < len(row):
            return row[t.header.index(n)]
    return ""


def parse_requirements(text: str) -> list[Requirement]:
    """Functional rows (`ID | Name | Statement ...`) and quality rows (`... | Quality attribute | ...`)."""
    out: list[Requirement] = []
    for t in tables(text):
        if "id" not in t.header or "statement" not in t.header:
            continue
        for row in t.rows:
            rid = _col(t, row, "id")
            if not REQ_ID.fullmatch(rid):
                continue
            out.append(
                Requirement(
                    id=rid,
                    kind="NFR" if rid.startswith("NFR") else "FR",
                    name=_col(t, row, "name"),
                    statement=_col(t, row, "statement"),
                    status=_col(t, row, "status"),
                    release=_col(t, row, "release"),
                    quality=_col(t, row, "quality attribute"),
                    stimulus=_col(t, row, "stimulus"),
                    environment=_col(t, row, "environment"),
                    response=_col(t, row, "response"),
                    measure=_col(t, row, "measure"),
                )
            )
    return out


def parse_criteria(text: str) -> list[Criterion]:
    out: list[Criterion] = []
    for t in tables(text):
        if "id" not in t.header or "given" not in t.header:
            continue
        for row in t.rows:
            cid = _col(t, row, "id")
            if not AC_ID.fullmatch(cid):
                continue
            out.append(
                Criterion(
                    id=cid,
                    proves=tuple(REQ_ID.findall(_col(t, row, "proves"))),
                    given=_col(t, row, "given"),
                    when=_col(t, row, "when"),
                    then=_col(t, row, "then"),
                    level=_col(t, row, "level").lower(),
                    status=_col(t, row, "status").lower(),
                    notes=_col(t, row, "notes"),
                )
            )
    return out


def _header(text: str) -> dict[str, object]:
    """The fenced YAML header of a use case: scalars, `[a, b]` lists and `- id: X` lists (all it uses)."""
    m = re.match(r"\s*```yaml\n(.*?)\n```", text, re.DOTALL)
    out: dict[str, object] = {}
    key = None
    for line in (m.group(1) if m else "").splitlines():
        top = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if top:
            key, value = top.group(1), top.group(2).strip()
            if value.startswith("[") and value.endswith("]"):
                out[key] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            elif value:
                out[key] = value.strip("\"'")
            else:
                out[key] = []
        elif key and isinstance(out.get(key), list):
            item = LIST_ITEM.match(line)
            if item:
                out[key].append(item.group(1).strip("\"'"))  # type: ignore[union-attr]
    return out


def parse_use_case(text: str, path: str) -> UseCase | None:
    h = _header(text)
    uid = str(h.get("id", ""))
    if not UC_ID.fullmatch(uid):
        return None

    def many(key: str) -> tuple[str, ...]:
        v = h.get(key, [])
        return tuple(v) if isinstance(v, list) else ()

    return UseCase(
        id=uid,
        name=str(h.get("name", "")) or title_of(text, uid),
        path=path,
        status=str(h.get("status", "")),
        actor=str(h.get("actor", "")),
        context=str(h.get("context", "")),
        satisfies=many("satisfies"),
        criteria=many("criteria"),
        rules=many("rules"),
        objects=many("objects"),
    )


def title_of(text: str, fallback: str) -> str:
    m = H1.search(text)
    return m.group(1) if m else fallback


AC_MARK = re.compile(r"""ac\(\s*["'](AC-\d+)["']\s*\)""")


def python_tests(text: str, path: str) -> list[TestFn]:
    """The test functions of a Python file and the criteria they carry (`@pytest.mark.ac("AC-9")`)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test"):
            acs = tuple(m for d in node.decorator_list for m in AC_MARK.findall(ast.unparse(d)))
            doc = (ast.get_docstring(node) or "").strip().splitlines()
            out.append(TestFn(path, node.name, node.lineno, acs, doc[0] if doc else ""))
    return sorted(out, key=lambda t: t.line)


def comment_tags(text: str) -> tuple[str, ...]:
    """Criteria a non-Python test names in a comment, the way `Verifies AC-36` does."""
    return tuple(dict.fromkeys(AC_ID.findall(text)))
