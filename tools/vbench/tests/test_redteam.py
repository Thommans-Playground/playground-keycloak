"""The cheap ways round the gates, tried against a real project: each must still be caught.

A gate that checks a link exists is only worth something if the link cannot be faked with a comment, a string,
a skipped test or a test that asserts nothing. The Python test files are read structurally (`domain/pytests.py`).
"""

from __future__ import annotations

from pathlib import Path

from vbench.domain.checks import check_acs, check_rungs

from .test_vbench import ctx, spec, write

REAL = 'def test_it():\n    """Verifies UC-A-001 · unit rung."""\n    assert str(1) == "1"\n'


def setup(proj: Path, test_source: str, acs=("AC-A-001",)) -> None:
    write(proj / "src/thing.py", '"""Realises UC-A-001"""\n')
    spec(proj, "UC-A-001", list(acs))
    write(proj / "tests/test_thing.py", test_source)


def rungs_ok(proj: Path) -> bool:
    return check_rungs(*ctx(proj)).ok


def acs_ok(proj: Path) -> bool:
    return check_acs(*ctx(proj)).ok


def test_a_real_test_closes_both_gates(proj: Path):
    setup(proj, 'import pytest\n@pytest.mark.ac("AC-A-001")\n' + REAL)
    assert rungs_ok(proj) and acs_ok(proj)


def test_assert_true_and_literal_only_assertions_do_not_count(proj: Path):
    for body in ("assert True", "assert 1 == 1", "assert 'ok'", "pass", "..."):
        setup(
            proj,
            f'import pytest\n@pytest.mark.ac("AC-A-001")\ndef test_it():\n    """Verifies UC-A-001 · unit rung."""\n    {body}\n',  # noqa: E501
        )
        assert not rungs_ok(proj) and not acs_ok(proj), body
    out = check_acs(*ctx(proj)).render()
    assert "marked only on tests/test_thing.py::test_it (it asserts nothing that can fail)" in out


def test_a_skipped_or_xfail_test_does_not_count(proj: Path):
    for deco in ("@pytest.mark.skip", '@pytest.mark.skip(reason="later")', "@pytest.mark.xfail", "@unittest.skip('x')"):
        setup(proj, f'import pytest\n@pytest.mark.ac("AC-A-001")\n{deco}\n{REAL}')
        assert not rungs_ok(proj) and not acs_ok(proj), deco
    setup(proj, f'import pytest\n@pytest.mark.ac("AC-A-001")\n@pytest.mark.skipif(False, reason="x")\n{REAL}')
    assert rungs_ok(proj) and acs_ok(proj)  # a condition is not a skip


def test_tags_in_comments_and_strings_do_not_count(proj: Path):
    setup(
        proj,
        '# Verifies UC-A-001 · unit rung.\n# pytest.mark.ac("AC-A-001")\ndef test_it():\n    assert str(1) == "1"\n',
    )
    assert not rungs_ok(proj) and not acs_ok(proj)
    setup(
        proj,
        'NOTE = "Verifies UC-A-001 · unit rung. pytest.mark.ac(\'AC-A-001\')"\ndef test_it():\n    assert str(1) == "1"\n',  # noqa: E501
    )
    assert not rungs_ok(proj) and not acs_ok(proj)


def test_a_tag_with_no_test_function_does_not_count(proj: Path):
    setup(proj, '"""Verifies UC-A-001 · unit rung."""\nimport pytest\nx = pytest.mark.ac("AC-A-001")\n')
    assert not rungs_ok(proj) and not acs_ok(proj)
    assert "no real test stands behind" in check_rungs(*ctx(proj)).render()


def test_the_marker_counts_on_a_class_and_at_module_level(proj: Path):
    body = '    def test_it(self):\n        """Verifies UC-A-001 · unit rung."""\n        assert str(1) == "1"\n'
    setup(proj, f'import pytest\n@pytest.mark.ac("AC-A-001")\nclass TestIt:\n{body}')
    assert rungs_ok(proj) and acs_ok(proj)
    setup(proj, f'import pytest\npytestmark = pytest.mark.ac("AC-A-001")\nclass TestIt:\n{body}')
    assert rungs_ok(proj) and acs_ok(proj)


def test_assert_helpers_and_raises_count(proj: Path):
    for body in ("with pytest.raises(ValueError):\n        int('x')", "assert_ok(1)"):
        top = "def assert_ok(v):\n    assert str(v) == '1'\n\n" if "assert_ok" in body else ""
        setup(
            proj,
            f'import pytest\n{top}@pytest.mark.ac("AC-A-001")\ndef test_it():\n    """Verifies UC-A-001 · unit rung."""\n    {body}\n',  # noqa: E501
        )
        assert rungs_ok(proj) and acs_ok(proj), body


def test_other_languages_and_unparseable_python_keep_the_text_match(proj: Path):
    write(
        proj / ".vbench/config.toml",
        (proj / ".vbench/config.toml").read_text().replace('test_ext = [".py"]', 'test_ext = [".py", ".ts"]'),
    )
    write(proj / "src/thing.py", '"""Realises UC-A-001"""\n')
    spec(proj, "UC-A-001", ["AC-A-001"])
    write(proj / "tests/thing.test.ts", "// Verifies UC-A-001 · unit rung.\n")
    assert rungs_ok(proj)
    write(proj / "tests/thing.test.ts", "")
    write(proj / "tests/test_thing.py", '"""Verifies UC-A-001 · unit rung."""\ndef test_it(:\n')
    assert rungs_ok(proj)  # does not parse: the old match applies, and the project's own test run will fail


# ---------------------------------------------------------------------------------------------------------
# The second round of cheap bypasses (spec §3): dead code, nested functions, assert-named calls, skips made in the
# body, tests pytest never collects, and tautologies. Each case is a whole test file; `counts` says whether the gates
# take it as real. A gate that passes any of the HOLLOW cases is a gate that proves nothing.
# ---------------------------------------------------------------------------------------------------------

DOC = '"""Verifies UC-A-001 · unit rung."""'


def one_test(body: str, top: str = "") -> str:
    """A file with one tagged test whose body is `body` (written at one level of indent already)."""
    pad = "\n".join("    " + ln if ln else ln for ln in body.splitlines())
    return f'import pytest\n{top}\n@pytest.mark.ac("AC-A-001")\ndef test_it():\n    {DOC}\n{pad}\n'


def counts(proj: Path, source: str, name: str = "tests/test_thing.py") -> bool:
    write(proj / "src/thing.py", '"""Realises UC-A-001"""\n')
    spec(proj, "UC-A-001", ["AC-A-001"])
    for stale in (proj / "tests").glob("*.py"):
        stale.unlink()
    write(proj / name, source)
    both = (rungs_ok(proj), acs_ok(proj))
    assert both[0] == both[1], f"the two gates disagree: rungs={both[0]} acs={both[1]}"
    return both[0]


HOLLOW_BODIES = {
    "if False": "if False:\n    assert str(1) == '1'",
    "if 0": "if 0:\n    assert str(1) == '1'",
    "if None": "assert True\nif None:\n    assert str(1) == '1'",
    "else of if True": "if True:\n    pass\nelse:\n    assert str(1) == '1'",
    "after return": "return\nassert str(1) == '1'",
    "after raise": "raise ValueError\nassert str(1) == '1'",
    "while False": "while False:\n    assert str(1) == '1'",
    "empty for": "for _ in []:\n    assert str(1) == '1'",
    "nested never called": "def check():\n    assert str(1) == '1'",
    "lambda only": "f = lambda: str(1) == '1'",
    "undefined assert helper": "assert_nothing(1)",
    "assert named method on anything": "obj = object()\nobj.assert_equal(1, 1)",
    "self.assert outside a TestCase": "self = object()\nself.assertEqual(1, 1)",
    "skip in the body": "pytest.skip('later')\nassert str(1) == '1'",
    "xfail in the body": "pytest.xfail('later')\nassert str(1) == '1'",
    "or True": "assert str(1) == '2' or True",
    "x equals x": "x = str(1)\nassert x == x",
    "x is x": "x = str(1)\nassert x is x",
}


def test_dead_code_and_hollow_assertions_do_not_count(proj: Path):
    for label, body in HOLLOW_BODIES.items():
        assert not counts(proj, one_test(body)), label


def test_a_helper_that_asserts_nothing_does_not_count(proj: Path):
    top = "def assert_ok(v):\n    pass\n"
    assert not counts(proj, one_test("assert_ok(1)", top))


def test_live_code_helpers_and_known_assert_apis_count(proj: Path):
    cases = {
        "a live branch": ("if str(1):\n    assert str(1) == '1'", ""),
        "a nested function that is called": ("def check():\n    assert str(1) == '1'\ncheck()", ""),
        "a same file helper that asserts": ("assert_ok(1)", "def assert_ok(v):\n    assert str(v) == '1'\n"),
        "a helper that calls a helper": (
            "assert_ok(1)",
            "def check(v):\n    assert str(v) == '1'\n\ndef assert_ok(v):\n    check(v)\n",
        ),
        "a mock assertion": ("m = Mock()\nm()\nm.assert_called_once()", "from unittest.mock import Mock"),
        "numpy testing": ("np.testing.assert_allclose(1, 1)", "import numpy as np"),
        "raises": ("with pytest.raises(ValueError):\n    int('x')", ""),
        "a real comparison": ("x = str(1)\nassert x == '1'", ""),
    }
    for label, (body, top) in cases.items():
        assert counts(proj, one_test(body, top)), label


def test_a_testcase_may_use_its_own_assert_methods_and_a_plain_class_may_not(proj: Path):
    case = (
        'import unittest\nimport pytest\n@pytest.mark.ac("AC-A-001")\n'
        "class {name}({base}):\n    def test_it(self):\n        {doc}\n        self.assertEqual(1, 1)\n"
    )
    assert counts(proj, case.format(name="TestIt", base="unittest.TestCase", doc=DOC))
    assert not counts(proj, case.format(name="TestIt", base="object", doc=DOC))


def test_tests_pytest_would_not_run_do_not_count(proj: Path):
    method = '    def test_it(self):\n        """Verifies UC-A-001 · unit rung."""\n        assert str(1) == "1"\n'
    mark = 'import pytest\n@pytest.mark.ac("AC-A-001")\n'
    assert counts(proj, f"{mark}class TestIt:\n{method}")
    assert not counts(proj, f"{mark}class Helper:\n{method}"), "a class not named Test* is never collected"
    init = "    def __init__(self):\n        pass\n"
    assert not counts(proj, f"{mark}class TestIt:\n{init}{method}"), "a class with __init__ is never collected"
    good = '    """Verifies UC-A-001 · unit rung."""\n    assert str(1) == "1"\n'
    hollow = '    """Verifies UC-A-001 · unit rung."""\n    pass\n'
    twice = f'{mark}def test_it():\n{good}\n\n@pytest.mark.ac("AC-A-001")\ndef test_it():\n{hollow}'
    assert not counts(proj, twice), "the second definition replaces the first: only the hollow one runs"
    swapped = f'{mark}def test_it():\n{hollow}\n\n@pytest.mark.ac("AC-A-001")\ndef test_it():\n{good}'
    assert counts(proj, swapped)


def test_a_file_pytest_does_not_collect_does_not_count(proj: Path):
    source = one_test("assert str(1) == '1'")
    assert counts(proj, source, "tests/test_thing.py")
    assert counts(proj, source, "tests/thing_test.py")
    assert not counts(proj, source, "tests/helpers.py"), "pytest only collects test_*.py and *_test.py"
    assert not counts(proj, source, "tests/conftest.py")


def test_skips_made_outside_the_test_do_not_count(proj: Path):
    real = 'def test_it():\n    """Verifies UC-A-001 · unit rung."""\n    assert str(1) == "1"\n'
    mark = '@pytest.mark.ac("AC-A-001")\n'
    assert not counts(proj, f"import pytest\npytestmark = pytest.mark.skip\n{mark}{real}")
    assert not counts(proj, f"import pytest\npytestmark = [pytest.mark.xfail]\n{mark}{real}")
    cls = f"{mark}@pytest.mark.skip\nclass TestIt:\n    " + real.replace("\n", "\n    ").rstrip() + "\n"
    assert not counts(proj, f"import pytest\n{cls.replace('def test_it():', 'def test_it(self):')}")
    assert not counts(proj, f'import pytest\n{mark}@pytest.mark.skipif(True, reason="no")\n{real}')
    assert not counts(proj, f'import pytest\n{mark}@pytest.mark.parametrize("x", [])\n{real.replace("()", "(x)")}')
    assert counts(proj, f'import pytest\n{mark}@pytest.mark.parametrize("x", [1])\n{real.replace("()", "(x)")}')


def test_an_id_that_only_starts_like_ours_closes_nothing(proj: Path):
    """UC-A-0021 is not UC-A-002: the match needs a word boundary on both sides."""
    write(proj / "src/thing.py", '"""Realises UC-A-002"""\n')
    spec(proj, "UC-A-002", ["AC-A-002"])
    write(
        proj / "tests/test_thing.py",
        'import pytest\n@pytest.mark.ac("AC-A-0021")\ndef test_it():\n'
        '    """Verifies UC-A-0021 · unit rung."""\n    assert str(1) == "1"\n',
    )
    assert not rungs_ok(proj) and not acs_ok(proj)
    write(proj / "src/other.py", '"""Realises UC-A-0021"""\n')
    assert "UC-A-0021" not in check_rungs(*ctx(proj)).render()


# ---------------------------------------------------------------------------------------------------------
# Claims with nothing behind them: a scaffolded fake left in the code, code that realises no use case, and a
# requirement marked built that no test validates.
# ---------------------------------------------------------------------------------------------------------

from vbench import cli  # noqa: E402
from vbench.domain.checks import CHECKS  # noqa: E402


def test_a_fake_marker_in_production_code_fails_the_gate(proj: Path, capsys):
    write(proj / "src/thing.py", '"""Realises UC-A-001"""\ndef step():\n    return 1  # FAKE: STP-A-001\n')
    res = CHECKS["fakes"](*ctx(proj))
    assert not res.ok
    assert "src/thing.py:3" in res.render() and "STP-A-001" in res.render()
    assert cli.main(["check", "fakes"]) == 1
    assert cli.main(["check"]) == 1, "a fake left in the code fails `vbench check` as a whole"


def test_no_fake_marker_and_fakes_in_tests_are_fine(proj: Path):
    write(proj / "src/thing.py", '"""Realises UC-A-001"""\ndef step():\n    return 1\n')
    write(proj / "tests/test_thing.py", "FAKE = 1  # FAKE: a test double is allowed in a test\n")
    assert CHECKS["fakes"](*ctx(proj)).ok


def test_a_fake_marker_in_any_comment_style_counts(proj: Path):
    for line in ("x = 1  # FAKE: STP-A-001", "x = 1  #FAKE: STP-A-001", "const x = 1; // FAKE: STP-A-001"):
        write(proj / "src/thing.py", f'"""Realises UC-A-001"""\n{line}\n')
        assert not CHECKS["fakes"](*ctx(proj)).ok, line


def test_production_code_that_realises_nothing_fails_the_rung_gate(proj: Path):
    write(proj / "src/thing.py", '"""Realises UC-A-001"""\n')
    write(proj / "src/untagged.py", "def helper():\n    return 1\n")
    spec(proj, "UC-A-001", ["AC-A-001"])
    write(proj / "tests/test_thing.py", one_test("assert str(1) == '1'"))
    res = check_rungs(*ctx(proj))
    assert not res.ok
    assert "src/untagged.py" in res.render() and "Realises" in res.render()
    assert "src/thing.py" not in res.render().split("untagged", 1)[-1]


def test_package_markers_and_listed_files_may_stay_untagged(proj: Path):
    write(proj / "src/thing.py", '"""Realises UC-A-001"""\n')
    write(proj / "src/pkg/__init__.py", "")
    write(proj / "src/pkg/vendored.py", "X = 1\n")
    spec(proj, "UC-A-001", ["AC-A-001"])
    write(proj / "tests/test_thing.py", one_test("assert str(1) == '1'"))
    assert not check_rungs(*ctx(proj)).ok  # vendored.py is still untagged
    cfg = proj / ".vbench/config.toml"
    write(cfg, cfg.read_text().replace("[vbench]", '[vbench]\nuntagged_ok = ["src/pkg/vendored.py"]', 1))
    assert check_rungs(*ctx(proj)).ok


REQ_HEAD = "| ID | Functional requirement | User story | Satisfies | UC | Maturity |\n|---|---|---|---|---|---|\n"


def requirement(proj: Path, maturity: str) -> None:
    row = f"| **REQ-FR-001** | The system shall do it. | As a user. | STK-REQ-001 | UC-A-001 | {maturity} |\n"
    write(proj / "docs/00-requirements-engineering.md", REQ_HEAD + row)


def test_a_requirement_marked_built_needs_a_criterion_a_real_test_validates(proj: Path):
    requirement(proj, "✅")
    res = CHECKS["requirements"](*ctx(proj))
    assert not res.ok and "REQ-FR-001" in res.render(), "marked built, but no criterion satisfies it"
    spec(proj, "UC-A-001", ["AC-A-001"])
    assert not CHECKS["requirements"](*ctx(proj)).ok, "a criterion nobody tests proves nothing"
    write(proj / "tests/test_thing.py", 'import pytest\n@pytest.mark.ac("AC-A-001")\ndef test_it():\n    pass\n')
    assert not CHECKS["requirements"](*ctx(proj)).ok, "a hollow test does not count"
    write(proj / "tests/test_thing.py", 'import pytest\n@pytest.mark.ac("AC-A-001")\n' + REAL)
    assert CHECKS["requirements"](*ctx(proj)).ok


def test_a_requirement_only_specified_is_not_asked_for_a_test_yet(proj: Path):
    requirement(proj, "⚪")
    assert CHECKS["requirements"](*ctx(proj)).ok
    requirement(proj, "")
    assert CHECKS["requirements"](*ctx(proj)).ok


# ---------------------------------------------------------------------------------------------------------
# Evidence: with `results = "<junit.xml>"` set, a test counts only when it ran and passed in that run.
# The text of a file cannot tell a test that is skipped by an `importorskip`, deselected, or failing.
# ---------------------------------------------------------------------------------------------------------

RESULTS = "reports/junit.xml"
CASE = {"passed": "", "skipped": '<skipped message="no"/>', "failed": '<failure message="no"/>', "error": "<error/>"}


def junit(*cases: tuple[str, str, str]) -> str:
    body = "".join(f'<testcase classname="{c}" name="{n}">{CASE[o]}</testcase>' for c, n, o in cases)
    return f'<?xml version="1.0"?><testsuites><testsuite name="pytest">{body}</testsuite></testsuites>'


def with_results(proj: Path, xml: str | None) -> None:
    cfg = proj / ".vbench/config.toml"
    if f'results = "{RESULTS}"' not in cfg.read_text():
        write(cfg, cfg.read_text().replace("[vbench]", f'[vbench]\nresults = "{RESULTS}"', 1))
    if xml is not None:
        write(proj / RESULTS, xml)


def all_gates(proj: Path) -> tuple[bool, bool]:
    return rungs_ok(proj), acs_ok(proj)


def test_a_test_counts_only_when_it_passed_in_the_recorded_run(proj: Path):
    setup(proj, 'import pytest\n@pytest.mark.ac("AC-A-001")\n' + REAL)
    assert all_gates(proj) == (True, True)  # no results configured: the structural reading, as before
    with_results(proj, junit(("tests.test_thing", "test_it", "passed")))
    assert all_gates(proj) == (True, True)
    for outcome in ("skipped", "failed", "error"):
        write(proj / RESULTS, junit(("tests.test_thing", "test_it", outcome)))
        assert all_gates(proj) == (False, False), outcome
    write(proj / RESULTS, junit(("tests.test_other", "test_it", "passed")))
    assert all_gates(proj) == (False, False), "a test that is not in the run did not run"


def test_a_missing_results_file_proves_nothing(proj: Path):
    setup(proj, 'import pytest\n@pytest.mark.ac("AC-A-001")\n' + REAL)
    with_results(proj, None)
    assert all_gates(proj) == (False, False)
    assert "reports/junit.xml" in check_acs(*ctx(proj)).render()


def test_the_reason_a_test_did_not_count_is_named(proj: Path):
    setup(proj, 'import pytest\n@pytest.mark.ac("AC-A-001")\n' + REAL)
    with_results(proj, junit(("tests.test_thing", "test_it", "skipped")))
    assert "did not pass in the last run (skipped)" in check_acs(*ctx(proj)).render()


def test_every_parametrised_case_must_pass_and_a_class_name_is_not_in_the_way(proj: Path):
    setup(proj, 'import pytest\n@pytest.mark.ac("AC-A-001")\n' + REAL)
    with_results(
        proj, junit(("tests.test_thing", "test_it[1]", "passed"), ("tests.test_thing", "test_it[2]", "passed"))
    )
    assert all_gates(proj) == (True, True)
    write(
        proj / RESULTS,
        junit(("tests.test_thing", "test_it[1]", "passed"), ("tests.test_thing", "test_it[2]", "failed")),
    )
    assert all_gates(proj) == (False, False)
    method = '    def test_it(self):\n        """Verifies UC-A-001 · unit rung."""\n        assert str(1) == "1"\n'
    setup(proj, f'import pytest\n@pytest.mark.ac("AC-A-001")\nclass TestIt:\n{method}')
    write(proj / RESULTS, junit(("tests.test_thing.TestIt", "test_it", "passed")))
    assert all_gates(proj) == (True, True)


def test_a_run_from_inside_the_tests_folder_still_matches(proj: Path):
    """pytest run from `tests/` writes `test_thing`, not `tests.test_thing`."""
    setup(proj, 'import pytest\n@pytest.mark.ac("AC-A-001")\n' + REAL)
    with_results(proj, junit(("test_thing", "test_it", "passed")))
    assert all_gates(proj) == (True, True)
