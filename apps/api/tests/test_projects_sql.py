"""SqlProjects keeps the promises of the ProjectRepository port. SQLite by default, PostgreSQL with TEST_DATABASE_URL
(then as the API role, which names neither created_at nor added_at: the database sets them)."""

import os
import uuid

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from app.projects.adapters.outbound.sql import MembershipRow, ProjectRow, SqlProjects
from app.projects.domain.caller import Caller
from app.projects.domain.project import Membership, Project
from tests.conftest import make_engine
from tests.migrations_support import drop_everything, owner_engine

ADMIN = Caller("acc-ada", is_administrator=True)


@pytest.fixture
def engine():
    engine = make_engine()
    yield engine
    engine.dispose()
    if os.environ.get("TEST_DATABASE_URL"):
        owner = owner_engine()
        drop_everything(owner)
        owner.dispose()


def counts(engine) -> tuple[int, int]:
    with Session(engine) as s:
        return s.scalar(select(func.count()).select_from(ProjectRow)), s.scalar(
            select(func.count()).select_from(MembershipRow)
        )


@pytest.mark.ac("AC-9")
def test_a_project_and_its_memberships_come_back_from_a_new_session(engine):
    project = Project.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    with Session(engine) as s:
        SqlProjects(s).add(project)
        s.commit()
    with Session(engine) as s:
        got = SqlProjects(s).by_id(project.id)
    assert got is not None and got.id == project.id
    assert (got.name, got.created_by, got.members) == ("Alpha", "acc-ada", {"acc-maya", "acc-bob"})
    assert {m.added_by for m in got.memberships} == {"acc-ada"}


@pytest.mark.ac("AC-10")
def test_a_project_with_no_member_comes_back_with_none(engine):
    project = Project.create(ADMIN, "Alpha", [])
    with Session(engine) as s:
        SqlProjects(s).add(project)
        s.commit()
    with Session(engine) as s:
        assert SqlProjects(s).by_id(project.id).members == frozenset()


def test_the_project_and_its_memberships_commit_together(engine):
    project = Project.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    with Session(engine) as s:
        SqlProjects(s).add(project)
        s.flush()
        s.commit()
    assert counts(engine) == (1, 2)


def test_a_rollback_leaves_neither_the_project_nor_its_memberships(engine):
    with Session(engine) as s:
        SqlProjects(s).add(Project.create(ADMIN, "Alpha", ["acc-maya"]))
        s.rollback()
    assert counts(engine) == (0, 0)


def test_the_stored_id_is_a_random_uuid_string(engine):
    with Session(engine) as s:
        SqlProjects(s).add(Project.create(ADMIN, "Alpha", []))
        s.commit()
        (stored,) = s.scalars(select(ProjectRow.id)).all()
    assert str(uuid.UUID(stored)) == stored and uuid.UUID(stored).version == 4


def test_an_id_that_does_not_exist_gives_none(engine):
    with Session(engine) as s:
        assert SqlProjects(s).by_id(str(uuid.uuid4())) is None


def test_the_database_sets_the_times(engine):
    with Session(engine) as s:
        SqlProjects(s).add(Project.create(ADMIN, "Alpha", ["acc-maya"]))
        s.commit()
        assert s.scalar(select(ProjectRow.created_at)) is not None
        assert s.scalar(select(MembershipRow.added_at)) is not None


# UC-P3: the reads (TSK-P3.1, TSK-P3.2)


def seeded(engine):
    alpha = Project.create(ADMIN, "Alpha", ["acc-maya", "acc-bob"])
    beta = Project.create(ADMIN, "Beta", ["acc-maya"])
    gamma = Project.create(ADMIN, "Gamma", [])
    with Session(engine) as s:
        repo = SqlProjects(s)
        for p in (alpha, beta, gamma):
            repo.add(p)
            s.flush()
        s.commit()
    return alpha, beta, gamma


@pytest.mark.ac("AC-55")
def test_list_for_member_returns_only_that_persons_projects_with_all_their_members(engine):
    alpha, beta, _ = seeded(engine)
    with Session(engine) as s:
        got = SqlProjects(s).list_for_member("acc-bob")
    assert [p.id for p in got] == [alpha.id]
    assert got[0].members == {"acc-maya", "acc-bob"}  # the whole member list, not only the asker
    with Session(engine) as s:
        assert {p.id for p in SqlProjects(s).list_for_member("acc-maya")} == {alpha.id, beta.id}


@pytest.mark.ac("AC-86")
def test_list_for_member_of_a_person_in_no_project_is_empty(engine):
    seeded(engine)
    with Session(engine) as s:
        assert SqlProjects(s).list_for_member("acc-nobody") == []


@pytest.mark.ac("AC-55")
def test_list_all_returns_every_project_with_its_members_including_one_with_none(engine):
    alpha, beta, gamma = seeded(engine)
    with Session(engine) as s:
        got = {p.id: p for p in SqlProjects(s).list_all()}
    assert set(got) == {alpha.id, beta.id, gamma.id}
    assert got[alpha.id].members == {"acc-maya", "acc-bob"} and got[gamma.id].members == frozenset()
    assert got[alpha.id].created_by == "acc-ada" and got[beta.id].name == "Beta"


@pytest.mark.ac("AC-55")
@pytest.mark.parametrize("read", ["list_all", "list_for_member"])
def test_the_lists_use_two_queries_however_many_projects_there_are(engine, read):
    seeded(engine)
    statements: list[str] = []

    def record(conn, cursor, statement, *rest):
        statements.append(statement)

    with Session(engine) as s:
        repo = SqlProjects(s)
        event.listen(engine, "before_cursor_execute", record)
        try:
            repo.list_all() if read == "list_all" else repo.list_for_member("acc-maya")
        finally:
            event.remove(engine, "before_cursor_execute", record)
    selects = [q for q in statements if q.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 2, selects


def test_the_lists_are_in_a_stable_order(engine):
    seeded(engine)
    with Session(engine) as s:
        first = [p.id for p in SqlProjects(s).list_all()]
        second = [p.id for p in SqlProjects(s).list_all()]
    assert first == second


# UC-P2: add_member and remove_member write only the row difference (TSK-P2.1, TSK-P2.2, TSK-P2.6)


def one_project(engine, members=("acc-maya",)):
    project = Project.create(ADMIN, "Alpha", list(members))
    with Session(engine) as s:
        SqlProjects(s).add(project)
        s.commit()
    return project


@pytest.mark.ac("AC-17")
def test_add_member_inserts_one_membership_with_who_added_it(engine):
    project = one_project(engine)
    with Session(engine) as s:
        assert SqlProjects(s).add_member(project.id, Membership("acc-bob", added_by="acc-ada")) is True
        s.commit()
    with Session(engine) as s:
        got = SqlProjects(s).by_id(project.id)
    assert got.members == {"acc-maya", "acc-bob"}
    assert Membership("acc-bob", added_by="acc-ada") in got.memberships


@pytest.mark.ac("AC-88")
@pytest.mark.ac("AC-90")
def test_add_member_of_a_row_that_exists_says_false_and_leaves_the_session_usable(engine):
    project = one_project(engine)
    with Session(engine) as s:
        repo = SqlProjects(s)
        assert repo.add_member(project.id, Membership("acc-maya", added_by="acc-other")) is False
        assert repo.by_id(project.id).members == {"acc-maya"}  # the same transaction still works
        s.commit()
    assert counts(engine) == (1, 1)
    with Session(engine) as s:
        assert [m.added_by for m in SqlProjects(s).by_id(project.id).memberships] == ["acc-ada"]  # not overwritten


@pytest.mark.ac("AC-20")
def test_remove_member_deletes_one_row_and_says_true_then_false(engine):
    project = one_project(engine, ["acc-maya", "acc-bob"])
    with Session(engine) as s:
        repo = SqlProjects(s)
        assert repo.remove_member(project.id, "acc-maya") is True
        assert repo.remove_member(project.id, "acc-maya") is False
        assert repo.by_id(project.id).members == {"acc-bob"}
        s.commit()
    assert counts(engine) == (1, 1)


@pytest.mark.ac("AC-20")
def test_the_last_member_can_be_removed_and_the_project_stays(engine):
    project = one_project(engine)
    with Session(engine) as s:
        SqlProjects(s).remove_member(project.id, "acc-maya")
        s.commit()
    with Session(engine) as s:
        assert SqlProjects(s).by_id(project.id).members == frozenset()


def test_a_membership_change_never_issues_an_update(engine):
    """The API role has no UPDATE on memberships (ADR 0015): only INSERT and DELETE are ever sent."""
    project = one_project(engine)
    statements: list[str] = []

    def record(conn, cursor, statement, *rest):
        statements.append(statement.lstrip().split()[0].upper())

    with Session(engine) as s:
        repo = SqlProjects(s)
        event.listen(engine, "before_cursor_execute", record)
        try:
            repo.add_member(project.id, Membership("acc-bob", added_by="acc-ada"))
            repo.add_member(project.id, Membership("acc-bob", added_by="acc-ada"))
            repo.remove_member(project.id, "acc-bob")
        finally:
            event.remove(engine, "before_cursor_execute", record)
    assert "UPDATE" not in statements and {"INSERT", "DELETE"} <= set(statements)
