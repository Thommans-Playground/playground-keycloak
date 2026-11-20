"""The API's database role and its grants (ADR 0011 amendments, ADR 0012, UC-L1 D12).

Runs as the OWNER role. Creates the role the API connects with (name from API_DB_USER, default playground_api;
password from API_DB_PASSWORD, which only the migration container gets), then grants it an allow list, table by
table, with no default privileges. SQLite has no roles, so there the migration does nothing.

Revision ID: 0002
Revises: 0001
"""

import os
import re

import sqlalchemy as sa
from alembic import op

from app.infrastructure.config import Settings

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

CREATE_ROLE = """
DO $$
DECLARE
    role_name text := current_setting('migration.api_role');
    role_password text := nullif(current_setting('migration.api_password', true), '');
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = role_name) THEN
        IF role_password IS NULL THEN
            RAISE EXCEPTION 'API_DB_PASSWORD is not set: the migration needs it to create the role %', role_name;
        END IF;
        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION', role_name, role_password);
    ELSIF role_password IS NOT NULL THEN
        EXECUTE format('ALTER ROLE %I PASSWORD %L', role_name, role_password);
    END IF;
END
$$
"""


def _role_name() -> str:
    name = Settings().api_db_user
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", name):
        raise RuntimeError(f"API_DB_USER '{name}' is not a plain lower case role name")
    return name


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    role = _role_name()
    bind.execute(sa.text("SELECT set_config('migration.api_role', :role, true)"), {"role": role})
    bind.execute(
        sa.text("SELECT set_config('migration.api_password', :password, true)"),
        {"password": os.environ.get("API_DB_PASSWORD", "")},
    )
    bind.execute(sa.text(CREATE_ROLE))
    # PostgreSQL 15 and later no longer let PUBLIC create in schema public; revoke it anyway, so the rule does
    # not depend on the server version (ADR 0011).
    bind.execute(sa.text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
    bind.execute(sa.text(f'REVOKE CREATE ON SCHEMA public FROM "{role}"'))
    bind.execute(sa.text(f'GRANT USAGE ON SCHEMA public TO "{role}"'))
    # No default privileges: a table added later grants nothing until its own migration says so.
    bind.execute(sa.text(f'GRANT SELECT, INSERT, UPDATE ON accounts TO "{role}"'))
    # The trail is append only: SELECT and INSERT, nothing else. L1.4 narrows INSERT to chosen columns, so the
    # database sets the time (RULE-L2).
    bind.execute(sa.text(f'GRANT SELECT, INSERT ON audit_entries TO "{role}"'))
    # Temporary: id is a serial today, so inserting needs USAGE on its sequence (never UPDATE: that allows setval).
    # L1.4 turns id into an identity column and removes this grant. alembic_version gets nothing.
    bind.execute(sa.text(f'GRANT USAGE ON SEQUENCE audit_entries_id_seq TO "{role}"'))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    role = _role_name()
    # The role itself stays (it belongs to the server, and a later upgrade finds it); it loses what 0002 gave it.
    bind.execute(sa.text(f'REVOKE ALL ON SEQUENCE audit_entries_id_seq FROM "{role}"'))
    bind.execute(sa.text(f'REVOKE ALL ON audit_entries, accounts FROM "{role}"'))
    bind.execute(sa.text(f'REVOKE USAGE ON SCHEMA public FROM "{role}"'))
