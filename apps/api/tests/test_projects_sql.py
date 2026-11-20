"""SqlProjects keeps the promises of the ProjectRepository port. SQLite by default, PostgreSQL with TEST_DATABASE_URL
(then as the API role, which names neither created_at nor added_at: the database sets them)."""

import os
import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.projects.adapters.outbound.sql import MembershipRow, ProjectRow, SqlProjects
from app.projects.domain.caller import Caller
from app.projects.domain.project import Project
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
