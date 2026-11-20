"""Alembic's environment (ADR 0012). It runs as the owner role, outside the app: the database URL comes from
MIGRATION_DATABASE_URL, which the API never reads. A caller (the tests) may hand in an open connection instead."""

import os

from alembic import context
from sqlalchemy import create_engine

import app.access.adapters.outbound.sql  # noqa: F401 - registers the tables on Base
import app.audit.adapters.outbound.sql  # noqa: F401 - registers the audit table on Base
from app.infrastructure.db import Base

target_metadata = Base.metadata


def run() -> None:
    connection = context.config.attributes.get("connection")
    if connection is None:
        url = os.environ.get("MIGRATION_DATABASE_URL")
        if not url:
            raise RuntimeError("MIGRATION_DATABASE_URL is not set: migrations run as the owner role (ADR 0012).")
        with create_engine(url).connect() as connection:
            _migrate(connection)
        return
    _migrate(connection)


def _migrate(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


run()
