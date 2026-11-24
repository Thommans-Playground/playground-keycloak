# TSK-P1.6: first members need an active account, each counted once

AC-13, AC-89 · plan status: **draft, not reviewed** · matches the code at `7481263`

Ground rules, the layout and the commands are in the [chapter summary](summary.md). This task needs TSK-P1.1 (Access
answers which accounts are active among some ids) and TSK-P1.3 (the project is created).

This is the plan someone follows to build this task. It was written by working backwards from the code that exists, so
its final code is that code: each block marked `# file` is a copy of that file at the commit above.

## 1. What we are building, and why

Creating a project may name first members. Each must be a person with an active account, and each is one member however
often they are named.

| AC | Given | Then | Why |
|---|---|---|---|
| AC-13 | an administrator names a first member who is not active or does not exist | it is refused, with one answer for an account that cannot be a member | A pending, a deactivated and an unknown account get the same answer, so the refusal cannot be used to find out which ids exist or in what state (FR-7). |
| AC-89 | an administrator names the same active account twice | the project has that person once | First members are de-duplicated before anything is written, so the project has one membership and, once TSK-P1.7 is built, one audit entry that names them once (FR-7). |

## 2. The logic

1. **Projects asks, Access answers, and Projects never imports Access.** Projects declares its own port,
   `AccountStatus.active_among(ids)`; a bridge in `composition/` answers it by calling Access's own use case (ADR 0002,
   0010, 0015). An architecture test fails if Projects imports another context.
2. **One question for all the people named,** not one for each: the ids are asked in one call (no N+1).
3. **Each person once.** The ids are already de-duplicated by `Project.create` (`dict.fromkeys`, TSK-P1.3), so the
   service asks about `set(project.members)` and Access is asked about each id once (AC-89). This task adds the test that
   pins it, not new de-duplication code.
4. **One answer for every reason.** `MemberNotEligible` carries a fixed message and names no id and no status (AC-13).
5. **One bad person refuses everyone.** The check is before the save, so nothing is written, not even the project.
6. **Order of the refusals:** the role first, then the name and the cap (rules in the domain, no lookup), then the
   eligibility. A request that is already refused for a cheaper reason never asks Access (AC-11, AC-12, AC-92).
7. **No names, no list:** an empty list of first members asks nobody.

**Where it lives:** the port in `application/ports.py`, the check in `ProjectsService.create`, the error in
`domain/errors.py`, the status in `adapters/inbound/errors.py`, and the bridge in `composition/bridges.py`, the one place
that sees both Access and Projects.

Known gap, accepted in the commit message: there is no lock between the check and the save, so a person deactivated in
that gap could still become a member.

## 3. The plan

Three stages. Each starts from a test.

### Stage 1: the use case refuses an inactive first member (AC-13, AC-89)

**1a. Write the tests.** First, a fake for the port in `tests/fakes.py`, so the use case can be tested with no Access:

```python
# tests/fakes.py
class FakeAccountStatus:
    """Stands in for Projects' AccountStatus port. `active=None` means every id is an active account."""

    def __init__(self, active: set[str] | None = None):
        self.active = active
        self.asked: list[set[str]] = []

    def active_among(self, ids):
        self.asked.append(set(ids))
        return set(ids) if self.active is None else set(ids) & self.active
```

Then in `tests/test_projects_service.py`, with a helper `service_with(active)` that builds
`ProjectsService(projects, status)` over `FakeProjects()` and `FakeAccountStatus(set(active))`:

- `@pytest.mark.ac("AC-13")`: for each of `acc-pending`, `acc-deactivated`, `acc-unknown` (none in the active set):
  `create` raises `MemberNotEligible`, its code is `member_not_eligible`, its message is the one fixed text and does not
  contain the id, and nothing is saved
- `@pytest.mark.ac("AC-13")`: `["acc-maya", "acc-gone", "acc-bob"]` with only maya and bob active: refused, nothing saved
- `@pytest.mark.ac("AC-13")`: the order: a non administrator is refused `NotAnAdministrator`, an empty name
  `InvalidProjectName`, 51 ids `InvalidRequest`, and in all three `status.asked == []`
- `@pytest.mark.ac("AC-89")`: `["acc-maya", "acc-maya"]` makes one membership, and `status.asked == [{"acc-maya"}]`
- `@pytest.mark.ac("AC-13")`: no first members is accepted and asks nobody

The existing `ProjectsService(...)` calls in `tests/test_projects_service.py` and `tests/test_projects_input.py` now pass
`FakeAccountStatus()` as the second argument.

**1b. Name the error.** Add to `app/projects/domain/errors.py` (the final text, below):

```python
# app/projects/domain/errors.py
class MemberNotEligible(ProjectsError):
    """One answer for a first member who is pending, deactivated or unknown: it names no id and no status (AC-13)."""

    code = "member_not_eligible"

    def __init__(self):
        super().__init__("That person cannot be added to or removed from this project.")
```

Run `uv run pytest tests/test_projects_service.py tests/test_projects_input.py -q`. **Expect** every test that builds the
service to fail with `TypeError: ProjectsService.__init__() takes 2 positional arguments but 3 were given` (checked at
`c5c6f64`, test files from that commit on the code of `9e96f0c`, with the error added).

**1c. Declare the port and use it.** Add the port to `app/projects/application/ports.py`:

```python
# app/projects/application/ports.py
class AccountStatus(Protocol):
    def active_among(self, ids: set[str]) -> set[str]:
        """Of these account ids, the ones whose people may be members."""
        ...
```

Give `ProjectsService` the port as its second argument (`self._accounts = accounts`; the constructor today also takes the
audit and people ports, from TSK-P1.7), and add the check to `create`, after `Project.create` has applied the name and
the cap. These are the lines this task adds to `ProjectsService.create`:

```python
# app/projects/application/service.py, inside ProjectsService.create
        project = Project.create(caller, name, member_ids)
        named = set(project.members)  # each person once (AC-89)
        if named and not named <= self._accounts.active_among(named):
            raise MemberNotEligible  # pending, deactivated or unknown: one answer (AC-13)
        self._projects.add(project)
```

**Expect** `37 passed` for `tests/test_projects_service.py` and `tests/test_projects_input.py` together (checked at
`c5c6f64`).

### Stage 2: Access answers the port (AC-13)

**2a. Write the bridge test** in `tests/test_projects_composition.py`, `@pytest.mark.ac("AC-13")`: build an
`AccessService` over fakes holding one active, one pending and one deactivated account, wrap it in `AccountStatusBridge`,
and assert `active_among({"a", "p", "d", "unknown"}) == {"a"}`, `active_among(set()) == set()`, and that the answer is a
`set`.

And an architecture test in `tests/test_architecture.py`,
`test_projects_imports_no_other_context_only_composition_sees_both`: no file of `app/projects/` imports another context,
`projects/application/ports.py` imports nothing from `app.access`, and `composition/bridges.py` does import it.

Run `uv run pytest tests -q -m "AC_13 or AC_89"`. **Expect** `4 failed, 7 passed` (checked at `c5c6f64`: the three
HTTP tests of stage 3, which build the app, and the bridge test).

**2b. Write the bridge.** Add to `app/composition/bridges.py`:

```python
# app/composition/bridges.py
class AccountStatusBridge:
    """Projects' AccountStatus port, answered by Access's use case, on the same session as the request."""

    def __init__(self, access: AccessService):
        self._access = access

    def active_among(self, ids: set[str]) -> set[str]:
        return set(self._access.active_among(list(ids)))
```

with `from app.access.application.service import AccessService` at the top. `AccessService.active_among` is TSK-P1.1. It
uses the account's own `is_active` rule, so "active" means the same here as everywhere.

**Expect** `3 failed, 8 passed` (checked): the bridge test now passes, the three HTTP tests still fail because the app
does not use it.

### Stage 3: wire it and answer 422 (AC-13, AC-89)

**3a. The HTTP tests** in `tests/test_projects_api.py`, over the real app and database, with `active_user(...)` and
`register(...)` helpers that approve or leave an account pending:

- `@pytest.mark.ac("AC-13")`: a pending, a deactivated (`POST /accounts/<id>/deactivate`) and a made-up UUID, each named
  as the one first member: all three answer 422 with `{"detail": {"code": "member_not_eligible", "message": ...}}` and
  the same body, the id is not in the answer, and no project exists
- `@pytest.mark.ac("AC-13")`: one active and one pending: refused, no project and no row in `memberships`
- `@pytest.mark.ac("AC-89")`: the same active person twice: 201, one member in the answer, one row in `memberships`

The 51-member test of TSK-P1.5 changes to register 51 real active accounts, because from now on the ids are looked up.

**3b. Wire the bridge.** In `app/composition/app.py` the service of a request is built over the request's own session
and Access service, so the check and the save are in one transaction. This is the function at the commit above; its
audit and people arguments were added by TSK-P1.7, and the one this task adds is `AccountStatusBridge(access)`:

```python
# app/composition/app.py, projects_service (inside create_app)
    def projects_service(
        session: Session = Depends(db),
        access: AccessService = Depends(service),
        audit: AuditService = Depends(audit_service),
    ) -> ProjectsService:
        # the request's session, so the project, its members and its audit entry commit together
        people = PeopleBridge(access)
        return ProjectsService(
            SqlProjects(session), AccountStatusBridge(access), ProjectsAuditBridge(audit, people), people
        )
```

**3c. Map the error to 422.** In `app/projects/adapters/inbound/errors.py` the status map gets
`MemberNotEligible: 422` (it sits beside the entries of TSK-P1.5 and later tasks). Without it the answer is 400.

**Expect** after 3b, with the wiring but no status entry yet: `2 failed, 9 passed` (checked: the two refusal tests fail; that the status is then the default 400 is read from the code, not observed). Then add 3c, and `11 passed` for `-m "AC_13 or AC_89"` (checked at `c5c6f64`).

## 4. Check it yourself

From `apps/api/`:

```
uv run pytest tests/test_projects_service.py tests/test_projects_composition.py -q   # 68 passed (these also hold TSK-P1.7 tests)
uv run pytest tests -q -m AC_13                                                       # 9 passed
uv run pytest tests -q -m AC_89                                                       # 4 passed (the audit tests of TSK-P1.7 carry AC-89 too)
uv run pytest tests/test_architecture.py -q                                           # 21 passed
uv run pytest -q                                                                      # 468 passed, 47 skipped (PostgreSQL ones)
```

All checked at `7481263`. At `c5c6f64`, the commit that built this task, the whole suite was `281 passed, 46 skipped`
(checked); its message reports 327 on PostgreSQL, which was not repeated (no `TEST_DATABASE_URL`).

## 5. Where this leaves things

- Source: `app/projects/domain/errors.py`, `app/projects/application/ports.py`, `app/projects/application/service.py`,
  `app/projects/adapters/inbound/errors.py`, `app/composition/bridges.py`, `app/composition/app.py`
- Tests: `tests/test_projects_service.py`, `tests/test_projects_api.py`, `tests/test_projects_composition.py`,
  `tests/test_architecture.py`, with the fake in `tests/fakes.py`
- ADR: none new; 0002, 0010 and 0015 decide the shape.

## Where the real build differs

- The message of `MemberNotEligible` was `"A first member cannot be added."` when this task was built. Commit `643d61d`
  (UC-P2) worded it to fit an add and a removal, and the tests now expect the new text; the plan ends on the code that
  exists. The Expect lines above were checked with the original text.
- De-duplication was not built here: `dict.fromkeys` was already in `Project.create` from TSK-P1.3. This task added the
  tests for AC-89 and the guarantee that Access is asked once for each id.
- `ProjectsService` has four constructor arguments now (TSK-P1.7 added the audit and people ports), so the tests build it
  with `FakeProjectsAudit()` and `FakePeople()` too.
- The counts for `-m AC_13` and `-m AC_89` at `7481263` include tests added by later tasks that carry the same marker.

## Review

Not reviewed. Write `Reviewed by <name> at <hash>` here when the plan has been read against the code.
