"""The audit table moves to the Audit context's shape (UC-L1 TSK-L1.4, ADR 0011 amendments, decision 14, 22).

Runs as the OWNER role. Adds kind (old rows become account entries), details and the names and emails at the time (old
rows keep none). The database sets the time (RULE-L2): `at` gets a default and the API loses the right to name it.
On PostgreSQL the id becomes an identity column (so the API role needs no sequence grant), and INSERT is granted on
every column except id and at. SQLite has no roles and no identity columns, so there only the columns change.
Safe to run twice: each step looks at what is already there.

Revision ID: 0003
Revises: 0002
"""

import re

import sqlalchemy as sa
from alembic import op

from app.infrastructure.config import Settings

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

NEW_COLUMNS = ("kind", "actor_name", "actor_email", "target_name", "target_email", "details")
# The API role may add these and nothing else: id and at are set by the database.
API_INSERT_COLUMNS = (
    "kind", "actor_id", "actor_name", "actor_email", "action",
    "target_id", "target_name", "target_email", "details", "reason",
)
UTC_NOW = sa.text("(now() AT TIME ZONE 'utc')")


def _role_name() -> str:
    name = Settings().api_db_user
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", name):
        raise RuntimeError(f"API_DB_USER '{name}' is not a plain lower case role name")
    return name


def upgrade() -> None:
    bind = op.get_bind()
    present = {c["name"] for c in sa.inspect(bind).get_columns("audit_entries")}
    postgres = bind.dialect.name == "postgresql"
    default_at = UTC_NOW if postgres else sa.text("CURRENT_TIMESTAMP")

    with op.batch_alter_table("audit_entries") as batch:
        if "kind" not in present:
            batch.add_column(sa.Column("kind", sa.String(), nullable=False, server_default="account"))
        for name in ("actor_name", "actor_email", "target_name", "target_email"):
            if name not in present:
                batch.add_column(sa.Column(name, sa.String(), nullable=True))
        if "details" not in present:
            batch.add_column(sa.Column("details", sa.JSON(), nullable=True))
        batch.alter_column("at", existing_type=sa.DateTime(), existing_nullable=False, server_default=default_at)

    if not postgres:
        return
    role = _role_name()
    identity = bind.execute(sa.text(
        "SELECT is_identity FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = 'audit_entries' AND column_name = 'id'"
    )).scalar_one()
    if identity != "YES":
        # serial -> identity: keep the numbering going after the rows that exist.
        start = int(bind.execute(sa.text("SELECT coalesce(max(id), 0) + 1 FROM audit_entries")).scalar_one())
        bind.execute(sa.text("ALTER TABLE audit_entries ALTER COLUMN id DROP DEFAULT"))
        bind.execute(sa.text("DROP SEQUENCE IF EXISTS audit_entries_id_seq"))  # also drops the USAGE grant of 0002
        bind.execute(sa.text(f"ALTER TABLE audit_entries ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (START WITH {start})"))
    # An identity column needs no sequence grant. Nothing on the sequence, whatever an earlier run left.
    bind.execute(sa.text(f'REVOKE ALL ON SEQUENCE audit_entries_id_seq FROM "{role}"'))
    # Table level INSERT out, column level INSERT in: the API cannot name the id or the time. SELECT stays.
    bind.execute(sa.text(f'REVOKE INSERT ON audit_entries FROM "{role}"'))
    bind.execute(sa.text(f'REVOKE INSERT (id, at) ON audit_entries FROM "{role}"'))
    columns = ", ".join(f'"{c}"' for c in API_INSERT_COLUMNS)
    bind.execute(sa.text(f'GRANT INSERT ({columns}) ON audit_entries TO "{role}"'))


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        role = _role_name()
        bind.execute(sa.text(f'REVOKE ALL ON audit_entries FROM "{role}"'))
        bind.execute(sa.text(f'GRANT SELECT, INSERT ON audit_entries TO "{role}"'))
    # The identity column stays: it is a serial in every way the old code used it. The new columns go.
    with op.batch_alter_table("audit_entries") as batch:
        batch.alter_column("at", existing_type=sa.DateTime(), existing_nullable=False, server_default=None)
        for name in NEW_COLUMNS:
            batch.drop_column(name)
