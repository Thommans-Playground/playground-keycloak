"""Verifies the terminal styling: roles become ANSI only on a terminal, and the words never depend on the style."""

from __future__ import annotations

import io
import re
from pathlib import Path

from vbench import cli
from vbench.adapters.term import Style, wants_color

ANSI = re.compile(r"\x1b\[[0-9;]*m")
ON = Style(True)


class Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_auto_colours_only_a_terminal_and_the_environment_can_override():
    assert wants_color("auto", Tty(), {}) is True
    assert wants_color("auto", io.StringIO(), {}) is False  # a pipe or a file
    assert wants_color("auto", Tty(), {"NO_COLOR": "1"}) is False
    assert wants_color("auto", Tty(), {"TERM": "dumb"}) is False
    assert wants_color("auto", io.StringIO(), {"FORCE_COLOR": "1"}) is True
    assert wants_color("auto", io.StringIO(), {"FORCE_COLOR": "0"}) is False
    assert wants_color("always", io.StringIO(), {"NO_COLOR": "1"}) is True
    assert wants_color("never", Tty(), {"FORCE_COLOR": "1"}) is False


def test_each_role_is_one_attribute_and_off_means_the_text_unchanged():
    assert ON("fail", "x") == "\x1b[1;31mx\x1b[0m"
    assert ON("planned", "x") == "\x1b[2;9mx\x1b[0m"  # dim and strikethrough
    assert ON("reason", "x") == "\x1b[3mx\x1b[0m"  # italic
    assert ON("path", "x") == "\x1b[4mx\x1b[0m"  # underline
    assert ON("ok", "") == ""
    assert Style(False)("fail", "x") == "x"


def test_marking_underlines_paths_and_colours_ids_without_touching_other_words():
    line = "UC-A-001: see docs/usecase-diagrams/UC-A-001-x.md and src/a.py:27 for nothing-like-this"
    marked = ON.mark(line)
    assert ANSI.sub("", marked) == line
    assert "\x1b[4mdocs/usecase-diagrams/UC-A-001-x.md\x1b[0m" in marked
    assert "\x1b[4msrc/a.py:27\x1b[0m" in marked
    assert marked.startswith("\x1b[36mUC-A-001\x1b[0m")
    assert Style(False).mark(line) == line


def test_a_failing_gate_gets_a_bold_red_heading_and_a_passing_one_a_green_name():
    assert ON.result(True, ["refs: all resolve."]) == ["\x1b[32mrefs:\x1b[0m all resolve."]
    out = ON.result(False, ["Coverage check FAILED:", "", "  - UNCOVERED AC-A-001: in docs/a/b.md"])
    assert out[0] == "\x1b[1;31mCoverage check FAILED:\x1b[0m"
    assert "\x1b[36mAC-A-001\x1b[0m" in out[2]


def test_a_planned_step_is_struck_through_and_an_empty_field_is_flagged():
    lines = [
        "UC-A-001: 2 step(s), in diagram order",
        "",
        "STP-A-001  do it",
        "    code     -",
        "STP-A-002  later  (planned)",
        "    code     -",
    ]
    out = ON.trace(lines)
    assert "\x1b[33m-\x1b[0m" in out[3]  # a built step with no code: a warning
    assert "\x1b[2;9m" in out[4]  # planned: struck through
    assert "\x1b[2m-\x1b[0m" in out[5]  # and its empty field is only dim
    assert [ANSI.sub("", x) for x in out] == lines


def test_the_commands_are_plain_by_default_and_styled_only_when_asked(proj: Path, capsys):
    assert cli.main(["new", "uc", "--area", "A", "--title", "Log in"]) == 0
    capsys.readouterr()
    for argv in (["status"], ["next"], ["check"]):
        cli.main(argv)
        plain = capsys.readouterr().out
        assert "\x1b" not in plain  # not a terminal under pytest
        cli.main(["--color", "always", *argv])
        styled = capsys.readouterr().out
        assert "\x1b[" in styled and ANSI.sub("", styled) == plain


def test_json_output_is_never_styled(proj: Path, capsys):
    for argv in (["status", "--json"], ["next", "--json"], ["check", "--json"]):
        cli.main(["--color", "always", *argv])
        assert "\x1b" not in capsys.readouterr().out
