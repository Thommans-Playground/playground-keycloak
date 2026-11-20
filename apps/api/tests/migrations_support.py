"""Helpers that run Alembic from the tests, as the owner role (ADR 0012)."""

import os
from pathlib import Path
from unittest import mock

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url

import app.access.adapters.outbound.sql  # noqa: F401 - registers the tables on Base
import app.audit.adapters.outbound.sql  # noqa: F401 - registers the audit table on Base
from app.infrastructure.db import Base
from tests.safety import check_test_database

API = Path(__file__).resolve().parents[1]


def owner_url() -> str | None:
    """The owner role's URL: TEST_MIGRATION_DATABASE_URL, else TEST_DATABASE_URL (a single-role setup, which the
    self check of the API refuses, so only the tests that do not start the app can use it)."""
    return os.environ.get("TEST_MIGRATION_DATABASE_URL") or os.environ.get("TEST_DATABASE_URL")


def on_postgres() -> bool:
    return bool(os.environ.get("TEST_DATABASE_URL"))


def as_owner(engine: Engine) -> Engine:
    """The engine that may change structure: the owner's on PostgreSQL, the given one on SQLite."""
    return owner_engine() if on_postgres() else engine


def owner_engine() -> Engine:
    return create_engine(check_test_database(owner_url()))  # refuses a database that is not named *_test


def upgrade(engine: Engine, revision: str = "head") -> None:
    cfg = Config(str(API / "alembic.ini"))
    cfg.set_main_option("script_location", str(API / "migrations"))
    with mock.patch.dict(os.environ, api_role_environment()), engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, revision)


def api_role_environment() -> dict[str, str]:
    """What the migration container gets in compose: the API role's name and password (migration 0002 creates the role).
    In the tests both come from TEST_DATABASE_URL, which connects as the API role."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        return {}
    api = make_url(url)
    return {"API_DB_USER": api.username or "", "API_DB_PASSWORD": api.password or ""}


def drop_everything(engine: Engine) -> None:
    """Drops every table and Alembic's own, as the owner."""
    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))


def stamp(engine: Engine, revision: str) -> None:
    """Tells Alembic the database is at `revision` without running anything, so the next upgrade runs the later ones again."""
    cfg = Config(str(API / "alembic.ini"))
    cfg.set_main_option("script_location", str(API / "migrations"))
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.stamp(cfg, revision)
