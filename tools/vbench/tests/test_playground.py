"""The playground's own format (the auth app) is read as facts: use cases, requirements, criteria and tagged tests."""

from __future__ import annotations

from vbench.domain.playground import (
    comment_tags,
    parse_criteria,
    parse_requirements,
    parse_use_case,
    python_tests,
)

USE_CASE = """```yaml
id: UC-A1
type: use-case
name: Sign in
status: draft
actor: person (not yet signed in)
context: BC-ACCESS
satisfies:
  - id: NFR-1
  - id: FR-1
criteria:
  - id: AC-1
  - id: AC-33
rules: [RULE-A6, RULE-A7]
objects: [OBJ-A1]
```

# Sign in
"""

REQUIREMENTS = """## Functional requirements

| ID | Name | Statement | Verified by | Release | Built | Status | Objects | Sources |
|---|---|---|---|---|---|---|---|---|
| FR-1 | Sign in | The system shall let a person sign in. | acceptance test | R1 | yes | draft |  | decision 1 |

## Quality

| ID | Kind | Name | Statement | Quality attribute | Stimulus | Environment | Response | Measure | Verified by | Release | Built | Status | Sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NFR-1 | quality | Access is checked | The system shall check access. | Security | A role is refused. | Normal. | Refused. | A test per role. | inspection | R1 | no | draft | north star |
"""

CRITERIA = """| ID | Proves | Given | When | Then | Level | Status | Notes |
|---|---|---|---|---|---|---|---|
| AC-1 | FR-1 | an active account | it signs in | they have a session | acceptance | draft |  |
| AC-43 | FR-1 | a browser with a session | it signs in again | the old session ends | integration | draft | R2 (decision 13) |
| AC-2 | FR-2 | x | y | z | unit | retired |  |
"""


def test_a_use_case_header_gives_its_requirements_criteria_and_context():
    uc = parse_use_case(USE_CASE, "docs/usecases/UC-A1-sign-in.md")
    assert uc is not None
    assert (uc.id, uc.name, uc.context) == ("UC-A1", "Sign in", "BC-ACCESS")
    assert uc.satisfies == ("NFR-1", "FR-1") and uc.criteria == ("AC-1", "AC-33")
    assert uc.rules == ("RULE-A6", "RULE-A7") and uc.objects == ("OBJ-A1",)


def test_a_file_without_a_use_case_header_is_not_a_use_case():
    assert parse_use_case("# Use cases\n\n- a list\n", "docs/usecases/README.md") is None


def test_requirements_are_read_from_the_functional_and_the_quality_table():
    reqs = {r.id: r for r in parse_requirements(REQUIREMENTS)}
    assert set(reqs) == {"FR-1", "NFR-1"}
    assert reqs["FR-1"].kind == "FR" and reqs["FR-1"].name == "Sign in"
    assert reqs["NFR-1"].kind == "NFR" and reqs["NFR-1"].quality == "Security"
    assert reqs["NFR-1"].measure == "A test per role."


def test_criteria_say_what_they_prove_and_when_they_are_deferred_or_retired():
    acs = {c.id: c for c in parse_criteria(CRITERIA)}
    assert acs["AC-1"].proves == ("FR-1",) and acs["AC-1"].level == "acceptance"
    assert acs["AC-1"].text == "Given an active account, when it signs in, then they have a session."
    assert acs["AC-43"].deferred and not acs["AC-1"].deferred
    assert acs["AC-2"].retired


def test_python_tests_carry_the_criteria_of_their_marker():
    src = (
        "import pytest\n\n"
        '@pytest.mark.ac("AC-9")\n@pytest.mark.ac("AC-10")\n'
        'def test_creates():\n    """A project is made."""\n\n'
        "def test_untagged():\n    pass\n"
    )
    tests = {t.name: t for t in python_tests(src, "apps/api/tests/test_x.py")}
    assert tests["test_creates"].acs == ("AC-9", "AC-10") and tests["test_creates"].docstring == "A project is made."
    assert tests["test_untagged"].acs == ()


def test_a_comment_in_a_web_test_names_the_criterion_it_verifies():
    assert comment_tags("// The hexagon holds. Verifies AC-36 (NFR-3).\n") == ("AC-36",)


def test_the_auth_app_exports_the_state_the_dashboard_draws(tmp_path):
    from vbench.adapters.fs import FsWorkspace
    from vbench.app.export_playground import export_playground_state

    def put(rel: str, text: str) -> None:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text)

    put("docs/usecases/UC-A1-sign-in.md", USE_CASE)
    put("docs/requirements/requirements.md", REQUIREMENTS)
    put("docs/requirements/acceptance-criteria.md", CRITERIA)
    put(
        "apps/api/tests/test_a.py",
        'import pytest\n@pytest.mark.ac("AC-1")\ndef test_signs_in():\n    """A session starts."""\n',
    )

    class Repo:
        def branch(self) -> str:
            return "main"

    state = export_playground_state(FsWorkspace(tmp_path), Repo())  # type: ignore[arg-type]
    ac = {c["id"]: c for c in state["criteria"]}
    assert ac["AC-1"]["state"] == "covered" and ac["AC-43"]["state"] == "planned" and "AC-2" not in ac
    assert state["useCases"][0]["id"] == "UC-A1" and state["useCases"][0]["covered"] == 1
    fr = state["requirements"]["functional"][0]
    assert (
        fr["id"] == "FR-1" and fr["label"] == "Proved" and fr["criteria"][0]["tests"][0]["title"] == "A session starts."
    )
    assert {i["phase"] for i in state["v"]["items"]} >= {"requirements", "acceptance"}
