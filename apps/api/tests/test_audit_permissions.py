"""AC-80, RULE-L1 (ADR 0011, 0012): PostgreSQL itself refuses the API role every change to the audit trail.
The tests run as the API role, and as the owner role for the control. PostgreSQL only: SQLite has no roles."""

import os
from datetime import UTC, datetime, timedelta

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

SEQUENCE = "pg_get_serial_sequence('public.audit_entries', 'id')"

# The API names neither the id nor the time: the database sets both (RULE-L2, ADR 0011 amendments).
INSERT = (
    "INSERT INTO audit_entries (kind, actor_id, action, target_id, reason) "
    "VALUES ('account', 'actor-1', 'deactivated', 'target-1', 'first')"
)


@pytest.fixture
def roles():
    """(api, owner) engines on a database that Alembic has migrated, holding one audit row."""
    api = make_engine()  # migrated as the owner; connects as the API role
    owner = owner_engine()
    with api.begin() as connection:
        connection.execute(text(INSERT))
    yield api, owner
    drop_everything(owner)
    api.dispose()
    owner.dispose()


def rows(engine):
    with engine.connect() as connection:
        return connection.execute(text("SELECT id, at, actor_id, action, target_id, reason FROM audit_entries ORDER BY id")).all()


STATEMENTS = {
    "update": "UPDATE audit_entries SET reason = 'rewritten'",
    "delete": "DELETE FROM audit_entries",
    "truncate": "TRUNCATE audit_entries",
    "alter table": "ALTER TABLE audit_entries ADD COLUMN extra text",
    "drop table": "DROP TABLE audit_entries",
    "setval on the sequence": f"SELECT setval({SEQUENCE}, 1000)",
}


@pytest.mark.ac("AC-80")
@pytest.mark.rule("RULE-L1")
@pytest.mark.parametrize("statement", STATEMENTS.values(), ids=STATEMENTS.keys())
def test_the_api_role_cannot_change_the_audit_trail_and_the_owner_can(roles, statement):
    api, owner = roles
    before = rows(owner)
    assert len(before) == 1

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


@pytest.mark.ac("AC-80")
@pytest.mark.rule("RULE-L1")
def test_the_api_role_can_still_add_and_read_entries(roles):
    api, _ = roles
    with api.begin() as connection:
        connection.execute(text(INSERT))
    assert [r.reason for r in rows(api)] == ["first", "first"]


TABLE_PRIVILEGES = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"]
EXPECTED_TABLES = {
    "accounts": {"SELECT", "INSERT", "UPDATE"},
    "audit_entries": {"SELECT"},  # INSERT is on chosen columns only, below
    "alembic_version": set(),
}
# id is an identity column: the sequence exists and the API role holds nothing on it.
EXPECTED_SEQUENCES = {"audit_entries_id_seq": set()}
# INSERT on every column but these two: the database sets them.
DATABASE_SET = {"id", "at"}


@pytest.mark.ac("AC-80")
@pytest.mark.rule("RULE-L1")
def test_the_api_role_holds_exactly_the_privileges_on_the_allow_list(roles):
    api, owner = roles
    with owner.connect() as connection:
        privileges = TABLE_PRIVILEGES + (["MAINTAIN"] if int(connection.execute(text("SHOW server_version_num")).scalar_one()) >= 170000 else [])
        user = api.url.username
        tables = connection.execute(text("SELECT relname FROM pg_class WHERE relkind IN ('r','p') AND relnamespace = 'public'::regnamespace")).scalars().all()
        sequences = connection.execute(text("SELECT relname FROM pg_class WHERE relkind = 'S' AND relnamespace = 'public'::regnamespace")).scalars().all()
        held_tables = {
            t: {p for p in privileges if connection.execute(text("SELECT has_table_privilege(:u, :t, :p)"), {"u": user, "t": f"public.{t}", "p": p}).scalar_one()}
            for t in tables
        }
        held_sequences = {
            s: {p for p in ("USAGE", "SELECT", "UPDATE") if connection.execute(text("SELECT has_sequence_privilege(:u, :s, :p)"), {"u": user, "s": f"public.{s}", "p": p}).scalar_one()}
            for s in sequences
        }
        held_schema = {
            p for p in ("USAGE", "CREATE") if connection.execute(text("SELECT has_schema_privilege(:u, 'public', :p)"), {"u": user, "p": p}).scalar_one()
        }
        any_column_update = connection.execute(text("SELECT has_any_column_privilege(:u, 'public.audit_entries', 'UPDATE')"), {"u": user}).scalar_one()
        columns = connection.execute(text(
            "SELECT attname FROM pg_attribute WHERE attrelid = 'public.audit_entries'::regclass AND attnum > 0 AND NOT attisdropped"
        )).scalars().all()
        insertable = {c for c in columns if connection.execute(text("SELECT has_column_privilege(:u, 'public.audit_entries', :c, 'INSERT')"), {"u": user, "c": c}).scalar_one()}
        selectable = {c for c in columns if connection.execute(text("SELECT has_column_privilege(:u, 'public.audit_entries', :c, 'SELECT')"), {"u": user, "c": c}).scalar_one()}
    assert insertable == set(columns) - DATABASE_SET
    assert selectable == set(columns)
    assert held_tables == EXPECTED_TABLES
    assert held_sequences == EXPECTED_SEQUENCES
    assert held_schema == {"USAGE"}
    assert not any_column_update


@pytest.mark.ac("AC-80")
@pytest.mark.rule("RULE-L2")
@pytest.mark.parametrize("column", ["at", "id"])
def test_an_insert_that_names_the_time_or_the_id_is_refused(roles, column):
    api, owner = roles
    before = rows(owner)
    value = "'2020-01-01 00:00:00'" if column == "at" else "999"
    with pytest.raises(DBAPIError) as refused:
        with api.begin() as connection:
            connection.execute(text(
                f"INSERT INTO audit_entries ({column}, kind, action, target_id) VALUES ({value}, 'account', 'approve', 't')"
            ))
    # A named id is refused twice over: by the column grant (42501) and by GENERATED ALWAYS (428C9). PostgreSQL
    # reports the second first, for a plain insert. The time has only the grant.
    assert refused.value.orig.sqlstate in ({PERMISSION_DENIED, "428C9"} if column == "id" else {PERMISSION_DENIED})
    assert rows(owner) == before
    if column == "id":  # forcing it past GENERATED ALWAYS still meets the grant
        with pytest.raises(DBAPIError) as forced:
            with api.begin() as connection:
                connection.execute(text(
                    "INSERT INTO audit_entries (id, kind, action, target_id) OVERRIDING SYSTEM VALUE "
                    "VALUES (999, 'account', 'approve', 't')"
                ))
        assert forced.value.orig.sqlstate == PERMISSION_DENIED
    # the control: the owner may name them (the owner can still edit rows, which is accepted for the alpha)
    with owner.connect() as connection:
        transaction = connection.begin()
        connection.execute(text(
            f"INSERT INTO audit_entries ({column}, kind, action, target_id) OVERRIDING SYSTEM VALUE "
            f"VALUES ({value}, 'account', 'approve', 't')"
        ))
        transaction.rollback()


@pytest.mark.ac("AC-80")
@pytest.mark.rule("RULE-L2")
def test_an_insert_without_the_time_works_and_the_database_sets_it(roles):
    api, owner = roles
    with api.begin() as connection:
        connection.execute(text(INSERT))
    with owner.connect() as connection:
        stored = connection.execute(text("SELECT at FROM audit_entries ORDER BY id DESC LIMIT 1")).scalar_one()
        database_now = connection.execute(text("SELECT now() AT TIME ZONE 'utc'")).scalar_one()
    assert stored <= database_now and database_now - stored < timedelta(seconds=30)
    assert abs(stored - datetime.now(UTC).replace(tzinfo=None)) < timedelta(seconds=30)  # UTC, as the app reads it
