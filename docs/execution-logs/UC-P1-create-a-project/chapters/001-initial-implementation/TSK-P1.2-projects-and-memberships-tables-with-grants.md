# Task P1.2: The projects and memberships tables, with grants

**Task ID:** TSK-P1.2 · **Use Case:** UC-P1 · **Criteria:** AC-95 · **Code matched at:** `7481263`

What this does and why: [summary, task P1.2](summary.md#p12-the-projects-and-memberships-tables-with-grants).

Run from `apps/api/`: `uv run pytest tests/test_architecture.py tests/test_migrations.py tests/test_projects_permissions.py -q`

Work test first in each step: write the test, run it, see it fail, then write the code.

---

## Step 1: the tests that name the new context and tables (SQLite)

**Test** (Unit and Architecture):

- `tests/migrations_support.py` and `tests/test_migrations.py`: import `app.projects.adapters.outbound.sql` so the tables
  register on `Base`, as `access` and `audit` already do.
- `tests/test_architecture.py`: the contexts test now expects `projects` as well, and the migration-imports test accepts
  `app.projects.adapters.outbound.sql`.
- `tests/test_migrations.py`: `test_migrations_create_todays_schema` expects the tables `accounts`, `audit_entries`,
  `projects`, `memberships`; the new tests are below. The head-revision assertion (`at == "0004"`) sits at the end of the
  existing `test_the_roles_migration_can_run_twice`, which then fails too, as does `test_migrations_match_the_models` (the
  models now have tables that no migration makes).

```python
# apps/api/tests/test_migrations.py
def test_the_project_tables_have_the_columns_of_the_ontology(engine):
    upgrade(as_owner(engine))
    assert columns(engine, "projects") == {"id", "name", "created_by", "created_at"}
    assert columns(engine, "memberships") == {"project_id", "account_id", "added_by", "added_at"}
```

```python
# apps/api/tests/test_migrations.py
def test_the_project_migration_can_run_twice(engine):
    owner = as_owner(engine)
    upgrade(owner)
    stamp(owner, "0003")
    upgrade(owner)  # the tables and the grants exist: neither a failure nor a change
    with owner.connect() as connection:
        at = MigrationContext.configure(connection).get_current_revision()
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert at == "0004" and diff == []
```

```python
# apps/api/tests/test_migrations.py
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
```

```python
# apps/api/tests/test_architecture.py
def test_there_is_at_least_the_access_audit_and_projects_contexts():
    assert {"access", "audit", "projects"} <= set(contexts())
```

**Code**:

Make the folders `app/projects/` with `domain/`, `application/`, `adapters/inbound/`, `adapters/outbound/`, each with an empty
`__init__.py` (ADR 0010). Add one line to `migrations/env.py` so Alembic sees the tables:

```python
# apps/api/migrations/env.py
import app.projects.adapters.outbound.sql  # noqa: F401 - registers the project tables on Base
```

Then write the two table classes in `app/projects/adapters/outbound/sql.py`. At `7481263` that file also holds the repository
`SqlProjects` of later tasks; these are the two classes of this task, copied from it, with its imports `from datetime import
datetime`, `from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func`, `from sqlalchemy.orm import Mapped,
mapped_column` and `from app.infrastructure.db import Base`:

```python
# apps/api/app/projects/adapters/outbound/sql.py
class ProjectRow(Base):
    __tablename__ = "projects"
    # A random UUID string made by the application, so an id reveals nothing about count or order (ADR 0015).
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(String)
    # The database sets the time, never the application (RULE-L2).
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

```python
# apps/api/app/projects/adapters/outbound/sql.py
class MembershipRow(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("project_id", "account_id", name="uq_memberships_project_account"),)
    # The unique key is the identity of a membership: a person is in a project once (AC-90).
    __mapper_args__ = {"primary_key": ["project_id", "account_id"]}
    project_id: Mapped[str] = mapped_column(String, ForeignKey("projects.id"))
    account_id: Mapped[str] = mapped_column(String)
    added_by: Mapped[str] = mapped_column(String)
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

Write `migrations/versions/0004_projects.py`. The stage shape is the header, `revision` ids, `UTC_NOW`, `_role_name` and
`upgrade` up to the two `create_table` calls, then `if not postgres: return`. The final file, with the grants, is in stage 4.

**Logic.** The id is a string made by the application, so there is no sequence. The database sets both times through `server_default`. The
unique key on (project, account) is the identity of a membership, and the foreign key ties it to an existing project.

On SQLite there are no roles, so the migration makes the two tables and stops. Each table is made only if it is not already
there, so a second run changes nothing.

---

## Step 2: the grant test (PostgreSQL, not run)

**Test** (Unit and Integration):

`tests/test_projects_permissions.py`, every test marked `@pytest.mark.ac("AC-95")` and skipped without `TEST_DATABASE_URL`. A
fixture `roles` yields the API engine and the owner engine on a migrated database holding two projects (`p-1` with a member,
`p-9` with none) and one membership. The tests:

- one for each statement in `REFUSED` (parametrized): the API role is refused with `42501`, the rows are unchanged, and
  the owner runs the same statement as the control
- the API role can add and read projects and memberships, and the database filled `created_at` and `added_at`
- the API role can remove a membership
- a person is in a project once (`23505`); a membership needs an existing project (`23503`)
- the API role may insert only the columns the application sets, and holds no UPDATE on any column

Also in `tests/test_audit_permissions.py`, the allow list of tables the API role may touch gains
`"projects": {"SELECT"}` and `"memberships": {"SELECT", "DELETE"}` (INSERT is on chosen columns only, tested above).

The statements and the first test:

```python
# apps/api/tests/test_projects_permissions.py
REFUSED = {
    "update a project": "UPDATE projects SET name = 'renamed'",
    "delete a project": "DELETE FROM projects WHERE id = 'p-9'",
    "truncate projects": "TRUNCATE projects CASCADE",
    "alter projects": "ALTER TABLE projects ADD COLUMN extra text",
    "drop projects": "DROP TABLE projects CASCADE",
    "update a membership": "UPDATE memberships SET added_by = 'someone'",
    "truncate memberships": "TRUNCATE memberships",
    "alter memberships": "ALTER TABLE memberships ADD COLUMN extra text",
    "drop memberships": "DROP TABLE memberships",
    "name created_at": (
        "INSERT INTO projects (id, name, created_by, created_at) VALUES ('p-2', 'Beta', 'admin-1', '2020-01-01')"
    ),
    "name added_at": (
        "INSERT INTO memberships (project_id, account_id, added_by, added_at) "
        "VALUES ('p-1', 'member-2', 'admin-1', '2020-01-01')"
    ),
}
```

```python
# apps/api/tests/test_projects_permissions.py
@pytest.mark.ac("AC-95")
@pytest.mark.parametrize("statement", REFUSED.values(), ids=REFUSED.keys())
def test_the_api_role_cannot_change_a_project_or_a_membership_and_the_owner_can(roles, statement):
    api, owner = roles
    before = rows(owner)
    assert len(before[0]) == 2 and len(before[1]) == 1

    # Each command in its own transaction, so one refusal does not hide another.
    with pytest.raises(DBAPIError) as refused:
        with api.begin() as connection:
            connection.execute(text(statement))
    assert refused.value.orig.sqlstate == PERMISSION_DENIED
    assert rows(owner) == before

    # The control: the owner runs the very same statement and it is accepted (then rolled back),
    # so a typo in the statement cannot make the refusal above pass.
    with owner.connect() as connection:
        transaction = connection.begin()
        connection.execute(text(statement))
        transaction.rollback()
    assert rows(owner) == before
```

**Code**:

The final file, `migrations/versions/0004_projects.py`:

```python
# apps/api/migrations/versions/0004_projects.py
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
```

**Logic.** The migration revokes everything first, then grants, so a second run (or a hand edit) ends in the same place. `projects` gets
SELECT and INSERT of three columns; `memberships` gets SELECT, DELETE and INSERT of three columns. The two time columns are not
insertable, so the database always sets them. No default privileges are set. `_role_name` refuses a role name that is not plain
lower case, because the name is placed in the SQL text.
