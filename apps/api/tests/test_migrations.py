"""Migrations (ADR 0004, 0012): Alembic builds the schema as the owner, and the app builds nothing."""

import os

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text

import app.access.adapters.outbound.sql  # noqa: F401 - registers the tables on Base
import app.audit.adapters.outbound.sql  # noqa: F401 - registers the audit table on Base
import app.projects.adapters.outbound.sql  # noqa: F401 - registers the project tables on Base
from app.access.adapters.outbound.token_verifier import JwtTokenVerifier
from app.infrastructure.config import Settings
from app.infrastructure.db import Base
from app.main import create_app
from tests.conftest import AUDIENCE, ISSUER, KEY, make_empty_engine
from tests.fakes import FakeIdp
from tests.migrations_support import API, as_owner, drop_everything, owner_engine, stamp, upgrade


@pytest.fixture
def engine():
    e = make_empty_engine()
    yield e
    if os.environ.get("TEST_DATABASE_URL"):
        owner = owner_engine()
        drop_everything(owner)
        owner.dispose()
    e.dispose()


def columns(engine, table):
    return {c["name"] for c in inspect(engine).get_columns(table)}


def test_migrations_create_todays_schema(engine):
    upgrade(as_owner(engine))
    assert set(inspect(engine).get_table_names()) - {"alembic_version"} == {
        "accounts",
        "audit_entries",
        "projects",
        "memberships",
    }
    assert columns(engine, "accounts") == {"id", "identity", "name", "email", "role", "status", "created", "created_by"}
    assert columns(engine, "audit_entries") == {
        "id",
        "at",
        "kind",
        "actor_id",
        "actor_name",
        "actor_email",
        "action",
        "target_id",
        "target_name",
        "target_email",
        "details",
        "reason",
    }


def test_the_project_tables_have_the_columns_of_the_ontology(engine):
    upgrade(as_owner(engine))
    assert columns(engine, "projects") == {"id", "name", "created_by", "created_at"}
    assert columns(engine, "memberships") == {"project_id", "account_id", "added_by", "added_at"}


def test_migrations_match_the_models(engine):
    upgrade(as_owner(engine))
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == [], f"the models and the migrations differ, write a migration: {diff}"


def test_create_app_creates_no_tables(engine):
    settings = Settings(keycloak_url="http://kc.test")
    verifier = JwtTokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key())
    create_app(settings, verifier, FakeIdp(), engine)
    assert inspect(engine).get_table_names() == []


def test_upgrade_is_safe_on_an_existing_schema(engine):
    Base.metadata.create_all(as_owner(engine))  # an old dev database: the tables exist, Alembic has never run
    upgrade(as_owner(engine))
    assert set(inspect(engine).get_table_names()) == {
        "accounts",
        "audit_entries",
        "projects",
        "memberships",
        "alembic_version",
    }
    with as_owner(engine).connect() as connection:  # alembic_version is the owner's: the API role has no grant on it
        at = MigrationContext.configure(connection).get_current_revision()
    cfg = Config(str(API / "alembic.ini"))
    cfg.set_main_option("script_location", str(API / "migrations"))
    assert at is not None and {at} == set(ScriptDirectory.from_config(cfg).get_heads())


def test_the_roles_migration_can_run_twice(engine):
    # Alembic skips a revision it already applied, so stamp the database back and run 0002 again: the second run
    # finds the role and the grants in place and must neither fail nor change the result.
    owner = as_owner(engine)
    upgrade(owner)
    stamp(owner, "0001")
    upgrade(owner)
    with as_owner(engine).connect() as connection:  # alembic_version is the owner's: the API role has no grant on it
        at = MigrationContext.configure(connection).get_current_revision()
    assert at == "0004"


OLD_ROW = (
    "INSERT INTO audit_entries (at, actor_id, action, target_id, reason) "
    "VALUES ('2026-01-01 10:00:00', 'actor-1', 'approve', 'target-1', 'old reason')"
)


@pytest.mark.ac("AC-56")
def test_an_old_row_becomes_an_account_entry_with_no_names(engine):
    owner = as_owner(engine)
    upgrade(owner, "0002")
    with owner.begin() as connection:
        connection.execute(text(OLD_ROW))
    upgrade(owner)
    with owner.connect() as connection:
        row = connection.execute(
            text(
                "SELECT kind, actor_id, actor_name, actor_email, target_id, target_name, target_email, details, reason "
                "FROM audit_entries"
            )
        ).one()
    assert row.kind == "account"
    assert (row.actor_id, row.target_id, row.reason) == ("actor-1", "target-1", "old reason")
    assert (row.actor_name, row.actor_email, row.target_name, row.target_email) == (None, None, None, None)
    assert not row.details  # no people involved: null or an empty list


@pytest.mark.rule("RULE-L2")
def test_the_database_sets_the_time_when_an_insert_names_none(engine):
    owner = as_owner(engine)
    upgrade(owner)
    with owner.begin() as connection:
        connection.execute(
            text("INSERT INTO audit_entries (kind, action, target_id) VALUES ('account', 'approve', 'target-1')")
        )
        at = connection.execute(text("SELECT at FROM audit_entries")).scalar_one()
    assert at is not None


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="identity columns: PostgreSQL only")
def test_the_id_is_an_identity_column_always_generated(engine):
    upgrade(as_owner(engine))
    with as_owner(engine).connect() as connection:
        row = connection.execute(
            text(
                "SELECT is_identity, identity_generation, column_default FROM information_schema.columns "
                "WHERE table_name = 'audit_entries' AND column_name = 'id'"
            )
        ).one()
    assert (row.is_identity, row.identity_generation, row.column_default) == ("YES", "ALWAYS", None)


@pytest.mark.skipif(not os.environ.get("TEST_DATABASE_URL"), reason="identity columns: PostgreSQL only")
def test_the_migration_keeps_the_numbering_of_old_rows_going(engine):
    owner = as_owner(engine)
    upgrade(owner, "0002")
    with owner.begin() as connection:
        connection.execute(text(OLD_ROW))
        connection.execute(text(OLD_ROW))
    upgrade(owner)
    with owner.begin() as connection:
        connection.execute(
            text("INSERT INTO audit_entries (kind, action, target_id) VALUES ('account', 'approve', 't')")
        )
        ids = connection.execute(text("SELECT id FROM audit_entries ORDER BY id")).scalars().all()
    assert ids == [1, 2, 3]


def test_the_project_migration_can_run_twice(engine):
    owner = as_owner(engine)
    upgrade(owner)
    stamp(owner, "0003")
    upgrade(owner)  # the tables and the grants exist: neither a failure nor a change
    with owner.connect() as connection:
        at = MigrationContext.configure(connection).get_current_revision()
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert at == "0004" and diff == []


def test_the_database_sets_when_a_project_and_a_membership_were_added(engine):
    owner = as_owner(engine)
    upgrade(owner)
    with owner.begin() as connection:
        connection.execute(text("INSERT INTO projects (id, name, created_by) VALUES ('p-1', 'Alpha', 'a-1')"))
        connection.execute(
            text("INSERT INTO memberships (project_id, account_id, added_by) VALUES ('p-1', 'a-2', 'a-1')")
        )
        created = connection.execute(text("SELECT created_at FROM projects")).scalar_one()
        added = connection.execute(text("SELECT added_at FROM memberships")).scalar_one()
    assert created is not None and added is not None
