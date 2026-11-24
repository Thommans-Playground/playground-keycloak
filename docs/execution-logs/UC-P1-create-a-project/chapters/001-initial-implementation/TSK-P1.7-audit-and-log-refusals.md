# TSK-P1.7: audit a project creation, and log every refusal

AC-29 and AC-48 (AC-48 only in part: it also lists sign-in and session lines, which are not this task's; the commit also proves AC-85 and AC-89) · plan status: **draft, not reviewed** · matches the code at `7481263`

Ground rules, the layout and the commands are in the [chapter summary](summary.md).

This is the plan someone follows to build this task. It was written by working backwards from the code that exists, so
its final code is that code: each block marked `# file` is a copy of that file at the commit above. The task was built
in commit `58dc0f1`; later slices (UC-P2, UC-P3) changed some of the same files, and the blocks show them as they are now.

## 1. What we are building, and why

| AC | Given | Then | Why |
|---|---|---|---|
| AC-29 | an administrator and active accounts | creating a project naming them writes one audit entry: who created it, which project (id and name), and the first members, each with the name and email they had at that time | The trail must say who made what and with whom, and a later rename must not rewrite history (RULE-L4). A refused creation writes none. |
| AC-48 (the refused-request part) | a refused request | it writes one log line, holding no token and no code | Operators need to see refusals. Here the line also holds no project name and no id from the body, since the input is untrusted. |
| AC-89 | a person named twice as a first member | they are in the project once and in the entry once | One person, one line in the trail (the de-duplication itself is TSK-P1.6; this task proves it reaches the entry). |
| AC-85 | an administrator who created projects | opens the audit trail | the creations show, newest first, with the names as they were. Owned by UC-L1; here only proved through the HTTP path. |

## 2. The logic

1. **The entry is written after the project is saved, in the same transaction.** Both rows commit together or neither does,
   so there is no entry for a project that does not exist (AC-29). The service writes it only on the success path, so
   every refusal before it writes nothing.
2. **Projects speaks in ids; names are looked up when the entry is written.** `ProjectEvent` holds ids and the project
   name. The names and emails are taken at that moment and stored in the entry, so a rename later changes nothing (AC-29).
3. **One question for all the people.** The actor and the members go to the `People` port in one call (no N+1).
4. **An id with no name keeps its id** (`Person(id)` with no name or email) instead of failing.
5. **Projects does not import Audit or Access.** It has its own ports (`AuditLog`, `People`, `SecurityLog`); the bridges
   in `composition/` answer them with Audit's and Access's use cases (ADR 0010, ADR 0015).
6. **Every refusal Projects answers writes one line** (`request_refused`, result `refused`, the reason code and the
   caller's id from `request.state.person_id`), and never the name or an id from the body (AC-48, ADR 0013). Both
   handlers do it: Projects' own errors and a body that is not a JSON object. A refusal by the guard chain is already
   logged by the guard, so Projects does not log it again.
7. **A success writes no line.**

**Where it lives:** the event and the three ports in `application/ports.py`; the use in `ProjectsService.create`; the
two bridges in `composition/bridges.py`; the wiring in `composition/app.py`; the log in the error handlers of
`adapters/inbound/errors.py`, because that is the one place every Projects refusal passes.

## 3. The plan

Four stages. In each, the test comes first.

### Stage 1: the service writes the event (AC-29, AC-89)

**1a. Write the tests** in `tests/test_projects_service.py`, with a fake `FakeProjectsAudit` (in `tests/fakes.py`) that
keeps the events and what the repository held when each came:

- `AC-29`: one event with the actor, the project id, the name and the members in order
- `AC-29`: the event comes after the save, and holds the trimmed name
- `AC-89`: a person named twice is in the event once
- `AC-29`: a refused creation writes no event (four cases: not an administrator, empty name, 51 members, an account that is not active)

Every place that builds `ProjectsService` now passes the fake as a third argument, so the existing tests in
`tests/test_projects_input.py` and `tests/test_projects_service.py` change by that one argument.

Run `uv run pytest tests/test_projects_service.py -q`. **Expect** a collection error, `cannot import name 'ProjectEvent'`
(checked).

**1b. Add the event and the port** to `app/projects/application/ports.py` and the call to `create`: `ProjectEvent`, the
`AuditLog` port, and in `app/projects/application/service.py` an `audit: AuditLog` argument to `ProjectsService.__init__`
(stored as `self._audit`), which `create` calls with a `ProjectEvent` after saving. This is where the final code is; the
`People` port follows in stage 2 and the `SecurityLog` port in stage 4.

Run again. **Expect** `19 passed` for the service file and `44 passed` for it with `test_projects_input.py` (checked).

### Stage 2: the bridges (AC-29)

**2a. Write the fake and the tests.** Add `FakePeople` to `tests/fakes.py` (it answers `names_of` from a dict, leaving out
unknown ids). Then write the tests in `tests/test_projects_composition.py`, each `@pytest.mark.ac("AC-29")`:

- the people bridge answers through Access's `people` and leaves out an unknown id
- the audit bridge turns a `ProjectEvent` into a project entry with the names now; the people are asked once, for the actor and the members together
- the audit bridge keeps an id it has no name for

Run `uv run pytest tests/test_projects_composition.py -q`. **Expect** `3 failed, 3 passed` (checked): the three new ones
fail for the missing bridges.

**2b. Add `PeopleBridge` and `ProjectsAuditBridge`** to `app/composition/bridges.py`, and the `People` port to `ports.py`.
**Expect** `6 passed` (checked).

### Stage 3: wire it, and see it in the trail (AC-29, AC-85, AC-89)

**3a. Write the tests** in a new file `tests/test_projects_audit_api.py`, through `create_app` and `GET /audit`
(`project_entries` keeps the `kind == "project"` entries):

- `AC-29`: one entry with actor, target (id and name, no email) and the members with names and emails
- `AC-29`: a rename afterwards does not change it
- `AC-29`: no first member still writes one entry, with no details
- `AC-29`: a refused creation (four cases) writes no entry and no row in `projects`
- `AC-89`: naming a person twice names them once
- `AC-85`: two creations show newest first, above the account entries

**Expect** them to fail, since `create_app` builds the service without an audit.

**3b. Wire the service** in `app/composition/app.py`: it now takes the `AuditService` and builds the two bridges on
the request's session. **Expect** `6 passed` for `-m "AC_29 or AC_85 or AC_89"` in that file (checked, with the error
handler still unchanged).

### Stage 4: log every refusal (AC-48)

**4a. Write the tests** in the same file, each `@pytest.mark.ac("AC-48")`, with a `FakeSecurityLog` as the log:

- a table of five refusals (not an administrator, empty name, an unknown field, a member who is not eligible, a body that is a list): each writes exactly one line with `request_refused`, `refused`, its code and the caller's id
- a created project writes no line
- a guard's refusal (no token, a bad token, pending, deactivated) is logged once, by the guard, and not again by Projects
- the real `JsonStdoutSecurityLog` line holds neither the project name nor an account id from the body

Run `uv run pytest tests/test_projects_audit_api.py -m AC_48 -q`. **Expect** `6 failed, 2 passed` (checked): the two that
pass are "a created project writes no line" and the guard test, which already hold.

**4b. Add the `SecurityLog` port and pass the log to the handlers.** Add the `SecurityLog` Protocol to
`app/projects/application/ports.py` (the handlers import it). `register_error_handlers(app, security_log)` in `adapters/inbound/errors.py`
calls `refused(...)` in both handlers, and `composition/app.py` passes `security_log`. In `tests/test_projects_errors.py`
the two calls to `register_error_handlers` get a `FakeSecurityLog()`.

**Expect** `14 passed` in `test_projects_audit_api.py`, and the whole suite `305 passed, 46 skipped` (checked at the
build commit; the 46 are PostgreSQL tests, skipped without `TEST_DATABASE_URL`). With PostgreSQL the commit reports 351: **not run** here,
`TEST_DATABASE_URL` is not set.

Final code, copied from the files at `7481263`. Only what this task adds is quoted.

The event and the three ports (`ProjectEvent`, `AuditLog`, `People` and `SecurityLog`):

```python
# app/projects/application/ports.py
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
# app/projects/application/ports.py
class People(Protocol):
    def names_of(self, ids: list[str]) -> dict[str, tuple[str, str]]:
        """For each known id, (name, email) as they are now. Unknown ids are left out."""
        ...


class AuditLog(Protocol):
    def record(self, event: ProjectEvent) -> None:
        """Write one entry in the trail, in the request's own transaction."""
        ...


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

The call in `ProjectsService.create` (the method today; the `People` port in the constructor and the view it returns are from UC-P3):

```python
# app/projects/application/service.py, ProjectsService.create
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

The two bridges:

```python
# app/composition/bridges.py
class PeopleBridge:
    """Projects' People port, answered by Access's use case, on the same session as the request."""

    def __init__(self, access: AccessService):
        self._access = access

    def names_of(self, ids: list[str]) -> dict[str, tuple[str, str]]:
        return {p.id: (p.name, p.email) for p in self._access.people(ids)}


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

The wiring (`people` is shared with the service since UC-P3; at this task it was built inline for the audit bridge only):

```python
# app/composition/app.py, inside create_app
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

and `register_projects_error_handlers(app, security_log)` in the same function. The log, in the handlers:

```python
# app/projects/adapters/inbound/errors.py, register_error_handlers
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

## 4. Check it yourself

```
uv run pytest tests/test_projects_service.py -q          # 62 passed at 7481263 (19 at the build commit)
uv run pytest tests/test_projects_composition.py -q      # 6 passed (same at 7481263)
uv run pytest tests/test_projects_audit_api.py -q        # 14 passed (same at 7481263)
uv run pytest -q                                          # 468 passed, 47 skipped at 7481263 (305 passed, 46 skipped at the build commit)
TEST_DATABASE_URL=<the playground_test database> uv run pytest -q   # PostgreSQL run, before the pull request
```

Only the service file and the whole suite grew after the build commit (UC-P2 and UC-P3 added tests); the composition
and audit files have the same counts at `7481263`. Run `scripts/check.sh` from the repo root before you finish.

## 5. Where this leaves things

- Source: `app/projects/application/ports.py`, `app/projects/application/service.py`, `app/projects/adapters/inbound/errors.py`, `app/composition/bridges.py`, `app/composition/app.py`
- Tests: `tests/test_projects_service.py`, `tests/test_projects_composition.py`, `tests/test_projects_audit_api.py`, `tests/test_projects_errors.py`, `tests/fakes.py` (`FakeProjectsAudit`, `FakePeople`)
- ADR: 0013 (security log), 0015 (the Projects build plan). None new.
- UC-P2 reuses the same `ProjectEvent` for adding and removing a member (AC-30).

## Where the real build differs

- One commit (`58dc0f1`) holds this task with AC-85 and AC-89, which the summary table does not list for it.
- The stages here are an ordering made afterwards; the commit is one step. Stages 1 to 4 were checked by applying the
  commit's files in that order on its parent.
- The service file went from 19 tests at the build commit to 62 at `7481263` (UC-P2 and UC-P3), and the whole suite from
  305 passed, 46 skipped to 468 passed, 47 skipped. The composition (6) and audit (14) counts are the same at `7481263`.
- At the build commit the `People` bridge was built inline; `ProjectsService` took no `People` until UC-P3.

## Review

Not reviewed. Write `Reviewed by <name> at <hash>` here when the plan has been read against the code.
