"""The Projects context's tables, and the API role's column level grants on them (UC-P1 TSK-P1.2, ADR 0015, AC-95).

Runs as the OWNER role. Creates `projects` and `memberships` (ids are UUID strings made by the application, so no
sequence). The database sets created_at and added_at. On PostgreSQL the API role gets, per table and with no default
privileges: SELECT and INSERT on the columns the application sets for `projects` (no UPDATE, no DELETE); SELECT,
INSERT on the columns the application sets and DELETE for `memberships` (no UPDATE). SQLite has no roles, so there
only the tables are made.
Safe to run twice: each step looks at what is already there.

Revision ID: 0004
Revises: 0003
"""

import re

import sqlalchemy as sa
from alembic import op

from app.infrastructure.config import Settings

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

UTC_NOW = sa.text("(now() AT TIME ZONE 'utc')")


def _role_name() -> str:
    name = Settings().api_db_user
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", name):
        raise RuntimeError(f"API_DB_USER '{name}' is not a plain lower case role name")
    return name


def upgrade() -> None:
    bind = op.get_bind()
    postgres = bind.dialect.name == "postgresql"
    now = UTC_NOW if postgres else sa.text("CURRENT_TIMESTAMP")
    existing = set(sa.inspect(bind).get_table_names())

    if "projects" not in existing:
        op.create_table(
            "projects",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("created_by", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=now),
        )
    if "memberships" not in existing:
        op.create_table(
            "memberships",
            sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id"), nullable=False),
            sa.Column("account_id", sa.String(), nullable=False),
            sa.Column("added_by", sa.String(), nullable=False),
            sa.Column("added_at", sa.DateTime(), nullable=False, server_default=now),
            sa.UniqueConstraint("project_id", "account_id", name="uq_memberships_project_account"),
        )

    if not postgres:
        return
    role = _role_name()
    # Start from nothing, so a second run (or a hand edit) ends in the same place.
    bind.execute(sa.text(f'REVOKE ALL ON projects, memberships FROM "{role}"'))
    bind.execute(sa.text(f'GRANT SELECT, INSERT (id, name, created_by) ON projects TO "{role}"'))
    bind.execute(sa.text(f'GRANT SELECT, DELETE, INSERT (project_id, account_id, added_by) ON memberships TO "{role}"'))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        role = _role_name()
        bind.execute(sa.text(f'REVOKE ALL ON projects, memberships FROM "{role}"'))
    op.drop_table("memberships")
    op.drop_table("projects")
