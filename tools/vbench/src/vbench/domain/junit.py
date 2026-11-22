"""What a test run recorded, read from a JUnit XML file (`pytest --junitxml=reports/junit.xml`).

The text of a test file cannot say whether pytest ran a test, skipped it (an `importorskip` of a module that is
not there, a deselection) or saw it fail. The run can. With `results = "<file>"` in the config, a test counts toward
a gate only when the run says it passed. Every parametrised case must pass, and a test the run does not mention did not
run. Stdlib only; a file that does not parse proves nothing.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

PARAMS = re.compile(r"\[.*\]$")


@dataclass(frozen=True)
class Run:
    """The cases of one recorded run: (classname, test name without its parameters) -> every outcome seen."""

    path: str = ""
    found: bool = False
    cases: dict[tuple[str, str], list[str]] = field(default_factory=dict)

    def outcome(self, test_file: str, name: str) -> str:
        """`passed`, or why the test does not count: `failed`, `skipped`, `not run`, or no results file."""
        if not self.found:
            return f"no results file at {self.path}"
        module = test_file.removesuffix(".py").replace("/", ".")
        seen = [
            o for (cls, test), outs in self.cases.items() if test == name and _same_module(module, cls) for o in outs
        ]
        if not seen:
            return "not run"
        if "failed" in seen:
            return "failed"
        return "skipped" if "skipped" in seen else "passed"


def _same_module(module: str, classname: str) -> bool:
    """`tests.test_thing` matches `tests.test_thing`, `tests.test_thing.TestIt` and `test_thing` (run inside tests/)."""
    parts = classname.split(".")
    for k in range(len(parts), 0, -1):
        prefix = ".".join(parts[:k])
        if module == prefix or module.endswith("." + prefix):
            return True
    return False


def read_run(path: str, text: str | None) -> Run:
    """`text` is the file's contents, None when there is no such file."""
    if not path:
        return Run()
    if text is None:
        return Run(path, False)
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return Run(path, False)
    cases: dict[tuple[str, str], list[str]] = {}
    for case in root.iter("testcase"):
        kids = {child.tag for child in case}
        outcome = "failed" if kids & {"failure", "error"} else "skipped" if "skipped" in kids else "passed"
        key = (case.get("classname", ""), PARAMS.sub("", case.get("name", "")))
        cases.setdefault(key, []).append(outcome)
    return Run(path, True, cases)
