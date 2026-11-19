# 0005 Tests name the criterion or rule they prove

- Status: accepted
- Date: 2026-11-19
- Decided by: together

## Context
The traceability tool found tags by searching text. A comment tag cannot be selected by pytest, and a list of ids in one comment was read as one.

## Decision
In pytest a test carries one marker for each criterion or rule (ac and rule markers, for example ac("AC-6")), and a hook adds a mark such as AC_6, so pytest -m AC_6 runs them. In the web tests the id sits in the test name, as (Verifies AC-6). at_tool.py reads both forms.

## Consequences
The tag is only a claim. It does not prove the test checks the criterion, and the tool does not read test results yet. The review of the process of 19 Nov 2026 lists the known gaps (stamp bug, tags in comments, false tags).

## Links
decision 11; .claude/skills/_vbench/standards/naming-conventions.md section 6; apps/api/tests/conftest.py.
