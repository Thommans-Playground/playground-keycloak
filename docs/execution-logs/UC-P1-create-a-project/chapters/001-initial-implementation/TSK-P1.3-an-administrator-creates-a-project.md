# TSK-P1.3: an administrator creates a project

AC-9, AC-10 · plan status: **draft, not reviewed** · matches the code at `7481263`

Ground rules, the layout and the commands are in the [chapter summary](summary.md).

This is the plan someone follows to build this task. It was written by working backwards from the code that exists, so
its final code is that code: each block marked `# file` is a copy of that file at the commit above. Where the file has
grown since (later tasks added to it), only what this task adds is quoted, and the text says so.

## 1. What we are building, and why

`POST /projects` takes a name and a list of first members and makes a project whose members are exactly the people
named. This task builds the whole path once, thin, from the domain to the route: later tasks add the refusals. It does
not yet check the role, the name, the members' accounts or audit anything (TSK-P1.4 to P1.7).

| AC | Given | Then | Why |
|---|---|---|---|
| AC-9 | an administrator and an active account | they create a project naming that account as a first member; the project exists and that person is a member | This is the use case itself (FR-7): without it there is no project for anything else to hang on. |
| AC-10 | an administrator | they create a project naming themselves as a first member; it exists and they are a member | The administrator is a superuser (decision 13) but is not a member by default. Being one is a choice, and so is naming nobody: a project may start with no member. |

## 2. The logic

1. **Only the people named are members.** The creator is a member only if named (AC-10). A project with none is valid.
2. **`added_by` of every first member is the creator.** Each `Membership` records who added it (ADR 0015).
3. **The id is a random UUID made in the domain** (`uuid4`), so an id reveals no count or order and the domain needs no
   database to have one (ADR 0015).
4. **Each person once.** `dict.fromkeys` keeps the order and drops a repeat. The test for AC-89 comes in TSK-P1.6; the
   one line is here because it is the natural way to write the loop.
5. **The project and its memberships are written in the request's own session**, project first, then a flush, then the
   memberships (they point at it). They commit together or not at all.
6. **The database sets the times**, never the application (`created_at`, `added_at`): the API role may not name them
   (AC-95, built in TSK-P1.2).
7. **Projects has its own `Caller`**, built in `composition/` from the account the guard chain returns (ADR 0002, 0015).
   The route sits behind the same guard chain as every account route, so no token, a pending and a deactivated account
   are refused before any Projects code runs.
8. **The answer is the project plus three empty lists**, `files`, `endpoints` and `evaluations` (decision 23).

**Where it lives:** the rule in `domain/project.py` (`Project.create`), the use case in `application/service.py`, the
port in `application/ports.py`, the table access in `adapters/outbound/sql.py`, the route and its schemas in
`adapters/inbound/`, and the only code that sees Access and Projects together in `composition/`. The domain imports
nothing outside itself (ADR 0010); the route holds no rule.

## 3. The plan

Four stages, inside out. The test comes before the code in each. Run the commands from `apps/api/`.

### Stage 1: the aggregate (AC-9, AC-10)

**1a. Write the tests** in `tests/test_projects_domain.py`:

- a project has the name, the creator and the named first members (`AC-9`)
- each first member is added by the creator (`AC-9`)
- an administrator who names themselves is a member (`AC-10`); one who names nobody makes a project with no member (`AC-10`)
- the creator is not a member unless named; the id is a random UUID version 4 (no marker: these are rules of this task
  with no criterion of their own)

Run `uv run pytest tests/test_projects_domain.py -q -x`. **Expect** a collection error, because `Project` does not exist
yet (checked).

**1b. Write the domain.** Three files. `caller.py` is final as it stands:

```python
# app/projects/domain/caller.py
@dataclass(frozen=True)
class Caller:
    account_id: str
    is_administrator: bool
```

`errors.py` holds the base the later refusals extend (the file has more classes since):

```python
# app/projects/domain/errors.py, ProjectsError
class ProjectsError(Exception):
    code = "projects_error"

    def __init__(self, message: str = ""):
        super().__init__(message)
        self.message = message
```

`project.py` holds `Membership`, `Project` and `Project.create`. This is the whole file as this task wrote it (commit
`9e8be89`): **stage shape, not the final file**. Today the file also has the later methods, and `create` also checks the
name and the cap on first members (TSK-P1.5, shown at the end of its file).

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

**Expect** `6 passed` (checked).

### Stage 2: the use case and its port (AC-9, AC-10)

**2a. Write the tests** in `tests/test_projects_service.py`, with `FakeProjects` (an in-memory repository, in
`tests/fakes.py`): `create` saves the project with its first members and returns it (`AC-9`); with the administrator as
first member and with none (`AC-10`).

Run `uv run pytest tests/test_projects_service.py -q -x`. **Expect** a collection error, `ProjectsService` does not exist
(checked).

**2b. Add the port `ProjectRepository`** (`add`, `by_id`) and `ProjectsService.create`, which builds the `Project` and
saves it. Both are the stage shape at `9e8be89`, not the final files (the port and the service hold more ports and
checks today):

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

**Expect** `3 passed` (checked).

### Stage 3: the SQL adapter (AC-9, AC-10)

**3a. Write the tests** in `tests/test_projects_sql.py`, which runs on SQLite, and on PostgreSQL when
`TEST_DATABASE_URL` is set: a project and its memberships come back from a new session (`AC-9`); a project with no
member comes back with none (`AC-10`); the two commit together, and a rollback leaves neither; the stored id is a UUID
string; an unknown id gives `None`; the database sets both times.

Run `uv run pytest tests/test_projects_sql.py -q`. **Expect** a collection error, `SqlProjects` does not exist (checked).

**3b. Add `SqlProjects.add` and `by_id`** to `adapters/outbound/sql.py` (the two row classes were made in TSK-P1.2).
The final `add` is below; the file also holds the readers and the member changes of later tasks.

```python
# app/projects/adapters/outbound/sql.py, SqlProjects.add (the class holds more since)
    def add(self, project: Project) -> None:
        self._s.add(ProjectRow(id=project.id, name=project.name, created_by=project.created_by))
        self._s.flush()  # the project row first: the memberships point at it, and there is no relationship to order them
        self._s.add_all(
            MembershipRow(project_id=project.id, account_id=m.account_id, added_by=m.added_by)
            for m in project.memberships
        )
        self._s.flush()
```

**Expect** `7 passed` on SQLite (checked). PostgreSQL: not run, `TEST_DATABASE_URL` is not set where this was written.

### Stage 4: the route and the wiring (AC-9, AC-10)

**4a. Write the tests**:

- `tests/test_projects_api.py`, through the HTTP client: an administrator creates a project naming an active account
  (`AC-9`): 201, a UUID id, the name, the creator, the member, the three empty lists, and the stored project read back
  through the repository; naming themselves (`AC-10`); naming nobody (`AC-10`); two projects, two ids; the route is
  behind the guard chain (401 with no token, `account_pending` for a pending account); the route is served by the
  Projects context.
- `tests/test_projects_errors.py`: a `ProjectsError` is answered with its code and message (400 by default).
- `tests/test_projects_composition.py`: the guard's account becomes Projects' `Caller` (`AC-10`), and a deactivated
  administrator is not an administrator.

Run `uv run pytest tests/test_projects_api.py tests/test_projects_errors.py tests/test_projects_composition.py -q`.
**Expect** collection errors in the errors and composition files (`projects_caller` and the handler do not exist) and,
with only the route and schemas missing, the API tests fail with no route (checked: `6 failed` in the API file alone).

**4b. Write the route, its schemas, the handler and the wiring.** First the shapes this task wrote (commit
`9e8be89`), which are enough to build and run the task on its own. They are **stage shape, not the final files**:

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

The handler answers a Projects rule's refusal with its code and message. Nothing refuses yet, so the status table is
empty and every later task adds its error to it:

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

In `app/composition/app.py`, inside `create_app`, `register_projects_error_handlers(app)` is called beside the other
two `register_*_error_handlers` calls, and the service is built on the request's session (stage shape):

```python
# app/composition/app.py (stage shape)
    def projects_service(session: Session = Depends(db)) -> ProjectsService:
        return ProjectsService(
            SqlProjects(session)
        )  # the request's session, so the project and its members commit together
```

**What the files look like today.** The router and the schemas have grown, and the role check moved out of the route's
body. These blocks are exact copies of HEAD. Three things in them come from later tasks: `authorise_creation` and the
raw body (TSK-P1.5, AC-11 and AC-93), `ProjectView` and `MemberOut` (the member names, ADR 0016). The router also holds
the list, open and member routes of UC-P3 and UC-P2.

```python
# app/projects/adapters/inbound/http.py, create_project (the router holds more routes since)
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
# app/projects/adapters/inbound/schemas.py, CreateProjectIn and ProjectOut
class CreateProjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # mass assignment: an unknown field is refused, not ignored (AC-93)

    name: str
    members: list[str] = []  # the first members, as account ids


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
# app/composition/bridges.py
def projects_caller(account: Account) -> ProjectsCaller:
    """The guard's account, in Projects' words (ADR 0002, 0015). The guard chain has refused a deactivated, pending
    or unknown account before this is built; whether an administrator may act is for the use case to say."""
    return ProjectsCaller(account.id, is_administrator=account.is_active_administrator)
```

and in `app/composition/app.py`, inside `create_app` (the lines that make the Caller and mount the router):

```python
# app/composition/app.py
    def project_caller(account=Depends(guards.active_account)):
        return projects_caller(account)  # the same guard chain as every route: 401, pending and deactivated are refused

    app.include_router(build_projects_router(projects_service, project_caller))
```

`projects_service` in the same function builds the service on the request's session; it was the one-argument
`ProjectsService(SqlProjects(session))` shown above, and now also gets the account, audit and people ports (TSK-P1.6, P1.7).
The final `ProjectsService.create`, with every check added later, is in [TSK-P1.4](TSK-P1.4-only-an-administrator-creates-a-project.md).

**Expect** `9 passed` for the three files (checked).

## 4. Check it yourself

```
uv run pytest -m "AC_9 or AC_10" -q         # 15 passed at the code in the header, counting later tasks' tests (checked)
uv run pytest tests/test_projects_domain.py tests/test_projects_sql.py -q
uv run pytest tests/test_architecture.py -q  # the domain imports nothing outside itself
uv run pytest -q                             # 468 passed, 47 skipped at the code in the header (checked)
```

At the commit that built this task the whole suite was `219 passed, 46 skipped` on SQLite (checked) and 265 on PostgreSQL
(the commit's message; not run here).

## 5. Where this leaves things

- Source: `app/projects/domain/project.py`, `caller.py`, `errors.py`; `application/ports.py`, `service.py`;
  `adapters/outbound/sql.py`; `adapters/inbound/http.py`, `schemas.py`, `errors.py`; `app/composition/bridges.py`, `app.py`
- Tests: `tests/test_projects_domain.py`, `test_projects_service.py`, `test_projects_sql.py`, `test_projects_api.py`,
  `test_projects_errors.py`, `test_projects_composition.py`, and `FakeProjects` in `tests/fakes.py`
- ADR: [0015](../../../../adr/0015-projects-context-build-plan.md) (layout, ports, tables). No new ADR.
- Not here yet: the role check (TSK-P1.4), name and cap (P1.5), active members (P1.6), audit and security log (P1.7).

## Where the real build differs

- One commit, `9e8be89`, built all four stages together; the stages above are a way to follow it, not four commits.
- The tests at that commit had the names, the `members` list of bare ids and a `FakeProjects` that returned the
  `Project` itself. Since then the answer carries `members` as `{id, name}` (ADR 0016) and the service returns a
  `ProjectView`, so the quoted `ProjectOut` and route differ from what the first commit wrote. The tests shown for AC-9
  and AC-10 at HEAD were adjusted to that (for instance `projects.by_id(p.id) is p.project`).
- The stage-4 "red" was run at the commit's parent with the route and schemas present and the wiring absent; with
  nothing present the API file fails the same way for the same reason.

## Review

Not reviewed. Write `Reviewed by <name> at <hash>` here when the plan has been read against the code.
