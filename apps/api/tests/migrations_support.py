"""Helpers that run Alembic from the tests, as the owner role (ADR 0012)."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

import app.access.adapters.outbound.sql  # noqa: F401 - registers the tables on Base
from app.infrastructure.db import Base
from tests.safety import check_test_database

API = Path(__file__).resolve().parents[1]


def owner_url() -> str | None:
    """TEST_MIGRATION_DATABASE_URL, else TEST_DATABASE_URL (the same superuser until the roles of TSK-L1.3)."""
    return os.environ.get("TEST_MIGRATION_DATABASE_URL") or os.environ.get("TEST_DATABASE_URL")


def owner_engine() -> Engine:
    return create_engine(check_test_database(owner_url()))  # refuses a database that is not named *_test


def upgrade(engine: Engine, revision: str = "head") -> None:
    cfg = Config(str(API / "alembic.ini"))
    cfg.set_main_option("script_location", str(API / "migrations"))
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, revision)


def drop_everything(engine: Engine) -> None:
    """Drops every table and Alembic's own, as the owner."""
    Base.metadata.drop_all(engine)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
