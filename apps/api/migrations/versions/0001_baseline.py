"""Baseline: the schema of today (accounts and audit_entries).

A table that already exists is skipped, so a dev database that create_all filled before Alembic upgrades
without error (ADR 0004, 0012).

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if "accounts" not in existing:
        op.create_table(
            "accounts",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("identity", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("created", sa.DateTime(), nullable=False),
            sa.Column("created_by", sa.String(), nullable=True),
        )
        op.create_index("ix_accounts_identity", "accounts", ["identity"], unique=True)
        op.create_index("ix_accounts_email", "accounts", ["email"])
    if "audit_entries" not in existing:
        op.create_table(
            "audit_entries",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("at", sa.DateTime(), nullable=False),
            sa.Column("actor_id", sa.String(), nullable=True),
            sa.Column("action", sa.String(), nullable=False),
            sa.Column("target_id", sa.String(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    op.drop_table("audit_entries")
    op.drop_index("ix_accounts_email", table_name="accounts")
    op.drop_index("ix_accounts_identity", table_name="accounts")
    op.drop_table("accounts")
