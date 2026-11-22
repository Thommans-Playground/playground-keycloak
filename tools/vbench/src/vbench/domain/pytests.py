"""Read a Python test file the way pytest would run it, so a tag only counts when a real test stands behind it.

The gates used to look for `Verifies UC-…` and the AC marker anywhere in the text, so a comment, a string or
a test with no assertion satisfied them. For Python this module parses the file with `ast` and answers:

    - which `Verifies` clauses sit in a docstring (module, class or test function), and whether a *real* test
      backs each one;
    - which acceptance criteria are marked on a real test, and which only on a hollow one.

A test is *real* when pytest would collect and run it and it asserts something that can fail:

    collected   a `test*` function in a `test_*.py` or `*_test.py` file, or a method of a `Test*` class without
                `__init__` (or of a `unittest.TestCase`). Of two definitions with one name only the last runs.
    not skipped no skip or xfail decorator or `pytestmark` (also on the class), no `skipif` on a constant true, no
                empty `parametrize`, and no `pytest.skip()`/`pytest.xfail()` made at the top of the body.
    asserts     in code that can run: not under `if False`, not after a `return` or `raise`, not in a nested
                function nobody calls. An `assert` must be able to fail (not `assert True`, `x or True`, `x == x`).
                A call counts when it is `pytest.raises`/`warns`, a `unittest` assert method on `self`, a `mock`
                `assert_called…`, a `…testing.assert…`, or a function in this file that itself asserts (to depth).

That is still a floor, not a judgement of quality: `assert result is not None` passes it. A helper imported from
another file is not followed, so it does not count; a conditional `pytest.skip()` or an `importorskip` cannot be
judged from the text, which is what the test results are for (`domain/junit.py`). Other languages, and Python files
that do not parse, keep the old text match (weaker, and said so).
"""

from __future__ import annotations

import ast
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from fnmatch import fnmatch
from posixpath import basename

from .config import Config

SKIPPED = re.compile(r"^(?:pytest\.)?mark\.(?:skip|xfail)\b|^(?:unittest\.)?(?:skip|expectedFailure)\b")
ASSERT_CALLS = {"pytest.raises", "pytest.warns", "pytest.deprecated_call", "raises", "warns", "deprecated_call"}
SKIP_CALLS = {"pytest.skip", "pytest.xfail", "skip", "xfail"}
MOCK_ASSERTS = ("assert_called", "assert_any_call", "assert_has_calls", "assert_not_called", "assert_awaited")
TEST_FILES = ("test_*.py", "*_test.py")
TERMINATORS = (ast.Return, ast.Raise, ast.Continue, ast.Break)
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
TRY = tuple(t for t in (ast.Try, getattr(ast, "TryStar", None)) if t)
DEPTH = 4  # how many helpers deep an assertion is followed


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


# ------------------------------------------------------------------------------------------ what can run
def _truth(expr: ast.expr) -> bool | None:
    """True or False when the condition is a literal (`if False`, `while 0`, `if not None`), else None (unknown)."""
    if isinstance(expr, ast.Constant):
        return bool(expr.value)
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        inner = _truth(expr.operand)
        return None if inner is None else not inner
    if isinstance(expr, ast.List | ast.Tuple | ast.Set | ast.Dict) and not _items(expr):
        return False
    return None


def _items(expr: ast.expr) -> list[ast.AST]:
    return list(expr.keys if isinstance(expr, ast.Dict) else expr.elts)  # type: ignore[attr-defined]


def _is_empty(expr: ast.expr) -> bool:
    return isinstance(expr, ast.List | ast.Tuple | ast.Set | ast.Dict) and not _items(expr)


def _live(body: list[ast.stmt]):
    """The statements of a block that can run: not under a literal-false branch, not after a return or raise."""
    for st in body:
        yield st
        if isinstance(st, ast.If):
            cond = _truth(st.test)
            if cond is not False:
                yield from _live(st.body)
            if cond is not True:
                yield from _live(st.orelse)
        elif isinstance(st, ast.While):
            if _truth(st.test) is not False:
                yield from _live(st.body)
            yield from _live(st.orelse)
        elif isinstance(st, ast.For | ast.AsyncFor):
            if not _is_empty(st.iter):
                yield from _live(st.body)
            yield from _live(st.orelse)
        elif isinstance(st, ast.With | ast.AsyncWith):
            yield from _live(st.body)
        elif TRY and isinstance(st, TRY):
            yield from _live(st.body)
            for handler in st.handlers:
                yield from _live(handler.body)
            yield from _live(st.orelse)
            yield from _live(st.finalbody)
        elif isinstance(st, ast.Match):
            for case in st.cases:
                yield from _live(case.body)
        if isinstance(st, TERMINATORS):
            return  # whatever follows in this block never runs


def _own(st: ast.stmt):
    """The expressions of one statement, leaving out its child statements, lambdas and handlers."""
    stack = list(ast.iter_child_nodes(st))
    while stack:
        n = stack.pop()
        if isinstance(n, ast.stmt | ast.excepthandler | ast.match_case | ast.Lambda):
            continue
        yield n
        stack.extend(ast.iter_child_nodes(n))


# ------------------------------------------------------------------------------------- what can fail
def _refers_to_something(expr: ast.expr) -> bool:
    """False for `assert True`, `assert 1 == 1`: an assertion made only of literals cannot fail."""
    return any(isinstance(n, ast.Name | ast.Attribute | ast.Call | ast.Subscript) for n in ast.walk(expr))


def _can_fail(test: ast.expr) -> bool:
    if isinstance(test, ast.Constant | ast.Tuple):  # a non-empty tuple is always true
        return False
    if isinstance(test, ast.BoolOp):
        if isinstance(test.op, ast.Or):  # one operand that cannot fail makes the whole `or` unable to
            return all(_can_fail(v) for v in test.values)
        return any(_can_fail(v) for v in test.values)
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        same = ast.dump(test.left) == ast.dump(test.comparators[0])
        if same and isinstance(test.ops[0], ast.Eq | ast.Is | ast.LtE | ast.GtE):
            return False  # x == x, x is x
    return _refers_to_something(test)


def _dotted(func: ast.expr) -> str:
    return ast.unparse(func)


class _Reader:
    """What a test body does, judged from the text of one file."""

    def __init__(self, tree: ast.Module):
        self.funcs = {n.name: n for n in tree.body if isinstance(n, FUNCTIONS)}

    def facts(
        self,
        fn: ast.FunctionDef | ast.AsyncFunctionDef,
        testcase: bool = False,
        methods: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] | None = None,
        seen: frozenset[str] = frozenset(),
    ) -> tuple[bool, bool]:
        """(asserts something that can fail, skips itself unconditionally)."""
        methods = methods or {}
        live = list(_live(fn.body))
        nested = {st.name: st for st in live if isinstance(st, FUNCTIONS)}
        skips = any(_skips_now(st) for st in fn.body)
        asserts = False
        for st in live:
            if isinstance(st, ast.Assert) and _can_fail(st.test):
                asserts = True
            for n in _own(st):
                if isinstance(n, ast.Call) and self._asserting(n, nested, testcase, methods, seen | {fn.name}):
                    asserts = True
        return asserts, skips

    def _asserting(self, call, nested, testcase, methods, seen) -> bool:
        name = _dotted(call.func)
        if name in ASSERT_CALLS:
            return True
        func = call.func
        if isinstance(func, ast.Attribute):
            if isinstance(func.value, ast.Name) and func.value.id == "self":
                if testcase and func.attr.startswith("assert"):
                    return True
                return self._follows(methods.get(func.attr), testcase, methods, seen)
            if func.attr.startswith(MOCK_ASSERTS):
                return True
            return ".testing." in f".{name}" and func.attr.startswith("assert")
        if isinstance(func, ast.Name):
            return self._follows(nested.get(func.id) or self.funcs.get(func.id), testcase, methods, seen)
        return False

    def _follows(self, helper, testcase, methods, seen) -> bool:
        if helper is None or helper.name in seen or len(seen) > DEPTH:
            return False
        return self.facts(helper, testcase, methods, seen)[0]


def _skips_now(st: ast.stmt) -> bool:
    """A skip made at the top of the body, where nothing can steer around it."""
    if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
        name = _dotted(st.value.func)
        return name in SKIP_CALLS or name.endswith(".skipTest")
    return isinstance(st, ast.Raise) and st.exc is not None and "SkipTest" in ast.unparse(st.exc)


# --------------------------------------------------------------------------------------- what pytest runs
def _skipped(decorators: list[ast.expr]) -> bool:
    for d in decorators:
        text = ast.unparse(d)
        if SKIPPED.match(text):
            return True
        if isinstance(d, ast.Call):
            head = ast.unparse(d.func)
            if head.endswith("mark.skipif") and d.args and _truth(d.args[0]) is True:
                return True  # a condition that is always true
            if head.endswith("mark.parametrize") and len(d.args) > 1 and _is_empty(d.args[1]):
                return True  # no cases: pytest skips it
    return False


def _marks(cfg: Config, nodes: list[ast.expr]) -> set[str]:
    text = " ".join(ast.unparse(n) for n in nodes)
    return {ac for call in cfg.ac_mark_re.findall(text) for ac in cfg.ac_re.findall(call)}


def _module_values(tree: ast.Module) -> list[ast.expr]:
    return [
        n.value
        for n in tree.body
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in n.targets)
    ]


def _module_skipped(tree: ast.Module) -> bool:
    values = _module_values(tree)
    flat = [e for v in values for e in (v.elts if isinstance(v, ast.List | ast.Tuple) else [v])]
    return _skipped(flat)


def _is_testcase(node: ast.ClassDef) -> bool:
    return any(ast.unparse(b).endswith("TestCase") for b in node.bases)


def _collected(node: ast.ClassDef) -> bool:
    """pytest collects `Test*` classes with no `__init__`, and any `unittest.TestCase`."""
    if _is_testcase(node):
        return True
    has_init = any(isinstance(m, FUNCTIONS) and m.name in {"__init__", "__new__"} for m in node.body)
    return node.name.startswith("Test") and not has_init


def _last_of_each_name(fns: list) -> list:
    """Python binds a name once: of two `def test_x` the second replaces the first, and only it runs."""
    return list({f.name: f for f in fns}.values())


Ran = Callable[[str], str]  # test name -> "passed", or what the recorded run says instead


def _function(
    cfg: Config, fn, inherited: set[str], skipped_outside: bool, reader: _Reader, ran: Ran | None = None, **where
) -> TestFn:
    marks = frozenset(inherited | _marks(cfg, fn.decorator_list))
    if skipped_outside or _skipped(fn.decorator_list):
        return TestFn(fn.name, False, "it is skipped or expected to fail", marks)
    asserts, skips = reader.facts(fn, **where)
    if skips:
        return TestFn(fn.name, False, "it skips itself in its body", marks)
    if not asserts:
        return TestFn(fn.name, False, "it asserts nothing that can fail", marks)
    if ran and (outcome := ran(fn.name)) != "passed":
        return TestFn(fn.name, False, f"it did not pass in the last run ({outcome})", marks)
    return TestFn(fn.name, True, "", marks)


def read_python_tests(
    cfg: Config, source: str, verifies: re.Pattern[str], path: str = "", ran: Ran | None = None
) -> PyTests | None:
    """None when the file does not parse (the caller falls back to the text match).

    `path` is the file's path: when given, a file pytest would not collect (`helpers.py`, `conftest.py`) has no
    real test in it. `ran` says what a recorded run did with a test (see `domain/junit.py`); without it the text is
    all there is to go on."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return None
    reader = _Reader(tree)
    out = PyTests()
    module_marks = _marks(cfg, _module_values(tree))
    module_skip = _module_skipped(tree)
    docs: list[tuple[str, list[TestFn] | None]] = [(ast.get_docstring(tree) or "", None)]  # None = the whole file
    top = [n for n in tree.body if isinstance(n, FUNCTIONS) and n.name.startswith("test")]
    for node in _last_of_each_name(top):
        fn = _function(cfg, node, module_marks, module_skip, reader, ran)
        out.functions.append(fn)
        docs.append((ast.get_docstring(node) or "", [fn]))
    for node in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        methods = {m.name: m for m in node.body if isinstance(m, FUNCTIONS)}
        run = _collected(node)
        class_skip = module_skip or _skipped(node.decorator_list)
        inherited = module_marks | _marks(cfg, node.decorator_list)
        members = []
        for m in _last_of_each_name([m for m in methods.values() if m.name.startswith("test")]):
            fn = _function(cfg, m, inherited, class_skip, reader, ran, testcase=_is_testcase(node), methods=methods)
            if not run:
                fn = replace(fn, real=False, why="pytest does not collect this class (Test* with no __init__)")
            members.append(fn)
            docs.append((ast.get_docstring(m) or "", [fn]))
        out.functions += members
        docs.append((ast.get_docstring(node) or "", members))
    in_collected_file = not path or any(fnmatch(basename(path), g) for g in TEST_FILES)
    for text, covered in docs:
        scope = out.functions if covered is None else covered
        backed = in_collected_file and any(f.real for f in scope)
        out.clauses += [(clause, backed) for clause in verifies.findall(text)]
    if not in_collected_file:
        why = "pytest does not collect this file (name it test_*.py or *_test.py)"
        out.functions = [replace(f, real=False, why=why) for f in out.functions]
    return out
