# Task P1.3: An administrator creates a project

**Task ID:** TSK-P1.3 · **Use Case:** UC-P1 · **Criteria:** AC-9, AC-10 · **Code matched at:** `7481263`

What this does and why: [summary, task P1.3](summary.md#p13-an-administrator-creates-a-project).

Run from `apps/api/`: `uv run pytest tests/fakes.py tests/test_projects_api.py tests/test_projects_composition.py tests/test_projects_domain.py tests/test_projects_errors.py tests/test_projects_service.py tests/test_projects_sql.py -q`

Work test first in each step: write the test, run it, see it fail, then write the code.

---

## Step 1: the aggregate (AC-9, AC-10)

**Test** (Unit):

```python
# apps/api/tests/test_projects_domain.py
@pytest.mark.ac("AC-9")
def test_a_project_has_the_name_the_creator_and_the_named_first_members():
    p = Project.create(ADMIN, "Alpha", {"acc-maya", "acc-bob"})
    assert (p.name, p.created_by) == ("Alpha", "acc-ada")
    assert p.members == {"acc-maya", "acc-bob"}
```

```python
# apps/api/tests/test_projects_domain.py
@pytest.mark.ac("AC-9")
def test_each_first_member_is_added_by_the_creator():
    p = Project.create(ADMIN, "Alpha", ["acc-maya"])
    assert p.memberships == (Membership("acc-maya", added_by="acc-ada"),)
```

```python
# apps/api/tests/test_projects_domain.py
@pytest.mark.ac("AC-10")
def test_an_administrator_who_names_themselves_is_a_member():
    assert Project.create(ADMIN, "Alpha", ["acc-ada"]).members == {"acc-ada"}
```

```python
# apps/api/tests/test_projects_domain.py
@pytest.mark.ac("AC-10")
def test_an_administrator_who_names_nobody_makes_a_project_with_no_member():
    p = Project.create(ADMIN, "Alpha", [])
    assert p.members == frozenset() and p.memberships == ()
```

Two more tests carry no criterion (rules of this task with none of their own): `test_the_creator_is_not_a_member_unless_named` and
`test_the_id_is_a_random_uuid_made_in_the_domain`, in the same file.

**Code**:

`caller.py` is final as it stands (the file also has a docstring):

```python
# apps/api/app/projects/domain/caller.py
@dataclass(frozen=True)
class Caller:
    account_id: str
    is_administrator: bool
```

`errors.py` holds the base the later refusals extend (the file has more classes since):

```python
# apps/api/app/projects/domain/errors.py
class ProjectsError(Exception):
    code = "projects_error"

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message
```

`project.py` as this task wrote it (commit `9e8be89`), **stage 1 shape, not the final file**. Today the file also has the later
methods, and `create` also checks the name and the cap on first members (TSK-P1.5):

```python
"""The Project aggregate and the Membership inside it (BC-PROJECTS, OBJ-P1, OBJ-P2). Pure: standard library only."""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from app.projects.domain.caller import Caller


@dataclass(frozen=True)
class Membership:
    account_id: str
    added_by: str


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    created_by: str
    memberships: tuple[Membership, ...] = ()

    @property
    def members(self) -> frozenset[str]:
        return frozenset(m.account_id for m in self.memberships)

    @classmethod
    def create(cls, caller: Caller, name: str, member_ids: Iterable[str]) -> "Project":
        """A new project. Its id is random, so it reveals nothing about count or order (ADR 0015). Only the people
        named are members: the creator is one only if named (AC-10)."""
        memberships = tuple(Membership(i, added_by=caller.account_id) for i in dict.fromkeys(member_ids))
        return cls(str(uuid.uuid4()), name, caller.account_id, memberships)
```

**Logic.** Only the people named are members. `dict.fromkeys` keeps the order and drops a repeat. Each `Membership` records who added it
(`added_by`, ADR 0015). The id is a random UUID made in the domain (`uuid4`), so it reveals no count or order and needs no
database.

---

## Step 2: the use case and its port (AC-9, AC-10)

**Test** (Unit):

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-9")
def test_create_saves_the_project_with_its_first_members_and_returns_it(service, projects):
    p = service.create(ADMIN, "Alpha", ["acc-maya"])
    assert projects.by_id(p.id) is p.project
    assert (p.name, p.created_by, p.members) == ("Alpha", "acc-ada", {"acc-maya"})
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-10")
def test_create_with_the_administrator_as_first_member(service, projects):
    p = service.create(ADMIN, "Alpha", ["acc-ada"])
    assert projects.by_id(p.id).members == {"acc-ada"}
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-10")
def test_create_with_no_first_member(service, projects):
    p = service.create(ADMIN, "Alpha", [])
    assert projects.by_id(p.id).members == frozenset()
```

`FakeProjects` is an in-memory repository, in `tests/fakes.py`:

```python
# apps/api/tests/fakes.py, FakeProjects (the class holds more methods since)
class FakeProjects:
    """Stands in for Projects' ProjectRepository port: keeps the projects in memory."""

    def __init__(self):
        self.rows: dict[str, object] = {}
        self.added: list = []  # the memberships written by add_member
        self.lose_the_race = False  # another request inserts the same row first, as the unique key would show

    def add(self, project):
        self.rows[project.id] = project

    def by_id(self, project_id):
        return self.rows.get(project_id)
```

**Code**:

Both blocks are the stage shape at `9e8be89`, not the final files (the port and the service hold more ports and checks today):

```python
# app/projects/application/ports.py (stage shape)
from typing import Protocol

from app.projects.domain.project import Project


class ProjectRepository(Protocol):
    def add(self, project: Project) -> None: ...
    def by_id(self, project_id: str) -> Project | None: ...
```

```python
# app/projects/application/service.py (stage shape)
class ProjectsService:
    def __init__(self, projects: ProjectRepository):
        self._projects = projects

    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> Project:
        project = Project.create(caller, name, member_ids)
        self._projects.add(project)
        return project
```

**Logic.** The use case builds the `Project` through the domain and saves it through the port. It knows no database.

---

## Step 3: the SQL adapter (AC-9, AC-10)

**Test** (Unit):

The file runs on SQLite, and on PostgreSQL when `TEST_DATABASE_URL` is set.

```python
# apps/api/tests/test_projects_sql.py
@pytest.mark.ac("AC-9")
def test_a_project_and_its_memberships_come_back_from_a_new_session(engine):
    project = Project.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    with Session(engine) as s:
        SqlProjects(s).add(project)
        s.commit()
    with Session(engine) as s:
        got = SqlProjects(s).by_id(project.id)
    assert got is not None and got.id == project.id
    assert (got.name, got.created_by, got.members) == ("Alpha", "acc-ada", {"acc-maya", "acc-bob"})
    assert {m.added_by for m in got.memberships} == {"acc-ada"}
```

```python
# apps/api/tests/test_projects_sql.py
@pytest.mark.ac("AC-10")
def test_a_project_with_no_member_comes_back_with_none(engine):
    project = Project.create(ADMIN, "Alpha", [])
    with Session(engine) as s:
        SqlProjects(s).add(project)
        s.commit()
    with Session(engine) as s:
        assert SqlProjects(s).by_id(project.id).members == frozenset()
```

```python
# apps/api/tests/test_projects_sql.py
def test_the_project_and_its_memberships_commit_together(engine):
    project = Project.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    with Session(engine) as s:
        SqlProjects(s).add(project)
        s.flush()
        s.commit()
    assert counts(engine) == (1, 2)
```

```python
# apps/api/tests/test_projects_sql.py
def test_a_rollback_leaves_neither_the_project_nor_its_memberships(engine):
    with Session(engine) as s:
        SqlProjects(s).add(Project.create(ADMIN, "Alpha", ["acc-maya"]))
        s.rollback()
    assert counts(engine) == (0, 0)
```

Three more in the same file: the stored id is a UUID string, an unknown id gives `None`, and the database sets both times
(`created_at`, `added_at`).

**Code**:

`SqlProjects.add` as it is today (the class also holds the readers and the member changes of later tasks; the two row classes
were made in TSK-P1.2):

```python
# apps/api/app/projects/adapters/outbound/sql.py, SqlProjects.add
    def add(self, project: Project) -> None:
        self._s.add(ProjectRow(id=project.id, name=project.name, created_by=project.created_by))
        self._s.flush()  # the project row first: the memberships point at it, and there is no relationship to order them
        self._s.add_all(
            MembershipRow(project_id=project.id, account_id=m.account_id, added_by=m.added_by)
            for m in project.memberships
        )
        self._s.flush()
```

**Logic.** The project row is written first and flushed, because the memberships point at it and there is no relationship to order them.
Both are written in the request's own session, so they commit together or not at all. The database sets the times
(`created_at`, `added_at`), never the application: the API role may not name them (AC-95, TSK-P1.2).

---

## Step 4: the route and the wiring (AC-9, AC-10)

**Test** (API and Unit):

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-9")
def test_an_administrator_creates_a_project_naming_an_active_account(api, admin, engine):
    maya_h, maya_id = register(api, "sub-maya", "maya@x.test")
    api.post(f"/accounts/{maya_id}/approve", headers=admin)

    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]})

    assert r.status_code == 201
    body = r.json()
    assert str(uuid.UUID(body["id"])) == body["id"]
    assert (body["name"], body["created_by"]) == ("Alpha", me_id(api, admin))
    assert body["members"] == [{"id": maya_id, "name": "maya"}]  # the name as Access has it now (ADR 0016)
    assert {k: body[k] for k in PLACEHOLDERS} == PLACEHOLDERS
    assert set(body) == {"id", "name", "created_by", "members", *PLACEHOLDERS}
    project = stored(engine, body["id"])  # a later read through the repository
    assert (project.name, project.members) == ("Alpha", {maya_id})
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-10")
def test_an_administrator_naming_themselves_is_a_member(api, admin, engine):
    ada_id = me_id(api, admin)
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [ada_id]})
    assert (r.status_code, r.json()["members"]) == (201, [{"id": ada_id, "name": "Ada"}])
    assert stored(engine, r.json()["id"]).members == {ada_id}
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-10")
def test_an_administrator_naming_nobody_makes_a_project_with_no_member(api, admin, engine):
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": []})
    assert (r.status_code, r.json()["members"]) == (201, [])
    assert stored(engine, r.json()["id"]).members == frozenset()
```

```python
# apps/api/tests/test_projects_api.py
def test_the_route_is_behind_the_access_guard_chain(api):
    assert api.post("/projects", json={"name": "Alpha", "members": []}).status_code == 401
    h, _ = register(api, "sub-new", "new@x.test")  # pending
    r = api.post("/projects", headers=h, json={"name": "Alpha", "members": []})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "account_pending")
```

```python
# apps/api/tests/test_projects_api.py
def test_the_project_route_is_served_by_the_projects_context(api):
    modules = {r.endpoint.__module__ for r in _api_routes(api.app) if r.path == "/projects"}
    assert modules == {"app.projects.adapters.inbound.http"}
```

```python
# apps/api/tests/test_projects_errors.py
def test_a_projects_refusal_is_answered_with_its_code_and_message():
    class Odd(ProjectsError):
        code = "odd"

    app = FastAPI()
    register_error_handlers(app, FakeSecurityLog())

    @app.get("/x")
    def x():
        raise Odd("No.")

    r = TestClient(app).get("/x")
    assert (r.status_code, r.json()) == (400, {"detail": {"code": "odd", "message": "No."}})
```

```python
# apps/api/tests/test_projects_composition.py
@pytest.mark.ac("AC-10")
def test_the_guards_account_becomes_projects_caller():
    assert projects_caller(account(Role.administrator)) == Caller("acc-1", is_administrator=True)
    assert projects_caller(account(Role.user)) == Caller("acc-1", is_administrator=False)
```

```python
# apps/api/tests/test_projects_composition.py
def test_a_deactivated_administrator_is_not_an_administrator_for_projects():
    assert projects_caller(account(Role.administrator, Status.deactivated)).is_administrator is False
```

`test_two_projects_have_two_different_ids` is in the API file too.

**Code**:

First the shapes this task wrote (commit `9e8be89`), enough to build and run the task on its own. They are **stage shape, not the
final files**:

```python
# app/projects/adapters/inbound/http.py (stage shape)
def build_router(
    service_dependency: Callable[..., ProjectsService], caller_dependency: Callable[..., Caller]
) -> APIRouter:
    router = APIRouter()

    @router.post("/projects", status_code=201, response_model=ProjectOut)
    def create_project(
        body: CreateProjectIn,
        who: Caller = Depends(caller_dependency),
        svc: ProjectsService = Depends(service_dependency),
    ):
        return ProjectOut.of(svc.create(who, body.name, body.members))

    return router
```

```python
# app/projects/adapters/inbound/schemas.py (stage shape)
class CreateProjectIn(BaseModel):
    name: str
    members: list[str] = []  # the first members, as account ids


class ProjectOut(BaseModel):
    id: str
    name: str
    created_by: str
    members: list[str]
    files: list[str] = []
    endpoints: list[str] = []
    evaluations: list[str] = []

    @classmethod
    def of(cls, p: Project) -> "ProjectOut":
        return cls(id=p.id, name=p.name, created_by=p.created_by, members=sorted(p.members))
```

The handler answers a Projects rule's refusal with its code and message. Nothing refuses yet, so the status table is empty and
every later task adds its error to it:

```python
# app/projects/adapters/inbound/errors.py (stage shape)
HTTP_STATUS: dict[type[ProjectsError], int] = {}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProjectsError)
    async def projects_error(request: Request, exc: ProjectsError):
        return JSONResponse(
            {"detail": {"code": exc.code, "message": exc.message}},
            status_code=HTTP_STATUS.get(type(exc), 400),
        )
```

In `app/composition/app.py`, inside `create_app`, `register_projects_error_handlers(app)` is called beside the other two
`register_*_error_handlers` calls, and the service is built on the request's session:

```python
# app/composition/app.py (stage shape)
    def projects_service(session: Session = Depends(db)) -> ProjectsService:
        return ProjectsService(
            SqlProjects(session)
        )  # the request's session, so the project and its members commit together
```

What the files look like today. The router and the schemas have grown, and the role check moved out of the route's body. Three
things in them come from later tasks: `authorise_creation` and the raw body (TSK-P1.5, AC-11 and AC-93), `ProjectView` and
`MemberOut` (the member names, ADR 0016). The router also holds the list, open and member routes of UC-P3 and UC-P2.

```python
# apps/api/app/projects/adapters/inbound/http.py, inside build_router
    @router.post("/projects", status_code=201, response_model=ProjectOut)
    def create_project(
        raw: dict[str, Any] = Body(),
        who: Caller = Depends(caller_dependency),
        svc: ProjectsService = Depends(service_dependency),
    ):
        svc.authorise_creation(who)  # the role first, then the input (AC-11, AC-93)
        try:
            body = CreateProjectIn.model_validate(raw)
        except ValidationError:  # no detail: it would echo the input
            raise InvalidRequest("The request is not valid.") from None
        return ProjectOut.of(svc.create(who, body.name, body.members))
```

```python
# apps/api/app/projects/adapters/inbound/schemas.py
class CreateProjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # mass assignment: an unknown field is refused, not ignored (AC-93)

    name: str
    members: list[str] = []  # the first members, as account ids
```

```python
# apps/api/app/projects/adapters/inbound/schemas.py
class ProjectOut(BaseModel):
    id: str
    name: str
    created_by: str
    members: list[MemberOut]
    files: list[str] = []
    endpoints: list[str] = []
    evaluations: list[str] = []

    @classmethod
    def of(cls, v: ProjectView) -> "ProjectOut":
        members = [MemberOut(id=i, name=n) for i, n in sorted(v.names.items())]
        return cls(id=v.id, name=v.name, created_by=v.created_by, members=members)
```

The Caller bridge, the only place that knows both contexts:

```python
# apps/api/app/composition/bridges.py
def projects_caller(account: Account) -> ProjectsCaller:
    """The guard's account, in Projects' words (ADR 0002, 0015). The guard chain has refused a deactivated, pending
    or unknown account before this is built; whether an administrator may act is for the use case to say."""
    return ProjectsCaller(account.id, is_administrator=account.is_active_administrator)
```

and in `app/composition/app.py`, inside `create_app` (the lines that make the Caller and mount the router):

```python
# apps/api/app/composition/app.py
    def project_caller(account=Depends(guards.active_account)):
        return projects_caller(account)  # the same guard chain as every route: 401, pending and deactivated are refused
```

```python
# apps/api/app/composition/app.py
    app.include_router(build_projects_router(projects_service, project_caller))
```

**Logic.** The route sits behind the same guard chain as every account route: no token, a pending and a deactivated account are refused
before any Projects code runs. `projects_service` builds the service on the request's session, so the project and its members
commit together. It was the one-argument `ProjectsService(SqlProjects(session))` shown above, and now also gets the account,
audit and people ports (TSK-P1.6, P1.7). The final `ProjectsService.create`, with every check added later, is in
[TSK-P1.4](TSK-P1.4-only-an-administrator-creates-a-project.md).
