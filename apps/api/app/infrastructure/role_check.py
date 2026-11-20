"""The start-up self check (ADR 0011 amendments, UC-L1 D12 and D13).

The API refuses to run with a database role that could change the audit trail or the structure, and with the owner's
URL in its environment. The same check is repeated at every start, so a wrong deploy (the owner's secret handed to the
API by mistake) stops at once instead of silently weakening AC-80."""

import os

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

AUDIT_TABLE = "public.audit_entries"


class UnsafeStartup(RuntimeError):
    """The API must not start: its role or its environment is not the one ADR 0011 asks for."""


def check_environment() -> None:
    if os.environ.get("MIGRATION_DATABASE_URL"):
        raise UnsafeStartup(
            "MIGRATION_DATABASE_URL is set in the API's environment: it is the owner role's URL and belongs to the "
            "migration step only (ADR 0011, 0012). Remove it from the API."
        )


def _one(connection: Connection, sql: str):
    return connection.execute(text(sql)).scalar_one_or_none()


def check_database_role(connection: Connection) -> None:
    """Raises UnsafeStartup if the connected role is more than the allow list. PostgreSQL only."""
    problems: list[str] = []
    if _one(connection, "SELECT rolsuper FROM pg_roles WHERE rolname = current_user"):
        problems.append("is a superuser")
    owned = connection.execute(
        text(
            "SELECT schemaname || '.' || tablename FROM pg_tables "
            "WHERE schemaname NOT IN ('pg_catalog', 'information_schema') "
            "AND pg_has_role(current_user, tableowner, 'MEMBER')"
        )
    ).scalars().all()
    if owned:
        problems.append(f"owns, or belongs to a role that owns, the tables {sorted(owned)}")
    if _one(connection, f"SELECT to_regclass('{AUDIT_TABLE}') IS NOT NULL"):
        for privilege in ("DELETE", "TRUNCATE", "TRIGGER"):
            if _one(connection, f"SELECT has_table_privilege(current_user, '{AUDIT_TABLE}', '{privilege}')"):
                problems.append(f"has {privilege} on audit_entries")
        for privilege in ("UPDATE", "REFERENCES"):  # on any column too, not only on the table
            if _one(connection, f"SELECT has_any_column_privilege(current_user, '{AUDIT_TABLE}', '{privilege}')"):
                problems.append(f"has {privilege} on audit_entries")
        sequences = connection.execute(
            text(
                "SELECT pg_get_serial_sequence('public.audit_entries', attname) FROM pg_attribute "
                "WHERE attrelid = 'public.audit_entries'::regclass AND attnum > 0 AND NOT attisdropped"
            )
        ).scalars().all()
        for sequence in filter(None, sequences):
            if connection.execute(
                text("SELECT has_sequence_privilege(current_user, :s, 'UPDATE')"), {"s": sequence}
            ).scalar_one():
                problems.append(f"can write the sequence {sequence} of audit_entries")
    if _one(connection, "SELECT has_schema_privilege(current_user, 'public', 'CREATE')"):
        problems.append("can create in schema public")
    if problems:
        who = _one(connection, "SELECT current_user")
        raise UnsafeStartup(
            f"The database role '{who}' is not safe for the API: it " + "; it ".join(problems) + ". "
            "Connect as the API role that migration 0002 creates (ADR 0011)."
        )


def check_start(engine: Engine) -> None:
    """What the composition root runs before it serves: the environment always, the role on PostgreSQL only."""
    check_environment()
    if engine.dialect.name == "postgresql":
        with engine.connect() as connection:
            check_database_role(connection)
