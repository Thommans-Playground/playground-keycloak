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
    for body in ("with pytest.raises(ValueError):\n        int('x')", "assert_ok(1)", "self.assertEqual(1, 1)"):
        setup(
            proj,
            f'import pytest\n@pytest.mark.ac("AC-A-001")\ndef test_it():\n    """Verifies UC-A-001 · unit rung."""\n    {body}\n',  # noqa: E501
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
