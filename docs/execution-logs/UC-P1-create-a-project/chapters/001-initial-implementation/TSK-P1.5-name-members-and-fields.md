# Task P1.5: Check the name, the members and the fields

**Task ID:** TSK-P1.5 · **Use Case:** UC-P1 · **Criteria:** AC-12, AC-91, AC-92, AC-93 · **Code matched at:** `7481263`

What this does and why: [summary, task P1.5](summary.md#p15-check-the-name-the-members-and-the-fields).

Run from `apps/api/`: `uv run pytest tests/test_projects_api.py tests/test_projects_input.py -q`

Work test first in each step: write the test, run it, see it fail, then write the code.

---

## Step 1: the length rule (AC-12)

**Test** (Unit):

First name the error in `app/projects/domain/errors.py`:

```python
# apps/api/app/projects/domain/errors.py
class InvalidProjectName(ProjectsError):
    code = "invalid_project_name"
```

Then these tests, each marked `@pytest.mark.ac("AC-12")` (two of the several in the file):

```python
# apps/api/tests/test_projects_input.py
@pytest.mark.ac("AC-12")
@pytest.mark.parametrize("bad", ["", "   ", "\u00a0 ", "x" * 101, " " + "x" * 101 + " "])
def test_an_empty_blank_or_too_long_name_is_refused(bad):
    with pytest.raises(InvalidProjectName):
        clean_name(bad)
```

```python
# apps/api/tests/test_projects_input.py
@pytest.mark.ac("AC-12")
def test_the_length_is_counted_in_characters_not_bytes():
    assert clean_name("\U0001f600" * 100) == "\U0001f600" * 100
    assert clean_name("é" * 100) == "é" * 100
    with pytest.raises(InvalidProjectName):
        clean_name("\U0001f600" * 101)
```

**Code**:

This is the stage 1 shape of `app/projects/domain/name.py`, not the final file:

```python
# app/projects/domain/name.py, stage 1
from app.projects.domain.errors import InvalidProjectName

MAX_NAME_LENGTH = 100


def clean_name(name: str) -> str:
    text = name.strip()
    if not 1 <= len(text) <= MAX_NAME_LENGTH:
        raise InvalidProjectName(f"A project name has 1 to {MAX_NAME_LENGTH} characters.")
    return text
```

**Logic.** Trim first, then count. `len` on a Python `str` counts characters, not bytes.

---

## Step 2: the character rule (AC-91)

**Test** (Unit):

```python
# apps/api/tests/test_projects_input.py
@pytest.mark.ac("AC-91")
@pytest.mark.parametrize(
    "char", ["\n", "\t", "\r", "\x00", "\x7f", "\u202e", "\u202a", "\u2066", "\u2069", "\u200e", "\u200f", "\u061c"]
)
def test_a_name_with_a_control_or_bidirectional_character_is_refused(char):
    with pytest.raises(InvalidProjectName) as e:
        clean_name(f"Al{char}pha")
    assert "Alpha" not in e.value.message and char not in e.value.message
```

**Code**:

The final file:

```python
# apps/api/app/projects/domain/name.py
"""The rule of a project's name (AC-12, AC-91): plain text, trimmed, 1 to 100 characters. Pure."""

import unicodedata

from app.projects.domain.errors import InvalidProjectName

MAX_NAME_LENGTH = 100
# Bidirectional marks, embeddings, overrides and isolates: they can make a name read as another one.
BIDIRECTIONAL = frozenset("‎‏؜" + "".join(map(chr, [*range(0x202A, 0x202F), *range(0x2066, 0x206A)])))


def clean_name(name: str) -> str:
    """The trimmed name, or InvalidProjectName. The length is counted in Unicode characters after trimming. The
    message never repeats the name: it would carry the hidden characters to the log and the screen."""
    text = name.strip()
    if not 1 <= len(text) <= MAX_NAME_LENGTH:
        raise InvalidProjectName(f"A project name has 1 to {MAX_NAME_LENGTH} characters.")
    if any(c in BIDIRECTIONAL or unicodedata.category(c) == "Cc" for c in text):
        raise InvalidProjectName("A project name is plain text, with no control or direction characters.")
    return text
```

In `Project.create` the first line of the body is the call, with `from app.projects.domain.name import clean_name` at the top
of the file:

```python
# app/projects/domain/project.py, inside Project.create
        name = clean_name(name)
```

**Logic.** The control characters are category `Cc`. The direction marks are category `Cf`, which also holds harmless characters, so the
marks are listed by hand and not all of `Cf` is refused. The message never repeats the name: it would carry the hidden
characters into the log and onto the screen.

One call, so the rule has one caller and one home.

---

## Step 3: the cap on first members (AC-92)

**Test** (Unit and API):

First name the error in `app/projects/domain/errors.py`. `InvalidRequest` is the one answer for input that is wrong in shape,
not in one field:

```python
# apps/api/app/projects/domain/errors.py
class InvalidRequest(ProjectsError):
    code = "invalid_request"
```

```python
# apps/api/tests/test_projects_input.py
@pytest.mark.ac("AC-92")
def test_more_than_50_first_members_is_refused_before_the_repository_is_asked():
    with pytest.raises(InvalidRequest):
        ProjectsService(ExplodingRepo(), FakeAccountStatus(), FakeProjectsAudit(), FakePeople()).create(
            ADMIN, "Alpha", [f"acc-{i}" for i in range(51)]
        )
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-92")
def test_51_first_members_are_refused_and_50_are_accepted(api, admin, engine):
    ids = [active_user(api, admin, f"sub-{i}", f"u{i}@x.test")[1] for i in range(51)]
    refused(api.post("/projects", headers=admin, json={"name": "Alpha", "members": ids}), "invalid_request")
    assert project_count(engine) == 0
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": ids[:50]})
    assert (r.status_code, len(r.json()["members"])) == (201, 50)
```

**Code**:

```python
# app/projects/domain/project.py
MAX_FIRST_MEMBERS = 50
```

```python
# apps/api/app/projects/domain/project.py, Project.create
    @classmethod
    def create(cls, caller: Caller, name: str, member_ids: Iterable[str]) -> "Project":
        """A new project. Its id is random, so it reveals nothing about count or order (ADR 0015). Only the people
        named are members: the creator is one only if named (AC-10). The name is trimmed and checked (AC-12, AC-91);
        at most 50 distinct first members (AC-92)."""
        name = clean_name(name)
        ids = tuple(dict.fromkeys(member_ids))
        if len(ids) > MAX_FIRST_MEMBERS:
            raise InvalidRequest(f"A project starts with at most {MAX_FIRST_MEMBERS} members.")
        memberships = tuple(Membership(i, added_by=caller.account_id) for i in ids)
        return cls(str(uuid.uuid4()), name, caller.account_id, memberships)
```

In `app/projects/adapters/inbound/errors.py` the map holds these two entries (the others in the file are other tasks'). Without
an entry an unmapped rule answers 400:

```python
# app/projects/adapters/inbound/errors.py
    InvalidProjectName: 422,
    InvalidRequest: 422,
```

**Logic.** The list is de-duplicated first (`dict.fromkeys`), then counted: 80 ids naming 50 people are accepted, 50 is accepted and 51 is
refused. The file also holds the later `add_member` and `remove_member` of UC-P2, and its `errors` import also names
`MemberNotEligible`.

---

## Step 4: unknown fields, and the role before the body (AC-93, AC-11)

**Test** (API):

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-93")
@pytest.mark.parametrize(
    "field,value",
    [("id", "p-1"), ("created_by", "acc-x"), ("added_by", "acc-x"), ("created_at", "2020-01-01"), ("files", ["f"])],
)
def test_an_unknown_field_is_refused_not_ignored_and_not_echoed(api, admin, engine, field, value):
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [], field: value})
    refused(r, "invalid_request")
    assert str(value) not in r.text and "Alpha" not in r.text
    assert project_count(engine) == 0
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-93")
def test_the_known_fields_still_work(api, admin):
    assert api.post("/projects", headers=admin, json={"name": "Alpha", "members": []}).status_code == 201
    assert api.post("/projects", headers=admin, json={"name": "Beta"}).status_code == 201
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-11")
def test_the_role_is_checked_before_unknown_fields_and_before_a_bad_name(api, admin, engine):
    maya_h, _ = active_user(api, admin, "sub-maya", "maya@x.test")
    r = api.post("/projects", headers=maya_h, json={"name": "", "members": [], "id": "p-1"})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 0
```

**Code**:

Forbid extra fields in the schema:

```python
# apps/api/app/projects/adapters/inbound/schemas.py
class CreateProjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # mass assignment: an unknown field is refused, not ignored (AC-93)

    name: str
    members: list[str] = []  # the first members, as account ids
```

Split the role check out of `create`, so a caller that bypasses the route is refused just the same (`create` calls it as its
first line):

```python
# apps/api/app/projects/application/service.py, ProjectsService.authorise_creation
    @staticmethod
    def authorise_creation(caller: Caller) -> None:
        """Only an administrator creates a project. The route calls it before it reads the body (AC-11, AC-93)."""
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")
```

The route reads the raw object, checks the role, then validates:

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

A body that is not even an object: FastAPI would refuse it with an answer that echoes the input, so `/projects` gets the same
shape of refusal:

```python
# apps/api/app/projects/adapters/inbound/errors.py, inside register_error_handlers
    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        """A body that is not even a JSON object, on /projects only. FastAPI's own answer echoes the input."""
        if request.url.path != "/projects" and not request.url.path.startswith("/projects/"):
            return await request_validation_exception_handler(request, exc)
        error = InvalidRequest("The request is not valid.")
        refused(request, error.code)
        return JSONResponse({"detail": {"code": error.code, "message": error.message}}, status_code=422)
```

**Logic.** An unknown field is refused, not ignored (AC-93). The role is checked before the body is read, so a person who may not create a
project gets 403 even with a bad name and an unknown field (AC-11). The route cannot let FastAPI validate the body first, so it
takes the raw object. A refusal of the input is one body shape, `{"detail": {"code", "message"}}`, status 422, with no detail.

The `refused(...)` line in the last handler, with the `refused` helper and the `security_log` argument it uses, belong to TSK-P1.7
(the security log, AC-48). At the commit that built this task the handler had no such line. No test in this task sends a body that
is not an object, so this handler is not pinned here.
