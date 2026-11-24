# Task P1.6: First members need an active account, each counted once

**Task ID:** TSK-P1.6 · **Use Case:** UC-P1 · **Criteria:** AC-13, AC-89 · **Code matched at:** `7481263`

What this does and why: [summary, task P1.6](summary.md#p16-first-members-need-an-active-account-each-counted-once).

Run from `apps/api/`: `uv run pytest tests/fakes.py tests/test_architecture.py tests/test_projects_api.py tests/test_projects_composition.py tests/test_projects_service.py -q`

Work test first in each step: write the test, run it, see it fail, then write the code.

---

## Step 1: the use case refuses an inactive first member (AC-13, AC-89)

**Test** (Unit):

First a fake for the port, so the use case can be tested with no Access:

```python
# apps/api/tests/fakes.py
class FakeAccountStatus:
    """Stands in for Projects' AccountStatus port. `active=None` means every id is an active account."""

    def __init__(self, active: set[str] | None = None):
        self.active = active
        self.asked: list[set[str]] = []

    def active_among(self, ids):
        self.asked.append(set(ids))
        return set(ids) if self.active is None else set(ids) & self.active
```

Then a helper that builds the service over fakes (the constructor has four arguments at `7481263`: TSK-P1.7 added the audit and
people ports):

```python
# apps/api/tests/test_projects_service.py
def service_with(active):
    projects, status = FakeProjects(), FakeAccountStatus(set(active))
    return ProjectsService(projects, status, FakeProjectsAudit(), FakePeople()), projects, status
```

Then the tests of the use case:

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-13")
@pytest.mark.parametrize("member", ["acc-pending", "acc-deactivated", "acc-unknown"])
def test_a_first_member_who_is_not_active_is_refused_with_one_answer_and_nothing_is_saved(member):
    service, projects, _ = service_with({"acc-maya"})
    with pytest.raises(MemberNotEligible) as refusal:
        service.create(ADMIN, "Alpha", [member])
    assert (refusal.value.code, refusal.value.message) == (
        "member_not_eligible",
        "That person cannot be added to or removed from this project.",
    )
    assert member not in str(refusal.value)
    assert projects.rows == {}
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-13")
def test_one_inactive_among_active_members_refuses_all_and_saves_nothing():
    service, projects, _ = service_with({"acc-maya", "acc-bob"})
    with pytest.raises(MemberNotEligible):
        service.create(ADMIN, "Alpha", ["acc-maya", "acc-gone", "acc-bob"])
    assert projects.rows == {}
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-13")
def test_eligibility_is_checked_after_authorisation_and_after_the_input_rules():
    service, projects, status = service_with(set())
    with pytest.raises(NotAnAdministrator):
        service.create(USER, "Alpha", ["acc-gone"])
    with pytest.raises(InvalidProjectName):
        service.create(ADMIN, "", ["acc-gone"])
    with pytest.raises(InvalidRequest):
        service.create(ADMIN, "Alpha", [f"acc-{i}" for i in range(51)])
    assert status.asked == [] and projects.rows == {}
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-89")
def test_naming_the_same_active_person_twice_makes_one_membership_and_asks_about_the_id_once():
    service, projects, status = service_with({"acc-maya"})
    p = service.create(ADMIN, "Alpha", ["acc-maya", "acc-maya"])
    assert len(p.memberships) == 1 and p.members == {"acc-maya"}
    assert projects.by_id(p.id) is p.project
    assert status.asked == [{"acc-maya"}]
```

```python
# apps/api/tests/test_projects_service.py
@pytest.mark.ac("AC-13")
def test_no_first_member_asks_nobody_and_is_accepted():
    service, _, status = service_with(set())
    assert service.create(ADMIN, "Alpha", []).members == frozenset()
    assert all(not asked for asked in status.asked)
```

The existing `ProjectsService(...)` calls in `tests/test_projects_service.py` and `tests/test_projects_input.py` now pass
`FakeAccountStatus()` as the second argument. First, name the error (the final text, below):

```python
# apps/api/app/projects/domain/errors.py
class MemberNotEligible(ProjectsError):
    """One answer for a first member who is pending, deactivated or unknown: it names no id and no status (AC-13)."""

    code = "member_not_eligible"

    def __init__(self):
        super().__init__("That person cannot be added to or removed from this project.")
```

**Code**:

Declare the port:

```python
# apps/api/app/projects/application/ports.py
class AccountStatus(Protocol):
    def active_among(self, ids: set[str]) -> set[str]:
        """Of these account ids, the ones whose people may be members."""
        ...
```

Give `ProjectsService` the port as its second argument (`self._accounts = accounts`; the constructor also takes the audit and
people ports, from TSK-P1.7), and add the check to `create`, after `Project.create` has applied the name and the cap. These are
the lines this task adds (the audit call after them is TSK-P1.7):

```python
# apps/api/app/projects/application/service.py, inside ProjectsService.create
        project = Project.create(caller, name, member_ids)
        named = set(project.members)  # each person once (AC-89)
        if named and not named <= self._accounts.active_among(named):
            raise MemberNotEligible  # pending, deactivated or unknown: one answer (AC-13)
        self._projects.add(project)
```

**Logic.** `set(project.members)` holds each person once, so Access is asked once for each id (AC-89). `named <= active_among(named)` is
true only if every person named is active. One missing person raises the one error, before the save, so nothing is written. An
empty set skips the question.

---

## Step 2: Access answers the port (AC-13)

**Test** (Unit and Architecture):

```python
# apps/api/tests/test_projects_composition.py
@pytest.mark.ac("AC-13")
def test_the_account_status_bridge_answers_through_accesss_own_is_active_rule():
    from app.access.application.service import AccessService
    from app.composition.bridges import AccountStatusBridge
    from tests.fakes import FakeAccounts, FakeAudit, FakeIdp, FakeUnitOfWork

    accounts = FakeAccounts()
    for acc_id, status in (("a", Status.active), ("p", Status.pending), ("d", Status.deactivated)):
        accounts.add(
            Account(acc_id, f"sub-{acc_id}", acc_id, f"{acc_id}@x.test", Role.user, status, datetime(2026, 1, 1), None)
        )
    access = AccessService(accounts, FakeAudit(), FakeIdp(), set(), uow=FakeUnitOfWork())
    bridge = AccountStatusBridge(access)
    assert bridge.active_among({"a", "p", "d", "unknown"}) == {"a"}
    assert bridge.active_among(set()) == set()
    assert isinstance(bridge.active_among({"a"}), set)
```

And an architecture test that no file of Projects imports another context, that the port imports nothing from Access, and that
the bridge does:

```python
# apps/api/tests/test_architecture.py
def test_projects_imports_no_other_context_only_composition_sees_both():
    # UC-P1 TSK-P1.6: Projects asks about accounts through its own AccountStatus port, answered by a bridge.
    for f in py_files(APP / "projects"):
        for mod in imports_of(f):
            assert not any(mod == f"app.{c}" or mod.startswith(f"app.{c}.") for c in contexts() if c != "projects"), (
                f"{f.relative_to(APP)} imports {mod}: Projects knows no other context (ADR 0002, 0010, 0015)"
            )
    ports = imports_of(APP / "projects" / "application" / "ports.py")
    assert not any(m.startswith("app.access") for m in ports)
    assert any(p.name == "bridges.py" for p in py_files(APP / "composition"))
    assert any(m.startswith("app.access") for m in imports_of(APP / "composition" / "bridges.py"))
```

**Code**:

Add the bridge to `app/composition/bridges.py`, with `from app.access.application.service import AccessService` at the top of the file:

```python
# apps/api/app/composition/bridges.py
class AccountStatusBridge:
    """Projects' AccountStatus port, answered by Access's use case, on the same session as the request."""

    def __init__(self, access: AccessService):
        self._access = access

    def active_among(self, ids: set[str]) -> set[str]:
        return set(self._access.active_among(list(ids)))
```

**Logic.** `AccessService.active_among` is TSK-P1.1. It uses the account's own `is_active` rule, so "active" means the same here as
everywhere. The bridge only turns Access's list into the set that Projects asked for.

---

## Step 3: wire it and answer 422 (AC-13, AC-89)

**Test** (API):

The HTTP tests, over the real app and database, with the `active_user(...)` and `register(...)` helpers that approve or leave an
account pending. First the helper that checks the one answer:

```python
# apps/api/tests/test_projects_api.py
def ineligible(r):
    assert r.status_code == 422
    assert r.json() == {
        "detail": {
            "code": "member_not_eligible",
            "message": "That person cannot be added to or removed from this project.",
        }
    }
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-13")
def test_a_pending_a_deactivated_and_an_unknown_account_get_the_identical_refusal_and_nothing_is_written(
    api, admin, engine
):
    _, pending_id = register(api, "sub-pen", "pen@x.test")
    _, gone_id = active_user(api, admin, "sub-gone", "gone@x.test")
    assert api.post(f"/accounts/{gone_id}/deactivate", headers=admin, json={"reason": "left"}).status_code == 200
    answers = []
    for member in (pending_id, gone_id, str(uuid.uuid4())):
        r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [member]})
        ineligible(r)
        assert member not in r.text
        answers.append((r.status_code, r.json()))
    assert answers[0] == answers[1] == answers[2]
    assert project_count(engine) == 0
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-13")
def test_one_active_and_one_inactive_member_refuses_all_and_writes_nothing(api, admin, engine):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    _, pending_id = register(api, "sub-pen", "pen@x.test")
    ineligible(api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id, pending_id]}))
    assert project_count(engine) == 0
    with Session(engine) as s:
        assert s.execute(text("SELECT count(*) FROM memberships")).scalar_one() == 0
```

```python
# apps/api/tests/test_projects_api.py
@pytest.mark.ac("AC-89")
def test_naming_the_same_active_person_twice_makes_one_membership(api, admin, engine):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id, maya_id]})
    assert (r.status_code, r.json()["members"]) == (201, [{"id": maya_id, "name": "maya"}])
    with Session(engine) as s:
        assert s.execute(text("SELECT count(*) FROM memberships")).scalar_one() == 1
```

The 51-member test of TSK-P1.5 changes to register 51 real active accounts, because from now on the ids are looked up.

**Code**:

In `app/composition/app.py` the service of a request is built over the request's own session and Access service, so the check
and the save are in one transaction. This is the function at the commit above; its audit and people arguments were added by
TSK-P1.7, and the one this task adds is `AccountStatusBridge(access)`:

```python
# apps/api/app/composition/app.py
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

Map the error to 422. Without the entry the answer is 400:

```python
# apps/api/app/projects/adapters/inbound/errors.py, in the status map
    MemberNotEligible: 422,
```

**Logic.** The bridge shares the request's session, so the lookup and the save see the same data. The status map is the only place that
knows `MemberNotEligible` is a 422.
