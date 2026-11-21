"""ProjectsService.create with a fake repository (UC-P1 TSK-P1.3: AC-9, AC-10)."""

import pytest

from app.projects.application.ports import ProjectEvent
from app.projects.application.service import ProjectsService
from app.projects.domain.caller import Caller
from app.projects.domain.errors import InvalidProjectName, InvalidRequest, MemberNotEligible, NotAnAdministrator
from tests.fakes import FakeAccountStatus, FakePeople, FakeProjects, FakeProjectsAudit

ADMIN = Caller("acc-ada", is_administrator=True)
USER = Caller("acc-maya", is_administrator=False)


@pytest.fixture
def projects():
    return FakeProjects()


@pytest.fixture
def service(projects):
    return ProjectsService(projects, FakeAccountStatus(), FakeProjectsAudit(), FakePeople())


@pytest.mark.ac("AC-9")
def test_create_saves_the_project_with_its_first_members_and_returns_it(service, projects):
    p = service.create(ADMIN, "Alpha", ["acc-maya"])
    assert projects.by_id(p.id) is p.project
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
    return ProjectsService(projects, status, FakeProjectsAudit(), FakePeople()), projects, status


@pytest.mark.ac("AC-13")
@pytest.mark.parametrize("member", ["acc-pending", "acc-deactivated", "acc-unknown"])
def test_a_first_member_who_is_not_active_is_refused_with_one_answer_and_nothing_is_saved(member):
    service, projects, _ = service_with({"acc-maya"})
    with pytest.raises(MemberNotEligible) as refusal:
        service.create(ADMIN, "Alpha", [member])
    assert (refusal.value.code, refusal.value.message) == ("member_not_eligible", "That person cannot be added to or removed from this project.")
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
    assert projects.by_id(p.id) is p.project
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
    return ProjectsService(projects, FakeAccountStatus(active), audit, FakePeople()), projects, audit


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
    assert audit.held_when_recorded == [p.project]
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


# UC-P3: list and open (TSK-P3.1 to TSK-P3.3)

from app.projects.domain.errors import ProjectNotFound  # noqa: E402


@pytest.fixture
def three(service, projects):
    """Alpha (Maya), Beta (Maya and Bob), Gamma (nobody)."""
    alpha = service.create(ADMIN, "Alpha", ["acc-maya"])
    beta = service.create(ADMIN, "Beta", ["acc-maya", "acc-bob"])
    gamma = service.create(ADMIN, "Gamma", [])
    return alpha, beta, gamma


@pytest.mark.ac("AC-55")
def test_a_user_lists_only_the_projects_they_are_a_member_of(service, three):
    alpha, beta, _ = three
    assert {p.id for p in service.list_projects(Caller("acc-maya", False))} == {alpha.id, beta.id}
    assert {p.id for p in service.list_projects(Caller("acc-bob", False))} == {beta.id}


@pytest.mark.ac("AC-55")
@pytest.mark.ac("AC-28")
def test_an_administrator_lists_every_project_member_or_not(service, three):
    assert {p.id for p in service.list_projects(Caller("acc-other", True))} == {p.id for p in three}


@pytest.mark.ac("AC-86")
def test_a_user_in_no_project_gets_an_empty_list_not_an_error(service, three):
    assert service.list_projects(Caller("acc-nobody", False)) == []


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-26")
def test_a_member_and_an_administrator_open_a_project(service, three):
    alpha, _, _ = three
    assert service.open_project(Caller("acc-maya", False), alpha.id).project is alpha.project
    assert service.open_project(Caller("acc-other", True), alpha.id).project is alpha.project


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-27")
@pytest.mark.parametrize(
    "project_id", ["not-a-project", "", "x" * 5000, "a\x00b", "00000000-0000-0000-0000-000000000000"]
)
def test_a_missing_or_malformed_id_is_project_not_found(service, three, project_id):
    with pytest.raises(ProjectNotFound):
        service.open_project(Caller("acc-maya", False), project_id)


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-27")
def test_a_project_the_person_may_not_see_is_project_not_found_too(service, three):
    _, beta, gamma = three
    for hidden in (beta, gamma):
        with pytest.raises(ProjectNotFound):
            service.open_project(Caller("acc-eve", False), hidden.id)


def test_reading_changes_nothing_and_writes_no_audit_entry(projects):
    audit = FakeProjectsAudit()
    svc = ProjectsService(projects, FakeAccountStatus(), audit, FakePeople())
    p = svc.create(ADMIN, "Alpha", ["acc-maya"])
    audit.events.clear()
    svc.list_projects(USER)
    svc.open_project(ADMIN, p.id)
    assert audit.events == []


# UC-P2: add_member and remove_member (TSK-P2.1 to TSK-P2.5)


def member_world(active=None, known=None):
    """A project of Maya's, made by Ada, and a service over fakes. Returns (service, project, projects, status, audit)."""
    projects, status = FakeProjects(), FakeAccountStatus(active)
    audit = FakeProjectsAudit(projects)
    service = ProjectsService(projects, status, audit, FakePeople())
    project = service.create(ADMIN, "Alpha", ["acc-maya"])
    audit.events.clear()
    audit.held_when_recorded.clear()
    status.asked.clear()
    return service, project, projects, status, audit


@pytest.mark.ac("AC-17")
def test_add_member_makes_an_active_person_a_member_and_returns_the_project():
    service, project, projects, _, _ = member_world()
    got = service.add_member(ADMIN, project.id, "acc-bob")
    assert got.members == {"acc-maya", "acc-bob"}
    assert projects.by_id(project.id).members == {"acc-maya", "acc-bob"}


@pytest.mark.ac("AC-30")
def test_a_real_addition_writes_one_event_after_the_change_is_saved():
    service, project, _, _, audit = member_world()
    service.add_member(ADMIN, project.id, "acc-bob")
    assert audit.events == [ProjectEvent("add_member", "acc-ada", project.id, "Alpha", ("acc-bob",))]
    assert audit.held_when_recorded[0].members == {"acc-maya", "acc-bob"}


@pytest.mark.ac("AC-18")
@pytest.mark.parametrize("who", ["acc-pending", "acc-deactivated", "acc-unknown"])
def test_add_member_refuses_a_person_who_is_not_active_with_one_answer_and_changes_nothing(who):
    service, project, projects, _, audit = member_world({"acc-maya", "acc-bob"})
    with pytest.raises(MemberNotEligible) as refusal:
        service.add_member(ADMIN, project.id, who)
    assert refusal.value.code == "member_not_eligible" and who not in refusal.value.message
    assert projects.by_id(project.id).members == {"acc-maya"}
    assert audit.events == []


@pytest.mark.ac("AC-88")
def test_adding_an_existing_member_changes_nothing_writes_no_event_and_returns_the_same_members():
    service, project, projects, _, audit = member_world()
    got = service.add_member(ADMIN, project.id, "acc-maya")
    assert got.members == {"acc-maya"}
    assert audit.events == [] and projects.added == []


@pytest.mark.ac("AC-20")
@pytest.mark.ac("AC-30")
def test_remove_member_takes_a_member_out_and_writes_one_event():
    service, project, projects, status, audit = member_world()
    got = service.remove_member(ADMIN, project.id, "acc-maya")
    assert got.members == frozenset() and projects.by_id(project.id).members == frozenset()
    assert audit.events == [ProjectEvent("remove_member", "acc-ada", project.id, "Alpha", ("acc-maya",))]
    assert status.asked == []  # an administrator may remove anyone: Access is not asked


@pytest.mark.ac("AC-87")
def test_removing_a_person_who_is_not_a_member_is_refused_and_writes_nothing():
    service, project, projects, _, audit = member_world()
    with pytest.raises(MemberNotEligible):
        service.remove_member(ADMIN, project.id, "acc-bob")
    assert projects.by_id(project.id).members == {"acc-maya"} and audit.events == []


@pytest.mark.ac("AC-60")
@pytest.mark.ac("AC-32")
@pytest.mark.parametrize("change", ["add", "remove"])
def test_a_member_who_is_not_an_administrator_is_refused_and_nothing_changes(change):
    service, project, projects, status, audit = member_world()
    with pytest.raises(NotAnAdministrator):
        if change == "add":
            service.add_member(USER, project.id, "acc-bob")
        else:
            service.remove_member(USER, project.id, "acc-maya")
    assert projects.by_id(project.id).members == {"acc-maya"} and audit.events == [] and status.asked == []


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-84")
@pytest.mark.parametrize("change", ["add", "remove"])
@pytest.mark.parametrize("project_id", ["exists", "00000000-0000-4000-8000-000000000000", "not-a-uuid", ""])
def test_someone_who_may_not_see_the_project_gets_project_not_found_whatever_the_id(change, project_id):
    from app.projects.domain.errors import ProjectNotFound

    service, project, projects, status, audit = member_world()
    outsider = Caller("acc-eve", is_administrator=False)
    pid = project.id if project_id == "exists" else project_id
    with pytest.raises(ProjectNotFound):
        if change == "add":
            service.add_member(outsider, pid, "acc-bob")
        else:
            service.remove_member(outsider, pid, "acc-maya")
    assert projects.by_id(project.id).members == {"acc-maya"} and audit.events == [] and status.asked == []


@pytest.mark.ac("AC-84")
def test_an_administrator_changing_a_missing_project_gets_project_not_found():
    from app.projects.domain.errors import ProjectNotFound

    service, *_ = member_world()
    with pytest.raises(ProjectNotFound):
        service.add_member(ADMIN, "not-a-uuid", "acc-bob")


@pytest.mark.ac("AC-60")
def test_visibility_is_checked_before_the_role_so_a_non_member_is_not_told_it_exists():
    """A member (not an administrator) gets forbidden; a stranger gets not found (the order of UC-P2 step 4)."""
    from app.projects.domain.errors import ProjectNotFound

    service, project, *_ = member_world()
    with pytest.raises(NotAnAdministrator):
        service.authorise_member_change(Caller("acc-maya", False), project.id)
    with pytest.raises(ProjectNotFound):
        service.authorise_member_change(Caller("acc-eve", False), project.id)
    assert service.authorise_member_change(ADMIN, project.id).id == project.id


@pytest.mark.ac("AC-90")
def test_the_loser_of_a_race_is_treated_as_already_a_member_and_writes_no_event():
    service, project, projects, _, audit = member_world()
    projects.lose_the_race = True  # the repository says another request inserted the row first
    got = service.add_member(ADMIN, project.id, "acc-bob")
    assert "acc-bob" in got.members
    assert audit.events == []


# ADR 0016: the answers carry the names of the members, looked up once for each answer

KNOWN = {"acc-maya": ("Maya", "maya@x.test"), "acc-bob": ("Bob", "bob@x.test"), "acc-ada": ("Ada", "ada@x.test")}


def named_world(known=None):
    projects, people = FakeProjects(), FakePeople(dict(KNOWN if known is None else known))
    service = ProjectsService(projects, FakeAccountStatus(), FakeProjectsAudit(), people)
    return service, people


@pytest.mark.ac("AC-9")
def test_create_returns_the_project_with_the_names_of_its_first_members_from_one_lookup():
    service, people = named_world()
    view = service.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    assert view.names == {"acc-maya": "Maya", "acc-bob": "Bob"}
    assert people.asked == [{"acc-maya", "acc-bob"}]


@pytest.mark.ac("AC-10")
def test_create_with_no_first_member_looks_up_nobody():
    service, people = named_world()
    assert service.create(ADMIN, "Alpha", []).names == {}
    assert people.asked == []


@pytest.mark.ac("AC-28")
def test_an_id_with_no_known_name_keeps_the_id_and_has_a_null_name():
    service, _ = named_world({"acc-maya": ("Maya", "maya@x.test")})
    view = service.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    assert view.names == {"acc-maya": "Maya", "acc-bob": None}


@pytest.mark.ac("AC-55")
def test_the_list_looks_names_up_once_for_the_members_of_all_the_projects():
    service, people = named_world()
    service.create(ADMIN, "Alpha", ["acc-maya"])
    service.create(ADMIN, "Beta", ["acc-maya", "acc-bob"])
    service.create(ADMIN, "Gamma", [])
    people.asked.clear()
    views = service.list_projects(ADMIN)
    assert len(views) == 3
    assert people.asked == [{"acc-maya", "acc-bob"}]  # one call for the union, not one for each project
    assert all(set(v.names) == set(v.members) for v in views)


@pytest.mark.ac("AC-86")
def test_an_empty_list_has_no_names_and_needs_no_lookup():
    service, people = named_world()
    assert service.list_projects(USER) == []
    assert people.asked == []


@pytest.mark.ac("AC-26")
def test_open_returns_the_project_with_the_names_of_its_members_from_one_lookup():
    service, people = named_world()
    made = service.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    people.asked.clear()
    view = service.open_project(ADMIN, made.id)
    assert view.names == {"acc-maya": "Maya", "acc-bob": "Bob"} and people.asked == [{"acc-maya", "acc-bob"}]


@pytest.mark.ac("AC-26")
def test_a_renamed_person_shows_the_new_name_at_the_next_read():
    service, people = named_world()
    made = service.create(ADMIN, "Alpha", ["acc-maya"])
    people.known["acc-maya"] = ("Maya Lopez", "maya@x.test")
    assert service.open_project(ADMIN, made.id).names == {"acc-maya": "Maya Lopez"}


@pytest.mark.ac("AC-27")
def test_a_refused_open_looks_nobody_up():
    from app.projects.domain.errors import ProjectNotFound

    service, people = named_world()
    with pytest.raises(ProjectNotFound):
        service.open_project(ADMIN, "not-a-uuid")
    assert people.asked == []


@pytest.mark.ac("AC-17")
def test_add_member_returns_the_project_with_the_names_after_the_change():
    service, people = named_world()
    made = service.create(ADMIN, "Alpha", ["acc-maya"])
    people.asked.clear()
    view = service.add_member(ADMIN, made.id, "acc-bob")
    assert view.names == {"acc-maya": "Maya", "acc-bob": "Bob"} and people.asked == [{"acc-maya", "acc-bob"}]


@pytest.mark.ac("AC-88")
def test_adding_an_existing_member_returns_the_names_too():
    service, _ = named_world()
    made = service.create(ADMIN, "Alpha", ["acc-maya"])
    assert service.add_member(ADMIN, made.id, "acc-maya").names == {"acc-maya": "Maya"}


@pytest.mark.ac("AC-20")
def test_remove_member_returns_the_project_with_the_names_of_who_is_left():
    service, people = named_world()
    made = service.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    people.asked.clear()
    view = service.remove_member(ADMIN, made.id, "acc-maya")
    assert view.names == {"acc-bob": "Bob"} and people.asked == [{"acc-bob"}]
