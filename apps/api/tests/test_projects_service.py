"""ProjectsService.create with a fake repository (UC-P1 TSK-P1.3: AC-9, AC-10)."""

import pytest

from app.projects.application.service import ProjectsService
from app.projects.domain.caller import Caller
from app.projects.domain.errors import NotAnAdministrator
from tests.fakes import FakeProjects

ADMIN = Caller("acc-ada", is_administrator=True)
USER = Caller("acc-maya", is_administrator=False)


@pytest.fixture
def projects():
    return FakeProjects()


@pytest.fixture
def service(projects):
    return ProjectsService(projects)


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
