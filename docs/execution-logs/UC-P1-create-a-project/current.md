# UC-P1 today

Written at commit `7481263`. Only the part covered by a written chapter is described here; the rest of UC-P1 is in the
use case file until its steps are written up.

## The project name rule (chapter 001, step 001)

- A name is trimmed, then must be 1 to 100 Unicode characters, with no control character and no bidirectional mark.
- The rule is `clean_name` in `apps/api/app/projects/domain/name.py`. It is pure: no HTTP, no framework.
- `Project.create` calls it first, and also caps distinct first members at 50 (`apps/api/app/projects/domain/project.py`).
- The error message never repeats the name.
- Tests: `apps/api/tests/test_projects_input.py` (10 tests, 25 cases with the parameters), marked AC-12, AC-91, AC-92.

## Known limits

- The HTTP side of these rules (422 body shape, unknown fields refused) is slice TSK-P1.5 too, but not written up yet.
