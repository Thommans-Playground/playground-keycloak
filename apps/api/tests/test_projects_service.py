"""ProjectsService.create with a fake repository (UC-P1 TSK-P1.3: AC-9, AC-10)."""

import pytest

from app.projects.application.ports import ProjectEvent
from app.projects.application.service import ProjectsService
from app.projects.domain.caller import Caller
from app.projects.domain.errors import InvalidProjectName, InvalidRequest, MemberNotEligible, NotAnAdministrator
from tests.fakes import FakeAccountStatus, FakeProjects, FakeProjectsAudit

ADMIN = Caller("acc-ada", is_administrator=True)
USER = Caller("acc-maya", is_administrator=False)


@pytest.fixture
def projects():
    return FakeProjects()


@pytest.fixture
def service(projects):
    return ProjectsService(projects, FakeAccountStatus(), FakeProjectsAudit())


@pytest.mark.ac("AC-9")
def test_create_saves_the_project_with_its_first_members_and_returns_it(service, projects):
    p = service.create(ADMIN, "Alpha", ["acc-maya"])
    assert projects.by_id(p.id) is p
    assert (p.name, p.created_by, p.members) == ("Alpha", "acc-ada", {"acc-maya"})


@pytest.mark.ac("AC-10")
def test_create_with_the_administrator_as_first_member(service, projects):
    p = service.create(ADMIN, "Alpha", ["acc-ada"])
    assert projects.by_id(p.id).members == {"acc-ada"}


@pytest.mark.ac("AC-10")
def test_create_with_no_first_member(service, projects):
    p = service.create(ADMIN, "Alpha", [])
    assert projects.by_id(p.id).members == frozenset()


@pytest.mark.ac("AC-11")
def test_create_refuses_a_caller_who_is_not_an_administrator_and_saves_nothing(service, projects):
    with pytest.raises(NotAnAdministrator):
        service.create(USER, "Alpha", ["acc-maya"])
    assert projects.rows == {}


@pytest.mark.ac("AC-11")
def test_create_checks_the_role_before_the_input(service, projects):
    with pytest.raises(NotAnAdministrator):  # the name and the members are not looked at
        service.create(USER, "", ["", "not-an-account"])
    assert projects.rows == {}


# AC-13, AC-89: a first member must have an active account, and each is counted once (UC-P1 TSK-P1.6)


def service_with(active):
    projects, status = FakeProjects(), FakeAccountStatus(set(active))
    return ProjectsService(projects, status, FakeProjectsAudit()), projects, status


@pytest.mark.ac("AC-13")
@pytest.mark.parametrize("member", ["acc-pending", "acc-deactivated", "acc-unknown"])
def test_a_first_member_who_is_not_active_is_refused_with_one_answer_and_nothing_is_saved(member):
    service, projects, _ = service_with({"acc-maya"})
    with pytest.raises(MemberNotEligible) as refusal:
        service.create(ADMIN, "Alpha", [member])
    assert (refusal.value.code, refusal.value.message) == ("member_not_eligible", "A first member cannot be added.")
    assert member not in str(refusal.value)
    assert projects.rows == {}


@pytest.mark.ac("AC-13")
def test_one_inactive_among_active_members_refuses_all_and_saves_nothing():
    service, projects, _ = service_with({"acc-maya", "acc-bob"})
    with pytest.raises(MemberNotEligible):
        service.create(ADMIN, "Alpha", ["acc-maya", "acc-gone", "acc-bob"])
    assert projects.rows == {}


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


@pytest.mark.ac("AC-89")
def test_naming_the_same_active_person_twice_makes_one_membership_and_asks_about_the_id_once():
    service, projects, status = service_with({"acc-maya"})
    p = service.create(ADMIN, "Alpha", ["acc-maya", "acc-maya"])
    assert len(p.memberships) == 1 and p.members == {"acc-maya"}
    assert projects.by_id(p.id) is p
    assert status.asked == [{"acc-maya"}]


@pytest.mark.ac("AC-13")
def test_no_first_member_asks_nobody_and_is_accepted():
    service, _, status = service_with(set())
    assert service.create(ADMIN, "Alpha", []).members == frozenset()
    assert all(not asked for asked in status.asked)


# AC-29, AC-89: creating a project writes one audit entry, after saving, and only when it was created (TSK-P1.7)


def audited(active=None):
    projects = FakeProjects()
    audit = FakeProjectsAudit(projects)
    return ProjectsService(projects, FakeAccountStatus(active), audit), projects, audit


@pytest.mark.ac("AC-29")
def test_create_writes_one_event_with_the_actor_the_project_and_the_first_members():
    service, _, audit = audited()
    p = service.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    assert audit.events == [ProjectEvent("create_project", "acc-ada", p.id, "Alpha", ("acc-maya", "acc-bob"))]
    assert audit.events[0].reason is None


@pytest.mark.ac("AC-29")
def test_the_event_is_written_after_the_project_is_saved_and_carries_the_trimmed_name():
    service, _, audit = audited()
    p = service.create(ADMIN, "  Alpha  ", [])
    assert audit.held_when_recorded == [p]
    assert (audit.events[0].project_name, audit.events[0].member_ids) == ("Alpha", ())


@pytest.mark.ac("AC-89")
def test_a_person_named_twice_is_in_the_event_once():
    service, _, audit = audited()
    service.create(ADMIN, "Alpha", ["acc-maya", "acc-maya", "acc-bob"])
    assert audit.events[0].member_ids == ("acc-maya", "acc-bob")


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
