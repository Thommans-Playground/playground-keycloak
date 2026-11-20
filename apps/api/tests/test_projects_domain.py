"""The rules of the Project aggregate, with no database and no HTTP (UC-P1 TSK-P1.3: AC-9, AC-10)."""

import uuid

import pytest

from app.projects.domain.caller import Caller
from app.projects.domain.project import Membership, Project, can_see

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


# RULE-P4: only members and administrators see inside a project (UC-P3 TSK-P3.2, TSK-P3.3)


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-26")
def test_a_member_sees_the_project():
    p = Project.create(ADMIN, "Alpha", ["acc-maya"])
    assert can_see(Caller("acc-maya", is_administrator=False), p) is True


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-28")
def test_an_administrator_who_is_not_a_member_sees_the_project():
    p = Project.create(ADMIN, "Alpha", ["acc-maya"])
    assert can_see(Caller("acc-other-admin", is_administrator=True), p) is True


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-26")
def test_a_person_who_is_neither_a_member_nor_an_administrator_does_not_see_the_project():
    p = Project.create(ADMIN, "Alpha", ["acc-maya"])
    assert can_see(Caller("acc-bob", is_administrator=False), p) is False
    assert can_see(Caller("acc-bob", is_administrator=False), Project.create(ADMIN, "Empty", [])) is False


# UC-P2: adding and removing a member (TSK-P2.1, TSK-P2.2). Each returns the new project, and says if anything changed.


@pytest.mark.ac("AC-17")
def test_add_member_adds_a_person_who_is_not_a_member_and_says_it_changed():
    p = Project.create(ADMIN, "Alpha", ["acc-maya"])
    got, changed = p.add_member(ADMIN, "acc-bob")
    assert changed is True
    assert got.members == {"acc-maya", "acc-bob"}
    assert Membership("acc-bob", added_by="acc-ada") in got.memberships
    assert p.members == {"acc-maya"}  # the original is not touched


@pytest.mark.ac("AC-88")
def test_add_member_of_an_existing_member_changes_nothing_and_says_so():
    p = Project.create(ADMIN, "Alpha", ["acc-maya"])
    got, changed = p.add_member(ADMIN, "acc-maya")
    assert changed is False
    assert got == p


@pytest.mark.ac("AC-20")
def test_remove_member_takes_the_person_out_and_leaves_the_others():
    p = Project.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    assert p.remove_member("acc-maya").members == {"acc-bob"}


@pytest.mark.ac("AC-20")
def test_the_last_member_may_be_removed_and_the_project_is_empty():
    p = Project.create(ADMIN, "Alpha", ["acc-maya"])
    got = p.remove_member("acc-maya")
    assert got.members == frozenset() and got.memberships == ()


@pytest.mark.ac("AC-87")
def test_remove_member_refuses_a_person_who_is_not_a_member():
    from app.projects.domain.errors import MemberNotEligible

    p = Project.create(ADMIN, "Alpha", ["acc-maya"])
    with pytest.raises(MemberNotEligible):
        p.remove_member("acc-bob")
