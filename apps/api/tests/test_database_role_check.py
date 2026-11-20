"""The start-up self check (ADR 0011 amendments, UC-L1 D12, D13): the API refuses to run with a role that could
change the audit trail or structure, or with the owner's URL in its environment. PostgreSQL only, but the
environment rule holds on every engine."""

import os

import pytest
from sqlalchemy import text

from app.access.adapters.outbound.token_verifier import JwtTokenVerifier
from app.infrastructure.config import Settings
from app.infrastructure.role_check import UnsafeStartup, check_database_role, check_environment
from app.main import create_app
from tests.conftest import AUDIENCE, ISSUER, KEY, make_engine
from tests.fakes import FakeIdp
from tests.migrations_support import drop_everything, owner_engine

postgres = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"), reason="roles and grants exist on PostgreSQL only"
)


def build(engine):
    verifier = JwtTokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key())
    return create_app(Settings(keycloak_url="http://kc.test"), verifier, FakeIdp(), engine)


@pytest.fixture
def api():
    engine = make_engine()
    yield engine
    owner = owner_engine()
    drop_everything(owner)
    owner.dispose()
    engine.dispose()


@pytest.fixture
def owner(api):
    engine = owner_engine()
    yield engine
    engine.dispose()


@postgres
def test_the_api_role_passes_the_check(api):
    with api.connect() as connection:
        check_database_role(connection)
    build(api)  # and the app starts


@postgres
def test_the_owner_role_is_refused(owner):
    with owner.connect() as connection, pytest.raises(UnsafeStartup, match="superuser"):
        check_database_role(connection)


@postgres
def test_create_app_refuses_to_start_as_the_owner(owner):
    with pytest.raises(UnsafeStartup):
        build(owner)


def test_create_app_refuses_to_start_when_the_migration_url_is_set(monkeypatch):
    monkeypatch.setenv("MIGRATION_DATABASE_URL", "postgresql+psycopg://owner:secret@db/playground")
    with pytest.raises(UnsafeStartup, match="MIGRATION_DATABASE_URL"):
        build(make_engine())


def test_the_environment_check_passes_without_the_migration_url(monkeypatch):
    monkeypatch.delenv("MIGRATION_DATABASE_URL", raising=False)
    check_environment()


def risky(connection, how: str) -> None:
    """Turns the connection into a plain role that has one unsafe thing (inside a transaction that is rolled back)."""
    run = lambda sql: connection.execute(text(sql))  # noqa: E731
    run("CREATE ROLE checked NOLOGIN")
    run("CREATE ROLE a_group NOLOGIN")
    match how:
        case "superuser":
            run("ALTER ROLE checked SUPERUSER")
        case "owns a table":
            run("ALTER TABLE accounts OWNER TO checked")
        case "member of a role that owns a table":
            run("ALTER TABLE accounts OWNER TO a_group")
            run("GRANT a_group TO checked")
        case "update on the audit table":
            run("GRANT UPDATE ON audit_entries TO checked")
        case "update on one column of the audit table":
            run("GRANT UPDATE (reason) ON audit_entries TO checked")
        case "delete on the audit table":
            run("GRANT DELETE ON audit_entries TO checked")
        case "truncate on the audit table":
            run("GRANT TRUNCATE ON audit_entries TO checked")
        case "trigger on the audit table":
            run("GRANT TRIGGER ON audit_entries TO checked")
        case "references on the audit table":
            run("GRANT REFERENCES ON audit_entries TO checked")
        case "write on the audit sequence":
            run("GRANT UPDATE ON SEQUENCE audit_entries_id_seq TO checked")
        case "create on the schema":
            run("GRANT CREATE ON SCHEMA public TO checked")
    run("SET ROLE checked")


UNSAFE = [
    "superuser",
    "owns a table",
    "member of a role that owns a table",
    "update on the audit table",
    "update on one column of the audit table",
    "delete on the audit table",
    "truncate on the audit table",
    "trigger on the audit table",
    "references on the audit table",
    "write on the audit sequence",
    "create on the schema",
]


@postgres
@pytest.mark.parametrize("how", UNSAFE)
def test_each_unsafe_role_is_refused(owner, how):
    with owner.connect() as connection:
        transaction = connection.begin()
        risky(connection, how)
        with pytest.raises(UnsafeStartup):
            check_database_role(connection)
        transaction.rollback()


@postgres
def test_a_plain_role_with_the_allow_list_passes(owner):
    with owner.connect() as connection:
        transaction = connection.begin()
        risky(connection, "none")  # no unsafe thing: a role with nothing at all
        check_database_role(connection)
        transaction.rollback()
