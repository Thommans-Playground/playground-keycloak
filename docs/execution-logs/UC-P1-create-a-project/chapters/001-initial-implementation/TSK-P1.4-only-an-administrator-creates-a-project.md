# Task P1.4: Only an administrator creates a project

**Task ID:** TSK-P1.4 · **Use Case:** UC-P1 · **Criteria:** AC-11, AC-32, AC-94 · **Code matched at:** `7481263`

What this does and why: [summary, task P1.4](summary.md#p14-only-an-administrator-creates-a-project).

Run from `apps/api/`: `uv run pytest tests/test_projects_api.py tests/test_projects_errors.py tests/test_projects_service.py -q`

Work test first in each step: write the test, run it, see it fail, then write the code.

---

## Step 1: the use case refuses (AC-11)

**Test** (Unit):

Two tests in `tests/test_projects_service.py`, each marked `@pytest.mark.ac("AC-11")`:

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-11")
def test_create_refuses_a_caller_who_is_not_an_administrator_and_saves_nothing(service, projects):
    with pytest.raises(NotAnAdministrator):
        service.create(USER, "Alpha", ["acc-maya"])
    assert projects.rows == {}
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-11")
def test_create_checks_the_role_before_the_input(service, projects):
    with pytest.raises(NotAnAdministrator):  # the name and the members are not looked at
        service.create(USER, "", ["", "not-an-account"])
    assert projects.rows == {}
```

**Code**:

The error is final:

```python
# apps/api/app/projects/domain/errors.py
class NotAnAdministrator(ProjectsError):
    code = "forbidden"
```

and the check, as it was written (stage 1 shape, not the final file; the final form is stage 3 of this section):

```python
    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> Project:
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")
        project = Project.create(caller, name, member_ids)
        self._projects.add(project)
        return project
```

**Logic.** The check is the first line of `create`, so nothing after it runs for a non-administrator and nothing is saved.

---

## Step 2: the status, and the API refuses (AC-11, AC-32)

**Test** (Unit and API):

In `tests/test_projects_errors.py`:

```python
# apps/api/tests/test_projects_errors.py
def test_not_an_administrator_is_answered_with_a_403_and_the_forbidden_body():
    app = FastAPI()
    register_error_handlers(app, FakeSecurityLog())

    @app.get("/x")
    def x():
        raise NotAnAdministrator("Administrators only.")

    r = TestClient(app).get("/x")
    assert (r.status_code, r.json()) == (
        403,
        {"detail": {"code": "forbidden", "message": "Administrators only."}},
    )
```

In `tests/test_projects_api.py`, through the HTTP client, with a project count read from the database:

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-11")
@pytest.mark.ac("AC-32")
def test_an_ordinary_user_cannot_create_a_project(api, admin, engine):
    maya_h, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    r = api.post("/projects", headers=maya_h, json={"name": "Alpha", "members": [maya_id]})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 0
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-11")
@pytest.mark.ac("AC-32")
def test_a_member_of_other_projects_is_still_not_an_administrator(api, admin, engine):
    maya_h, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    assert api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]}).status_code == 201
    r = api.post("/projects", headers=maya_h, json={"name": "Beta", "members": [maya_id]})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 1
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-11")
def test_the_role_is_checked_before_the_input(api, admin, engine):
    maya_h, _ = active_user(api, admin, "sub-maya", "maya@x.test")
    r = api.post("/projects", headers=maya_h, json={"name": "", "members": ["not-an-account"]})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 0
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-32")
def test_a_demoted_administrator_is_refused_at_once(api, admin, engine):
    """The role is read on every request, not taken from the token (AC-32: the server decides, not the screen)."""
    bo_h, bo_id = active_user(api, admin, "sub-bo", "bo@x.test")
    assert api.post(f"/accounts/{bo_id}/promote", headers=admin, json={"reason": "Covers"}).status_code == 200
    assert api.post("/projects", headers=bo_h, json={"name": "Alpha", "members": []}).status_code == 201
    assert api.post(f"/accounts/{bo_id}/demote", headers=admin, json={"reason": "Back"}).status_code == 200
    r = api.post("/projects", headers=bo_h, json={"name": "Beta", "members": []})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 1
```

**Code**:

```python
# apps/api/app/projects/adapters/inbound/errors.py, HTTP_STATUS (the table holds more entries since)
HTTP_STATUS: dict[type[ProjectsError], int] = {
    NotAnAdministrator: 403,
    InvalidProjectName: 422,
    InvalidRequest: 422,
    MemberNotEligible: 422,
    ProjectNotFound: 404,
}
```

At this task the table was `{NotAnAdministrator: 403}`; the other four entries come from TSK-P1.5, P1.6 and UC-P3.

**Logic.** One entry maps the error to 403. The shared handler writes the body `{"detail": {"code", "message"}}`.

---

## Step 3: every project route passes the guard chain (AC-94)

**Test** (API):

```python
# apps/api/tests/test_projects_api.py
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

It builds a pending account and a deactivated one, takes every route of the app whose path is `/projects` or starts with
`/projects/`, replaces `{project_id}` with a UUID, and for each method sends it four times: no token and a bad token (401),
the pending account (403 `account_pending`), the deactivated one (403 `account_deactivated`). It asserts the table is not
empty, so a rename cannot make it pass on nothing.

**Code**:

No new code. The route depends on Access's `guards.active_account`, wired in TSK-P1.3. The check today is a method the route
can call before it reads the body (TSK-P1.5, AC-93), and `create` calls it first. Quoted from the file; the class holds more since:

```python
# apps/api/app/projects/application/service.py, ProjectsService
    @staticmethod
    def authorise_creation(caller: Caller) -> None:
        """Only an administrator creates a project. The route calls it before it reads the body (AC-11, AC-93)."""
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")
```

```python
# apps/api/app/projects/application/service.py, ProjectsService
    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> ProjectView:
        """Create a project with its first members (AC-9, AC-10). Only an administrator may, and that is checked
        before the input is (AC-11, AC-32); then the name and the cap on first members are (AC-12, AC-91, AC-92); then that every person named has an
        active account (AC-13), each counted once (AC-89). The audit entry is written after saving, in the request's own
        transaction, and only when the project was created (AC-29)."""
        self.authorise_creation(caller)
        project = Project.create(caller, name, member_ids)
        named = set(project.members)  # each person once (AC-89)
        if named and not named <= self._accounts.active_among(named):
            raise MemberNotEligible  # pending, deactivated or unknown: one answer (AC-13)
        self._projects.add(project)
        self._audit.record(
            ProjectEvent(
                "create_project",
                caller.account_id,
                project.id,
                project.name,
                tuple(m.account_id for m in project.memberships),
            )
        )
        return self._view(project)
```

The rest of `create` is the work of TSK-P1.5 to P1.7. The route calls `svc.authorise_creation(who)` before it validates the
body; that line is shown in the route block of TSK-P1.3.

**Logic.** The guard chain answers for a missing, bad, pending or deactivated caller before any Projects code runs. The use case
answers for an active caller who is not an administrator.
