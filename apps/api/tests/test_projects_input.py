"""The input rules of creating a project: the name, the cap on first members (UC-P1 TSK-P1.5: AC-12, AC-91, AC-92)."""

import pytest

from app.projects.application.service import ProjectsService
from app.projects.domain.caller import Caller
from app.projects.domain.errors import InvalidProjectName, InvalidRequest, NotAnAdministrator
from app.projects.domain.name import clean_name
from app.projects.domain.project import Project
from tests.fakes import FakeAccountStatus, FakeProjects

ADMIN = Caller("acc-ada", is_administrator=True)
USER = Caller("acc-maya", is_administrator=False)


@pytest.mark.ac("AC-12")
@pytest.mark.parametrize("bad", ["", "   ", "\u00a0 ", "x" * 101, " " + "x" * 101 + " "])
def test_an_empty_blank_or_too_long_name_is_refused(bad):
    with pytest.raises(InvalidProjectName):
        clean_name(bad)


@pytest.mark.ac("AC-12")
def test_a_name_of_100_characters_is_accepted_and_the_spaces_around_it_are_removed():
    assert clean_name("x" * 100) == "x" * 100
    assert clean_name("  Alpha \t".replace("\t", " ")) == "Alpha"
    assert clean_name(" " + "x" * 100 + " ") == "x" * 100


@pytest.mark.ac("AC-12")
def test_the_length_is_counted_in_characters_not_bytes():
    assert clean_name("\U0001f600" * 100) == "\U0001f600" * 100
    assert clean_name("é" * 100) == "é" * 100
    with pytest.raises(InvalidProjectName):
        clean_name("\U0001f600" * 101)


@pytest.mark.ac("AC-91")
@pytest.mark.parametrize(
    "char", ["\n", "\t", "\r", "\x00", "\x7f", "\u202e", "\u202a", "\u2066", "\u2069", "\u200e", "\u200f", "\u061c"]
)
def test_a_name_with_a_control_or_bidirectional_character_is_refused(char):
    with pytest.raises(InvalidProjectName) as e:
        clean_name(f"Al{char}pha")
    assert "Alpha" not in e.value.message and char not in e.value.message


@pytest.mark.ac("AC-12")
def test_a_project_is_stored_with_the_trimmed_name():
    assert Project.create(ADMIN, "  Alpha  ", []).name == "Alpha"


@pytest.mark.ac("AC-12")
def test_the_service_refuses_a_bad_name_and_saves_nothing():
    repo = FakeProjects()
    with pytest.raises(InvalidProjectName):
        ProjectsService(repo, FakeAccountStatus()).create(ADMIN, "   ", [])
    assert repo.rows == {}


class ExplodingRepo:
    def add(self, project):
        raise AssertionError("the repository must not be asked")

    def by_id(self, project_id):
        raise AssertionError("the repository must not be asked")


@pytest.mark.ac("AC-92")
def test_more_than_50_first_members_is_refused_before_the_repository_is_asked():
    with pytest.raises(InvalidRequest):
        ProjectsService(ExplodingRepo(), FakeAccountStatus()).create(ADMIN, "Alpha", [f"acc-{i}" for i in range(51)])


@pytest.mark.ac("AC-92")
def test_50_first_members_are_accepted():
    repo = FakeProjects()
    p = ProjectsService(repo, FakeAccountStatus()).create(ADMIN, "Alpha", [f"acc-{i}" for i in range(50)])
    assert len(p.members) == 50 and repo.by_id(p.id) is p


@pytest.mark.ac("AC-92")
def test_duplicates_are_not_an_error_and_the_cap_counts_distinct_ids():
    p = ProjectsService(FakeProjects(), FakeAccountStatus()).create(
        ADMIN, "Alpha", [f"acc-{i % 50}" for i in range(80)]
    )
    assert len(p.members) == 50


@pytest.mark.ac("AC-11")
def test_the_role_is_checked_before_the_name_and_the_cap():
    with pytest.raises(NotAnAdministrator):
        ProjectsService(ExplodingRepo(), FakeAccountStatus()).create(USER, "\u202e", [f"acc-{i}" for i in range(51)])
