# Task P1.7: Audit a project creation, and log every refusal

**Task ID:** TSK-P1.7 · **Use Case:** UC-P1 · **Criteria:** AC-29, AC-48 (the refused-request line only: the sign-in and session lines of AC-48 are not this task's). The same commit also proves AC-85 and AC-89 · **Code matched at:** `7481263`

What this does and why: [summary, task P1.7](summary.md#p17-audit-a-project-creation-and-log-every-refusal).

Run from `apps/api/`: `uv run pytest tests/fakes.py tests/test_projects_audit_api.py tests/test_projects_composition.py tests/test_projects_service.py -q`

Work test first in each step: write the test, run it, see it fail, then write the code.

---

## Step 1: the service writes the event (AC-29, AC-89)

**Test** (Unit):

A fake `FakeProjectsAudit` in `tests/fakes.py` keeps the events and what the repository held when each came:

```python
# apps/api/tests/fakes.py
class FakeProjectsAudit:
    """Stands in for Projects' AuditLog port: keeps the events, and what the repository held when each came."""

    def __init__(self, projects=None):
        self.events: list = []
        self.held_when_recorded: list = []
        self._projects = projects

    def record(self, event):
        self.events.append(event)
        if self._projects is not None:
            self.held_when_recorded.append(self._projects.by_id(event.project_id))
```

Then the tests in `tests/test_projects_service.py`:

```python
# apps/api/tests/test_projects_service.py
def audited(active=None):
    projects = FakeProjects()
    audit = FakeProjectsAudit(projects)
    return ProjectsService(projects, FakeAccountStatus(active), audit, FakePeople()), projects, audit
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-29")
def test_create_writes_one_event_with_the_actor_the_project_and_the_first_members():
    service, _, audit = audited()
    p = service.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    assert audit.events == [ProjectEvent("create_project", "acc-ada", p.id, "Alpha", ("acc-maya", "acc-bob"))]
    assert audit.events[0].reason is None
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-29")
def test_the_event_is_written_after_the_project_is_saved_and_carries_the_trimmed_name():
    service, _, audit = audited()
    p = service.create(ADMIN, "  Alpha  ", [])
    assert audit.held_when_recorded == [p.project]
    assert (audit.events[0].project_name, audit.events[0].member_ids) == ("Alpha", ())
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-89")
def test_a_person_named_twice_is_in_the_event_once():
    service, _, audit = audited()
    service.create(ADMIN, "Alpha", ["acc-maya", "acc-maya", "acc-bob"])
    assert audit.events[0].member_ids == ("acc-maya", "acc-bob")
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-29")
@pytest.mark.parametrize(
    "caller,name,members",
    [
        (USER, "Alpha", []),
        (ADMIN, "", []),
        (ADMIN, "Alpha", [f"acc-{i}" for i in range(51)]),
        (ADMIN, "Alpha", ["acc-gone"]),
    ],
)
def test_a_refused_creation_writes_no_event(caller, name, members):
    service, projects, audit = audited(active={"acc-maya"})
    with pytest.raises(Exception):  # noqa: B017 - which refusal is proven in the tests above
        service.create(caller, name, members)
    assert audit.events == [] and projects.rows == {}
```

Every place that builds `ProjectsService` now passes the fake as a third argument, so the existing tests in
`tests/test_projects_input.py` and `tests/test_projects_service.py` change by that one argument.

**Code**:

The event and the port in `app/projects/application/ports.py`, an `audit: AuditLog` argument to `ProjectsService.__init__`
(stored as `self._audit`), and the call in `create`. This is where the final code is; the `People` port follows in stage 2 and
the `SecurityLog` port in stage 4.

```python
# apps/api/app/projects/application/ports.py
@dataclass(frozen=True)
class ProjectEvent:
    """What happened to a project, in Projects' words: ids only, the names are looked up when it is written."""

    action: str  # create_project, add_member or remove_member
    actor_id: str
    project_id: str
    project_name: str
    member_ids: tuple[str, ...] = ()  # the first members, each once, or the one member of a change
    reason: str | None = None  # none for a creation
```

```python
# apps/api/app/projects/application/ports.py
class AuditLog(Protocol):
    def record(self, event: ProjectEvent) -> None:
        """Write one entry in the trail, in the request's own transaction."""
        ...
```

The constructor, as it is now (it also takes `people` since UC-P3):

```python
# apps/api/app/projects/application/service.py, ProjectsService.__init__
    def __init__(self, projects: ProjectRepository, accounts: AccountStatus, audit: AuditLog, people: People):
        self._projects = projects
        self._accounts = accounts
        self._audit = audit
        self._people = people
```

The call in `ProjectsService.create` (the method today; the view it returns is from UC-P3):

```python
# apps/api/app/projects/application/service.py, ProjectsService.create
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

**Logic.** The entry is written after the project is saved and only on the success path, so every refusal before it writes nothing. Projects
speaks in ids: the names are looked up later, by the bridge. The members come from the saved project, so each is in the event once (AC-89).

---

## Step 2: the bridges (AC-29)

**Test** (Unit):

A fake `FakePeople` in `tests/fakes.py` answers `names_of` from a dict and leaves out unknown ids:

```python
# apps/api/tests/fakes.py
class FakePeople:
    """Stands in for Projects' People port: {id: (name, email)} for the known ids, nothing for the others."""

    def __init__(self, known: dict[str, tuple[str, str]] | None = None):
        self.known = known or {}
        self.asked: list[set[str]] = []

    def names_of(self, ids):
        self.asked.append(set(ids))
        return {i: self.known[i] for i in ids if i in self.known}
```

Then the tests in `tests/test_projects_composition.py`, each marked `@pytest.mark.ac("AC-29")`:

```python
# apps/api/tests/test_projects_composition.py
def access_with(*people):
    from app.access.application.service import AccessService
    from tests.fakes import FakeAccounts, FakeAudit, FakeIdp, FakeUnitOfWork

    accounts = FakeAccounts()
    for acc_id, name, email in people:
        accounts.add(
            Account(acc_id, f"sub-{acc_id}", name, email, Role.user, Status.active, datetime(2026, 1, 1), None)
        )
    return AccessService(accounts, FakeAudit(), FakeIdp(), set(), uow=FakeUnitOfWork())
```

```python
# apps/api/tests/test_projects_composition.py
@pytest.mark.ac("AC-29")
def test_the_people_bridge_answers_through_accesss_people_and_leaves_out_the_unknown():
    from app.composition.bridges import PeopleBridge

    bridge = PeopleBridge(access_with(("a", "Ada", "ada@x.test"), ("m", "Maya", "maya@x.test")))
    assert bridge.names_of(["a", "m", "ghost"]) == {"a": ("Ada", "ada@x.test"), "m": ("Maya", "maya@x.test")}
    assert bridge.names_of([]) == {}
```

```python
# apps/api/tests/test_projects_composition.py
@pytest.mark.ac("AC-29")
def test_the_audit_bridge_turns_a_project_event_into_a_project_entry_with_the_names_now():
    from app.audit.application.service import AuditService
    from app.audit.domain.entry import Kind, Person
    from app.composition.bridges import ProjectsAuditBridge
    from app.projects.application.ports import ProjectEvent
    from tests.fakes import FakeAuditEntries, FakePeople

    port = FakeAuditEntries()
    people = FakePeople({"a": ("Ada", "ada@x.test"), "m": ("Maya", "maya@x.test")})
    ProjectsAuditBridge(AuditService(port), people).record(
        ProjectEvent("create_project", "a", "p-1", "Alpha", ("m", "a"))
    )
    (stored,) = port.stored
    e = stored.entry
    assert (e.kind, e.action, e.reason) == (Kind.project, "create_project", None)
    assert e.actor == Person("a", "Ada", "ada@x.test")
    assert e.target == Person("p-1", "Alpha", None)
    assert e.details == (Person("m", "Maya", "maya@x.test"), Person("a", "Ada", "ada@x.test"))
    assert people.asked == [{"a", "m"}]  # one question, for the actor and the members together
```

```python
# apps/api/tests/test_projects_composition.py
@pytest.mark.ac("AC-29")
def test_the_audit_bridge_keeps_an_id_it_has_no_name_for():
    from app.audit.application.service import AuditService
    from app.audit.domain.entry import Person
    from app.composition.bridges import ProjectsAuditBridge
    from app.projects.application.ports import ProjectEvent
    from tests.fakes import FakeAuditEntries, FakePeople

    port = FakeAuditEntries()
    ProjectsAuditBridge(AuditService(port), FakePeople()).record(
        ProjectEvent("create_project", "a", "p", "Alpha", ("m",))
    )
    e = port.stored[0].entry
    assert (e.actor, e.details) == (Person("a"), (Person("m"),))
```

**Code**:

The `People` port, in `ports.py`:

```python
# apps/api/app/projects/application/ports.py
class People(Protocol):
    def names_of(self, ids: list[str]) -> dict[str, tuple[str, str]]:
        """For each known id, (name, email) as they are now. Unknown ids are left out."""
        ...
```

The two bridges, in `app/composition/bridges.py`:

```python
# apps/api/app/composition/bridges.py
class PeopleBridge:
    """Projects' People port, answered by Access's use case, on the same session as the request."""

    def __init__(self, access: AccessService):
        self._access = access

    def names_of(self, ids: list[str]) -> dict[str, tuple[str, str]]:
        return {p.id: (p.name, p.email) for p in self._access.people(ids)}
```

```python
# apps/api/app/composition/bridges.py
class ProjectsAuditBridge:
    """Projects' AuditLog port, answered by Audit's use case, on the same session as the request. The names are the
    ones people have now, written into the entry so a later rename does not change it (RULE-L4)."""

    def __init__(self, audit: AuditService, people: People):
        self._audit = audit
        self._people = people

    def record(self, event: ProjectEvent) -> None:
        names = self._people.names_of([event.actor_id, *event.member_ids])

        def person(account_id: str) -> Person:
            name, email = names.get(account_id, (None, None))
            return Person(account_id, name, email)

        self._audit.record(
            AuditEntry(
                actor=person(event.actor_id),
                action=event.action,
                kind=Kind.project,
                target=Person(event.project_id, event.project_name),  # the project: id and name, no email
                details=tuple(person(i) for i in event.member_ids),
                reason=event.reason,
            )
        )
```

**Logic.** Projects does not import Audit or Access. The bridges are the only place that sees both sides: the people bridge answers Projects'
`People` port with Access's use case, and the audit bridge answers `AuditLog` with Audit's. The people are asked once, for the actor and
the members together, and an id with no name keeps its id (`Person(id)` with no name or email). The project is the target: its id and
name, no email.

---

## Step 3: wire it, and see it in the trail (AC-29, AC-85, AC-89)

**Test** (API):

A new file `tests/test_projects_audit_api.py`, through `create_app` and `GET /audit`. `project_entries` keeps the
entries with `kind == "project"`:

```python
# apps/api/tests/test_projects_audit_api.py
def project_entries(api, admin):
    return [e for e in api.get("/audit", headers=admin).json() if e["kind"] == "project"]
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-29")
def test_a_created_project_writes_one_entry_with_the_actor_the_project_and_the_first_members(api, admin):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    _, bob_id = active_user(api, admin, "sub-bob", "bob@x.test")
    ada_id = me_id(api, admin)

    project = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id, bob_id]}).json()

    (e,) = project_entries(api, admin)
    assert (e["kind"], e["action"], e["reason"]) == ("project", "create_project", None)
    assert (e["actor_id"], e["actor_name"], e["actor_email"]) == (ada_id, "Ada", "ada@x.test")
    assert (e["target_id"], e["target_name"], e["target_email"]) == (project["id"], "Alpha", None)
    assert e["details"] == [
        {"id": maya_id, "name": "maya", "email": "maya@x.test"},
        {"id": bob_id, "name": "bob", "email": "bob@x.test"},
    ]
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-29")
def test_a_rename_afterwards_does_not_change_the_entry(api, admin):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]})
    renamed = auth("sub-maya", "maya@x.test", name="Maya Lopez")
    assert api.get("/me", headers=renamed).json()["name"] == "Maya Lopez"
    assert api.get("/me", headers=auth("sub-ada", "ada@x.test", name="Ada Byron")).json()["name"] == "Ada Byron"

    (e,) = project_entries(api, admin)
    assert (e["actor_name"], e["details"][0]["name"]) == ("Ada", "maya")
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-29")
def test_a_project_with_no_first_member_still_writes_one_entry(api, admin):
    api.post("/projects", headers=admin, json={"name": "Alpha", "members": []})
    (e,) = project_entries(api, admin)
    assert e["details"] == []
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-29")
def test_a_refused_creation_writes_no_entry(api, admin, engine):
    _, maya_id = register(api, "sub-maya", "maya@x.test")  # pending: not eligible
    user_h, _ = active_user(api, admin, "sub-bob", "bob@x.test")
    before = api.get("/audit", headers=admin).json()
    bad = [
        (user_h, {"name": "Alpha", "members": []}),
        (admin, {"name": "", "members": []}),
        (admin, {"name": "Alpha", "members": [], "id": "x"}),
        (admin, {"name": "Alpha", "members": [maya_id]}),
    ]
    for headers, body in bad:
        assert api.post("/projects", headers=headers, json=body).status_code in (403, 422)
    assert api.get("/audit", headers=admin).json() == before
    with Session(engine) as s:
        assert s.execute(text("SELECT count(*) FROM projects")).scalar_one() == 0
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-89")
def test_naming_a_person_twice_names_them_once_in_the_entry(api, admin):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id, maya_id]})
    (e,) = project_entries(api, admin)
    assert [d["id"] for d in e["details"]] == [maya_id]
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-85")
def test_an_administrator_sees_each_project_creation_in_the_trail_newest_first(api, admin):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    first = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]}).json()
    second = api.post("/projects", headers=admin, json={"name": "Beta", "members": []}).json()

    entries = api.get("/audit", headers=admin).json()
    assert [(e["kind"], e["target_name"]) for e in entries[:2]] == [("project", "Beta"), ("project", "Alpha")]
    assert (entries[0]["target_id"], entries[1]["target_id"]) == (second["id"], first["id"])
    assert entries[1]["details"][0]["name"] == "maya"
    assert entries[2]["kind"] == "account"  # the account entries are still there, below
```

**Code**:

The service is built with the two bridges on the request's session (`people` is shared with the service since UC-P3; at this task it was
built inline for the audit bridge only):

```python
# apps/api/app/composition/app.py, inside create_app
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

**Logic.** The request's one session means the project, its members and its audit entry commit together. The route and the use case do not
know that Audit exists.

---

## Step 4: log every refusal (AC-48)

**Test** (API):

In the same file, each marked `@pytest.mark.ac("AC-48")`, with a `FakeSecurityLog` as the log:

```python
# apps/api/tests/fakes.py
class FakeSecurityLog:
    """Records the security events, so a test can see what was raised. Satisfies both contexts' SecurityLog ports."""

    def __init__(self):
        self.events: list[dict] = []

    def event(self, name, result, person_id=None, session_id=None, reason=None):
        self.events.append(
            {"event": name, "result": result, "person_id": person_id, "session_id": session_id, "reason": reason}
        )
```

```python
# apps/api/tests/test_projects_audit_api.py
def refusal_lines(log, since):
    return log.events[since:]
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-48")
@pytest.mark.parametrize(
    "who,body,status,code",
    [
        ("user", {"name": "Alpha", "members": []}, 403, "forbidden"),
        ("admin", {"name": "  ", "members": []}, 422, "invalid_project_name"),
        ("admin", {"name": "Alpha", "members": [], "id": "x"}, 422, "invalid_request"),
        ("admin", {"name": "Alpha", "members": ["no-such-account"]}, 422, "member_not_eligible"),
        ("admin", ["not", "an", "object"], 422, "invalid_request"),
    ],
)
def test_each_projects_refusal_writes_exactly_one_line_with_its_code_and_who(api, admin, log, who, body, status, code):
    user_h, user_id = active_user(api, admin, "sub-bob", "bob@x.test")
    headers, account_id = (user_h, user_id) if who == "user" else (admin, me_id(api, admin))
    since = len(log.events)

    r = api.post("/projects", headers=headers, json=body)

    assert r.status_code == status
    (line,) = refusal_lines(log, since)
    assert (line["event"], line["result"], line["reason"], line["person_id"]) == (
        "request_refused",
        "refused",
        code,
        account_id,
    )
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-48")
def test_a_created_project_writes_no_line(api, admin, log):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    since = len(log.events)
    assert api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]}).status_code == 201
    assert refusal_lines(log, since) == []
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-48")
def test_a_guards_refusal_is_logged_once_by_the_guard_and_not_again_by_projects(api, admin, log):
    pending, pending_id = register(api, "sub-new", "new@x.test")
    gone, gone_id = active_user(api, admin, "sub-gone", "gone@x.test")
    api.post(f"/accounts/{gone_id}/deactivate", headers=admin, json={"reason": "Left"})
    body = {"name": "Alpha", "members": []}
    for headers, code in [
        ({}, "missing_token"),
        ({"Authorization": "Bearer nope"}, "invalid_token"),
        (pending, "account_pending"),
        (gone, "account_deactivated"),
    ]:
        since = len(log.events)
        assert api.post("/projects", headers=headers, json=body).status_code in (401, 403)
        assert [e["reason"] for e in refusal_lines(log, since)] == [code]
```

```python
# apps/api/tests/test_projects_audit_api.py
@pytest.mark.ac("AC-48")
def test_the_json_line_holds_no_project_name_and_no_account_id_but_the_callers(engine):
    stream = StringIO()
    settings = Settings(keycloak_url="http://kc.test", bootstrap_admin_emails="ada@x.test")
    verifier = JwtTokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key())
    api = TestClient(create_app(settings, verifier, FakeIdp(), engine, JsonStdoutSecurityLog(stream)))
    admin = auth("sub-ada", "ada@x.test", name="Ada")
    ada_id = me_id(api, admin)
    stream.truncate(0)
    stream.seek(0)

    r = api.post("/projects", headers=admin, json={"name": "Secret Alpha", "members": ["acc-someone-else"]})

    assert r.status_code == 422
    (raw,) = stream.getvalue().splitlines()
    line = json.loads(raw)
    assert (line["event"], line["result"], line["reason"], line["person_id"]) == (
        "request_refused",
        "refused",
        "member_not_eligible",
        ada_id,
    )
    assert "Secret" not in raw and "acc-someone-else" not in raw
```

**Code**:

The `SecurityLog` port, in `ports.py` (the handlers import it):

```python
# apps/api/app/projects/application/ports.py
class SecurityLog(Protocol):
    """Where Projects says that it refused a request, for the operators (ADR 0013). Never an audit entry."""

    def event(
        self,
        name: str,
        result: str,
        person_id: str | None = None,
        session_id: str | None = None,
        reason: str | None = None,
    ) -> None: ...
```

`register_error_handlers(app, security_log)` calls `refused(...)` in both handlers:

```python
# apps/api/app/projects/adapters/inbound/errors.py
def register_error_handlers(app: FastAPI, security_log: SecurityLog) -> None:
    def refused(request: Request, code: str) -> None:
        """One line for each refusal Projects answers: the code and who, never the name or an id from the body."""
        security_log.event(
            "request_refused", "refused", person_id=getattr(request.state, "person_id", None), reason=code
        )

    @app.exception_handler(ProjectsError)
    async def projects_error(request: Request, exc: ProjectsError):
        refused(request, exc.code)
        return JSONResponse(
            {"detail": {"code": exc.code, "message": exc.message}},
            status_code=HTTP_STATUS.get(type(exc), 400),
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        """A body that is not even a JSON object, on /projects only. FastAPI's own answer echoes the input."""
        if request.url.path != "/projects" and not request.url.path.startswith("/projects/"):
            return await request_validation_exception_handler(request, exc)
        error = InvalidRequest("The request is not valid.")
        refused(request, error.code)
        return JSONResponse({"detail": {"code": error.code, "message": error.message}}, status_code=422)
```

`composition/app.py` passes the log, inside `create_app`:

```python
# apps/api/app/composition/app.py, inside create_app
    register_projects_error_handlers(app, security_log)
```

In `tests/test_projects_errors.py` the two calls to `register_error_handlers` get a `FakeSecurityLog()`.

**Logic.** Every Projects refusal passes the two handlers, so there is one place for the line: the code and the caller's id from
`request.state.person_id`, never the name or an id from the body (ADR 0013). Both handlers do it: Projects' own errors and a body that
is not a JSON object. The guard's refusals are already logged by the guard, so Projects does not log them again. A success writes no line.
