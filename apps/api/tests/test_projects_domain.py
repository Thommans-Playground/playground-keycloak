"""The rules of the Project aggregate, with no database and no HTTP (UC-P1 TSK-P1.3: AC-9, AC-10)."""

import uuid

import pytest

from app.projects.domain.caller import Caller
from app.projects.domain.project import Membership, Project

ADMIN = Caller("acc-ada", is_administrator=True)


@pytest.mark.ac("AC-9")
def test_a_project_has_the_name_the_creator_and_the_named_first_members():
    p = Project.create(ADMIN, "Alpha", {"acc-maya", "acc-bob"})
    assert (p.name, p.created_by) == ("Alpha", "acc-ada")
    assert p.members == {"acc-maya", "acc-bob"}


@pytest.mark.ac("AC-9")
def test_each_first_member_is_added_by_the_creator():
    p = Project.create(ADMIN, "Alpha", ["acc-maya"])
    assert p.memberships == (Membership("acc-maya", added_by="acc-ada"),)


@pytest.mark.ac("AC-10")
def test_an_administrator_who_names_themselves_is_a_member():
    assert Project.create(ADMIN, "Alpha", ["acc-ada"]).members == {"acc-ada"}


@pytest.mark.ac("AC-10")
def test_an_administrator_who_names_nobody_makes_a_project_with_no_member():
    p = Project.create(ADMIN, "Alpha", [])
    assert p.members == frozenset() and p.memberships == ()


def test_the_creator_is_not_a_member_unless_named():
    assert "acc-ada" not in Project.create(ADMIN, "Alpha", ["acc-maya"]).members


def test_the_id_is_a_random_uuid_made_in_the_domain():
    ids = {Project.create(ADMIN, "Alpha", []).id for _ in range(20)}
    assert len(ids) == 20
    assert all(uuid.UUID(i).version == 4 and str(uuid.UUID(i)) == i for i in ids)
