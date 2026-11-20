"""AC-95 (ADR 0015): PostgreSQL itself refuses the API role every change to a project, and to a membership but its
removal. The tests run as the API role, and as the owner role for the control. PostgreSQL only: SQLite has no roles."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.conftest import make_engine
from tests.migrations_support import drop_everything, owner_engine

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="database roles and grants exist on PostgreSQL only: set TEST_DATABASE_URL and TEST_MIGRATION_DATABASE_URL",
)

PERMISSION_DENIED = "42501"

# The API names neither created_at nor added_at: the database sets them.
INSERT_PROJECT = "INSERT INTO projects (id, name, created_by) VALUES ('p-1', 'Alpha', 'admin-1')"
INSERT_MEMBERSHIP = "INSERT INTO memberships (project_id, account_id, added_by) VALUES ('p-1', 'member-1', 'admin-1')"


@pytest.fixture
def roles():
    """(api, owner) engines on a migrated database: two projects (one with no member) and one membership."""
    api = make_engine()
    owner = owner_engine()
    with api.begin() as connection:
        connection.execute(text(INSERT_PROJECT))
        connection.execute(text(INSERT_MEMBERSHIP))
        # A project with no member: the owner's control DELETE of it meets no foreign key.
        connection.execute(text("INSERT INTO projects (id, name, created_by) VALUES ('p-9', 'Empty', 'admin-1')"))
    yield api, owner
    drop_everything(owner)
    api.dispose()
    owner.dispose()


def rows(engine):
    with engine.connect() as connection:
        return (
            connection.execute(text("SELECT id, name, created_by, created_at FROM projects ORDER BY id")).all(),
            connection.execute(
                text("SELECT project_id, account_id, added_by, added_at FROM memberships ORDER BY account_id")
            ).all(),
        )


REFUSED = {
    "update a project": "UPDATE projects SET name = 'renamed'",
    "delete a project": "DELETE FROM projects WHERE id = 'p-9'",
    "truncate projects": "TRUNCATE projects CASCADE",
    "alter projects": "ALTER TABLE projects ADD COLUMN extra text",
    "drop projects": "DROP TABLE projects CASCADE",
    "update a membership": "UPDATE memberships SET added_by = 'someone'",
    "truncate memberships": "TRUNCATE memberships",
    "alter memberships": "ALTER TABLE memberships ADD COLUMN extra text",
    "drop memberships": "DROP TABLE memberships",
    "name created_at": (
        "INSERT INTO projects (id, name, created_by, created_at) VALUES ('p-2', 'Beta', 'admin-1', '2020-01-01')"
    ),
    "name added_at": (
        "INSERT INTO memberships (project_id, account_id, added_by, added_at) "
        "VALUES ('p-1', 'member-2', 'admin-1', '2020-01-01')"
    ),
}


@pytest.mark.ac("AC-95")
@pytest.mark.parametrize("statement", REFUSED.values(), ids=REFUSED.keys())
def test_the_api_role_cannot_change_a_project_or_a_membership_and_the_owner_can(roles, statement):
    api, owner = roles
    before = rows(owner)
    assert len(before[0]) == 2 and len(before[1]) == 1

    # Each command in its own transaction, so one refusal does not hide another.
    with pytest.raises(DBAPIError) as refused:
        with api.begin() as connection:
            connection.execute(text(statement))
    assert refused.value.orig.sqlstate == PERMISSION_DENIED
    assert rows(owner) == before

    # The control: the owner runs the very same statement and it is accepted (then rolled back),
    # so a typo in the statement cannot make the refusal above pass.
    with owner.connect() as connection:
        transaction = connection.begin()
        connection.execute(text(statement))
        transaction.rollback()
    assert rows(owner) == before


@pytest.mark.ac("AC-95")
def test_the_api_role_can_add_and_read_projects_and_memberships(roles):
    api, _ = roles
    with api.begin() as connection:
        connection.execute(text("INSERT INTO projects (id, name, created_by) VALUES ('p-2', 'Beta', 'admin-1')"))
        connection.execute(
            text("INSERT INTO memberships (project_id, account_id, added_by) VALUES ('p-2', 'member-1', 'admin-1')")
        )
    projects, memberships = rows(api)
    assert [p.id for p in projects] == ["p-1", "p-2", "p-9"]
    assert [(m.project_id, m.account_id) for m in memberships] == [("p-1", "member-1"), ("p-2", "member-1")]
    assert all(p.created_at is not None for p in projects) and all(m.added_at is not None for m in memberships)


@pytest.mark.ac("AC-95")
def test_the_api_role_can_remove_a_membership(roles):
    api, owner = roles
    with api.connect() as connection:
        transaction = connection.begin()
        removed = connection.execute(text("DELETE FROM memberships WHERE account_id = 'member-1'")).rowcount
        transaction.rollback()
    assert removed == 1
    assert len(rows(owner)[1]) == 1  # rolled back


@pytest.mark.ac("AC-95")
def test_a_person_is_in_a_project_once(roles):
    api, _ = roles
    with pytest.raises(DBAPIError) as refused:
        with api.begin() as connection:
            connection.execute(text(INSERT_MEMBERSHIP))
    assert refused.value.orig.sqlstate == "23505"  # unique violation


@pytest.mark.ac("AC-95")
def test_a_membership_needs_a_project_that_exists(roles):
    api, _ = roles
    with pytest.raises(DBAPIError) as refused:
        with api.begin() as connection:
            connection.execute(
                text("INSERT INTO memberships (project_id, account_id, added_by) VALUES ('nope', 'm', 'a')")
            )
    assert refused.value.orig.sqlstate == "23503"  # foreign key violation


@pytest.mark.ac("AC-95")
@pytest.mark.parametrize(
    ("table", "insertable"),
    [("projects", {"id", "name", "created_by"}), ("memberships", {"project_id", "account_id", "added_by"})],
)
def test_the_api_role_may_insert_only_the_columns_the_application_sets(roles, table, insertable):
    api, owner = roles
    with owner.connect() as connection:
        columns = (
            connection.execute(
                text(
                    "SELECT attname FROM pg_attribute WHERE attrelid = CAST(:t AS regclass) "
                    "AND attnum > 0 AND NOT attisdropped"
                ),
                {"t": f"public.{table}"},
            )
            .scalars()
            .all()
        )
        user = api.url.username
        held = {
            c
            for c in columns
            if connection.execute(
                text("SELECT has_column_privilege(:u, :t, :c, 'INSERT')"), {"u": user, "t": f"public.{table}", "c": c}
            ).scalar_one()
        }
        any_update = connection.execute(
            text("SELECT has_any_column_privilege(:u, :t, 'UPDATE')"), {"u": user, "t": f"public.{table}"}
        ).scalar_one()
    assert held == insertable
    assert not any_update
