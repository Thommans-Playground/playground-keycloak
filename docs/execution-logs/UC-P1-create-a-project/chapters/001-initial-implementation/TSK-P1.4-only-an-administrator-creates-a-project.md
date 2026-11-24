# TSK-P1.4: only an administrator creates a project

AC-11, AC-32, AC-94 · plan status: **draft, not reviewed** · matches the code at `7481263`

Ground rules, the layout and the commands are in the [chapter summary](summary.md).

This is the plan someone follows to build this task. It was written by working backwards from the code that exists, so
its final code is that code: each block marked `# file` is a copy of that file at the commit above. Where the file has
grown since (later tasks added to it), only what this task adds is quoted, and the text says so.

## 1. What we are building, and why

[TSK-P1.3](TSK-P1.3-an-administrator-creates-a-project.md) lets anyone who passes the guard chain create a project.
This task makes the server refuse everyone who is not an administrator, and proves that every route under `/projects`
sits behind the guard chain.

| AC | Given | Then | Why |
|---|---|---|---|
| AC-11 | a user who is not an administrator | they try to create a project; it is refused | Creating a project is an administrator's act (decision 13). The refusal is a 403 `forbidden`, nothing is written, and the name and members are not looked at. |
| AC-32 | a caller who may not make a project command (a user, or a member who is not an administrator), even if the screen hides the button | they make it; the server refuses it and nothing is created or changed | The screen is a courtesy, the server decides (NFR-1). Here the command is create; the add and remove commands are proven by UC-P2, under the same criterion. |
| AC-94 | a request with no token, a pending account, a deactivated account | each makes a request to every `/projects` route, with an id of a project that exists | Each is refused (401 or 403) before the project is looked at, and the answer shows nothing about the project. A route a later slice adds under `/projects` without the guard chain must fail a test. **Met in part here:** the walk test in this task uses a random UUID for a project that does not exist, and does not check that the answer hides the project. The cases with a real project id are the later tests named in stage 3a. |

## 2. The logic

1. **The role check is the first thing `create` does** (AC-11). It runs before the name and members are looked at, so a
   non-administrator learns nothing about what is valid and nothing can be written. The order is decision 14.
2. **The rule is in the use case, not the route.** `Caller.is_administrator` is a fact the composition root reads from
   the account on every request, so a demoted administrator is refused at once, and a token that still says
   "administrator" proves nothing (AC-32). The route only maps the refusal to a status.
3. **One error, one answer.** `NotAnAdministrator`, code `forbidden`, status 403, a fixed message that repeats nothing the
   caller sent.
4. **Being a member of other projects is not a role.** A member who is not an administrator is refused the same way
   (AC-32). There are two roles and no project roles (decision 13).
5. **The guard chain is not repeated in Projects.** The route depends on `guards.active_account` (Access's chain), so
   401, `account_pending` and `account_deactivated` come from it before any Projects code (AC-94). The test walks the
   route table instead of naming routes, so a route added later is covered with no edit.

**Where it lives:** the error in `domain/errors.py`; the check in `ProjectsService`; the status in
`adapters/inbound/errors.py` (`HTTP_STATUS`); the guard dependency in `composition/app.py`, built in TSK-P1.3. The walk
test is in `tests/test_projects_api.py`.

## 3. The plan

Three stages. Run the commands from `apps/api/`.

### Stage 1: the use case refuses (AC-11)

**1a. Write the tests** in `tests/test_projects_service.py`, each marked `@pytest.mark.ac("AC-11")`:

- `create` with a caller who is not an administrator raises `NotAnAdministrator` and the repository holds nothing
- the role is checked before the input: `create(USER, "", ["", "not-an-account"])` raises `NotAnAdministrator`, not a
  rule about the name

Run `uv run pytest tests/test_projects_service.py -q -x`. **Expect** a collection error, `NotAnAdministrator` does not
exist (checked).

**1b. Add the error and the check.** The error is final:

```python
# app/projects/domain/errors.py, NotAnAdministrator
class NotAnAdministrator(ProjectsError):
    code = "forbidden"
```

and the check, as it was written (stage shape, not the final file; the final form is stage 3):

```python
    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> Project:
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")
        project = Project.create(caller, name, member_ids)
        self._projects.add(project)
        return project
```

**Expect** the two new service tests to pass (checked, as part of `18 passed` for the three files of stage 2).

### Stage 2: the status, and the API refuses (AC-11, AC-32)

**2a. Write the tests.**

In `tests/test_projects_errors.py`: `NotAnAdministrator("Administrators only.")` is answered
`403 {"detail": {"code": "forbidden", "message": "Administrators only."}}`.

In `tests/test_projects_api.py`, through the HTTP client, with a project count read from the database:

- an ordinary active user posts to `/projects`: 403 `forbidden`, no project exists (`AC-11`, `AC-32`)
- a user who is a member of another project is refused the same way, and the count stays at 1 (`AC-11`, `AC-32`)
- the role is checked before the input: a user posting `{"name": "", "members": ["not-an-account"]}` gets 403, not 422
  (`AC-11`)
- a demoted administrator is refused at once: promote a user, create a project (201), demote them, post again: 403, the
  count stays at 1 (`AC-32`). It proves the role is read on every request.

Run `uv run pytest tests/test_projects_api.py tests/test_projects_errors.py tests/test_projects_service.py -q`.
**Expect** a collection error in the errors and service files, and in the API file `4 failed, 7 passed`: the four new
tests fail (the answer is 201), the TSK-P1.3 tests still pass (checked).

**2b. Map the error to its status:**

```python
# app/projects/adapters/inbound/errors.py, HTTP_STATUS (the table holds more entries since)
HTTP_STATUS: dict[type[ProjectsError], int] = {
    NotAnAdministrator: 403,
    InvalidProjectName: 422,
    InvalidRequest: 422,
    MemberNotEligible: 422,
    ProjectNotFound: 404,
}
```

At this task the table was `{NotAnAdministrator: 403}`; the other four entries come from TSK-P1.5, P1.6 and UC-P3.

**Expect** `18 passed` for the three files (checked).

### Stage 3: every project route passes the guard chain (AC-94)

**3a. Write the test** in `tests/test_projects_api.py`, marked `@pytest.mark.ac("AC-94")`. It builds a pending account
and a deactivated one, takes every route of the app whose path is `/projects` or starts with `/projects/`, replaces
`{project_id}` with a UUID, and for each method sends it four times: no token and a bad token (401), the pending
account (403 `account_pending`), the deactivated one (403 `account_deactivated`). It asserts the table is not empty, so
a rename cannot make it pass on nothing.

The `{project_id}` it sends is a random UUID, so no project exists behind it: the test proves that the guard chain
answers first on every route, but not the AC's "a project that exists" or "shows nothing about the project". Those are
proved by two later tests that create real projects: `test_the_read_routes_are_behind_the_guard_chain_before_the_project_is_looked_at`
in `tests/test_projects_read_api.py` (`GET /projects` and `GET /projects/{id}`) and
`test_the_member_routes_are_behind_the_guard_chain_before_the_project_is_looked_at` in `tests/test_projects_members_api.py`
(the add and remove routes). Both try only no token and a pending account, not a bad token or a deactivated account.

```python
# tests/test_projects_api.py
@pytest.mark.ac("AC-94")
def test_every_projects_route_passes_the_guard_chain(api, admin):
    """Walks the route table, so a route a later slice adds under /projects is covered with no edit here."""
    pending, _ = register(api, "sub-new", "new@x.test")
    gone, gone_id = active_user(api, admin, "sub-gone", "gone@x.test")
    assert api.post(f"/accounts/{gone_id}/deactivate", headers=admin, json={"reason": "Left"}).status_code == 200
    bad = {"Authorization": "Bearer not-a-token"}
    routes = [r for r in _api_routes(api.app) if r.path == "/projects" or r.path.startswith("/projects/")]
    assert len(routes) >= 1, "the table must really cover the routes"
    for route in routes:
        path = route.path.replace("{project_id}", str(uuid.uuid4()))
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            body = {"json": {"name": "Alpha", "members": [], "reason": "a reason"}} if method != "GET" else {}
            expected = {
                "no token": ({}, 401, None),
                "bad token": (bad, 401, None),
                "pending": (pending, 403, "account_pending"),
                "deactivated": (gone, 403, "account_deactivated"),
            }
            for who, (headers, status, code) in expected.items():
                r = api.request(method, path, headers=headers, **body)
                assert r.status_code == status, f"{who}: {method} {route.path}"
                if code:
                    assert r.json()["detail"]["code"] == code, f"{who}: {method} {route.path}"
```

Run it. **Expect** it to pass at once (checked: `11 passed` in the API file), because the guard dependency was wired in
TSK-P1.3. This test is a guard for the routes to come, not a driver of new code here. The commit message says an
unguarded test route made it fail; that was **not run** for this plan.

**3b. Final code of the check.** `ProjectsService` today holds the check as a method the route can call before it reads
the body (TSK-P1.5, AC-93), and `create` calls it first. Quoted from the file; the class holds more since:

```python
# app/projects/application/service.py, ProjectsService
    @staticmethod
    def authorise_creation(caller: Caller) -> None:
        """Only an administrator creates a project. The route calls it before it reads the body (AC-11, AC-93)."""
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")

    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> ProjectView:
        """Create a project with its first members (AC-9, AC-10). Only an administrator may, and that is checked
        before the input is (AC-11, AC-32); then the name and the cap on first members are (AC-12, AC-91, AC-92); then that every person named has an
        active account (AC-13), each counted once (AC-89). The audit entry is written after saving, in the request's own
        transaction, and only when the project was created (AC-29)."""
        self.authorise_creation(caller)
```

The rest of `create` is the work of TSK-P1.5 to P1.7. The route calls `svc.authorise_creation(who)` before it validates
the body; that line is shown in the route block of TSK-P1.3.

## 4. Check it yourself

```
uv run pytest -m "AC_11 or AC_32 or AC_94" -q   # 15 passed at the code in the header (checked); 7 at the commit that built this task
uv run pytest tests/test_projects_api.py tests/test_projects_service.py tests/test_projects_errors.py -q
uv run pytest tests/test_architecture.py -q     # 20 passed at the commit that built this task (checked)
uv run pytest -q                                 # 468 passed, 47 skipped at the code in the header (checked)
```

At the commit that built this task the whole suite was `227 passed, 46 skipped` on SQLite (checked) and 273 on
PostgreSQL (the commit's message; not run here, `TEST_DATABASE_URL` is not set).

## 5. Where this leaves things

- Source: `app/projects/domain/errors.py`, `app/projects/application/service.py`, `app/projects/adapters/inbound/errors.py`
- Tests: `tests/test_projects_service.py`, `tests/test_projects_errors.py`, `tests/test_projects_api.py`
- ADR: [0015](../../../../adr/0015-projects-context-build-plan.md) (the walk test is its "Tests" line). No new ADR.
- Not here: the security log line for a refusal (TSK-P1.7, AC-48). At this task a 403 writes nothing to the log.
- Not proved here: AC-32 for add and remove a member, and AC-94 for the member routes' own cases. The walk test covers
  their routes once they exist; their own refusals are tests of UC-P2.

## Where the real build differs

- One commit, `5f3ecff`, built the three stages. The role check was in `create` only; the route calling
  `authorise_creation` before it reads the body arrived with TSK-P1.5 (AC-93), and `create` returns a `ProjectView`
  since ADR 0016. The quoted `create` is today's, with the later checks left out.
- AC-94 passed the first time it ran. The guard chain was already on the route from TSK-P1.3; this task adds the test
  that keeps it so. Two later tests repeat the idea with a real project id for the read routes and the member routes
  (`test_projects_read_api.py`, `test_projects_members_api.py`), for no token and a pending account only; the walk here
  covers every route and all four cases, but with an id that matches no project.
- The `HTTP_STATUS` table at the commit had one entry; the block above is today's.

## Review

Not reviewed. Write `Reviewed by <name> at <hash>` here when the plan has been read against the code.
