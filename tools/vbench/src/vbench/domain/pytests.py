"""Read a Python test file the way a reader would, so a tag only counts when a real test stands behind it.

The gates used to look for `Verifies UC-…` and the AC marker anywhere in the text, so a comment, a string or
a test with no assertion satisfied them. For Python this module parses the file with `ast` and answers:

    - which `Verifies` clauses sit in a docstring (module, class or test function), and whether a *real* test
      backs each one;
    - which acceptance criteria are marked on a real test, and which only on a hollow one.

A test is *real* when it is a `test*` function that is not skipped or expected to fail and that asserts something
which can fail: an `assert` of more than a constant, a `pytest.raises`/`warns` block, or a call to something
named `assert…`. That is still a floor, not a judgement of quality: `assert result is not None` passes it.
Other languages, and Python files that do not parse, keep the old text match (weaker, and said so).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from .config import Config

SKIPPED = re.compile(r"^(?:pytest\.)?mark\.(?:skip|xfail)\b|^(?:unittest\.)?(?:skip|expectedFailure)\b")
ASSERT_CALLS = {"raises", "warns", "deprecated_call"}


@dataclass(frozen=True)
class TestFn:
    __test__ = False  # not a pytest class

    name: str
    real: bool
    why: str  # empty when real; otherwise what is missing
    acs: frozenset[str]


@dataclass
class PyTests:
    clauses: list[tuple[str, bool]] = field(default_factory=list)  # (text after "Verifies", a real test backs it)
    functions: list[TestFn] = field(default_factory=list)


def _call_name(node: ast.Call) -> str:
    f = node.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def _refers_to_something(expr: ast.expr) -> bool:
    """False for `assert True`, `assert 1 == 1`: an assertion made only of literals cannot fail."""
    return any(isinstance(n, ast.Name | ast.Attribute | ast.Call | ast.Subscript) for n in ast.walk(expr))


def _asserts_something(fn: ast.AST) -> bool:
    for n in ast.walk(fn):
        if isinstance(n, ast.Assert) and _refers_to_something(n.test):
            return True
        if isinstance(n, ast.Call):
            name = _call_name(n)
            if "assert" in name.lower() or name in ASSERT_CALLS:
                return True
    return False


def _skipped(decorators: list[ast.expr]) -> bool:
    return any(SKIPPED.match(ast.unparse(d)) for d in decorators)


def _marks(cfg: Config, nodes: list[ast.expr]) -> set[str]:
    text = " ".join(ast.unparse(n) for n in nodes)
    return {ac for call in cfg.ac_mark_re.findall(text) for ac in cfg.ac_re.findall(call)}


def _module_marks(cfg: Config, tree: ast.Module) -> set[str]:
    values = [
        n.value
        for n in tree.body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in n.targets)
    ]
    return _marks(cfg, values)


def _function(cfg: Config, fn: ast.FunctionDef | ast.AsyncFunctionDef, inherited: set[str]) -> TestFn:
    if _skipped(fn.decorator_list):
        why = "it is skipped or expected to fail"
    elif not _asserts_something(fn):
        why = "it asserts nothing that can fail"
    else:
        why = ""
    return TestFn(fn.name, not why, why, frozenset(inherited | _marks(cfg, fn.decorator_list)))


def read_python_tests(cfg: Config, source: str, verifies: re.Pattern[str]) -> PyTests | None:
    """None when the file does not parse (the caller falls back to the text match)."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    out = PyTests()
    module = _module_marks(cfg, tree)
    docs: list[tuple[str, list[TestFn] | None]] = []  # (docstring, the tests it covers; None = every test in the file)
    docs.append((ast.get_docstring(tree) or "", None))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("test"):
            fn = _function(cfg, node, module)
            out.functions.append(fn)
            docs.append((ast.get_docstring(node) or "", [fn]))
        elif isinstance(node, ast.ClassDef):
            inherited = module | _marks(cfg, node.decorator_list)
            members = [
                _function(cfg, m, inherited)
                for m in node.body
                if isinstance(m, ast.FunctionDef | ast.AsyncFunctionDef) and m.name.startswith("test")
            ]
            out.functions += members
            docs.append((ast.get_docstring(node) or "", members))
            for m in node.body:
                if isinstance(m, ast.FunctionDef | ast.AsyncFunctionDef) and m.name.startswith("test"):
                    docs.append((ast.get_docstring(m) or "", [f for f in members if f.name == m.name]))
    for text, covered in docs:
        scope = out.functions if covered is None else covered
        backed = any(f.real for f in scope)
        out.clauses += [(clause, backed) for clause in verifies.findall(text)]
    return out
