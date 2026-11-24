# TSK-P1.2: the projects and memberships tables, with grants

AC-95 written · plan status: **draft, not reviewed** · matches the code at `7481263`

Ground rules, the layout and the commands are in the [chapter summary](summary.md).

This is the plan someone follows to build this task. It was written by working backwards from the code that exists, so
its final code is that code: each block marked `# file` is a copy of that file at the commit above. All paths are
relative to `apps/api/`.

## 1. What we are building, and why

Two tables, owned by the owner role that runs the migrations, and a database role for the API that can do only what
Projects needs. Nothing here creates a project yet (TSK-P1.3).

| AC | Given | Then | Why it exists |
|---|---|---|---|
| AC-95 | the database role the API connects with (not the owner role that runs the migrations) | it tries to update or delete a project, update a membership, or truncate, alter or drop either table: the database refuses each one (42501), while adding and reading projects and memberships, and deleting a membership, still work | A project and its membership history must not be rewritable by a bug or by stolen API credentials. The rule is enforced by permissions in PostgreSQL, like the audit table (AC-80, FR-7, FR-9). |

## 2. The logic

1. **The API role holds an allow list, from nothing.** The migration revokes everything first, then grants: on `projects`
   SELECT and INSERT of `id, name, created_by` (no UPDATE, no DELETE, no TRUNCATE); on `memberships` SELECT, DELETE and
   INSERT of `project_id, account_id, added_by` (no UPDATE). No default privileges. A second run ends in the same place
   (AC-95).
2. **Only the columns the application sets are insertable.** `created_at` and `added_at` are set by the database, so an
   insert that names one is refused too (the same idea as RULE-L2, which says it for an audit entry).
3. **A membership can be removed but never edited.** Removing is a DELETE of one row; an UPDATE is refused. So history
   is the difference between the rows before and after (ADR 0015).
4. **Ids are random UUID strings made by the application,** so there is no sequence, and an id reveals neither count nor
   order (ADR 0015).
5. **A person is in a project once.** A unique key on (project, account) is the identity of a membership, and a foreign
   key ties it to an existing project (AC-90, built on in the later slices).
6. **The control.** Each forbidden statement runs as the API role in its own transaction and fails with `42501`; then
   the owner runs the very same statement and it is accepted (rolled back), so a typo cannot make a refusal pass.
7. **PostgreSQL only.** SQLite has no roles, so there the migration makes the tables and stops; the grant test is skipped
   unless `TEST_DATABASE_URL` is set.

**Where it lives:** the tables in `app/projects/adapters/outbound/sql.py` (the adapter, with `Base`), the grants in one
Alembic migration `migrations/versions/0004_projects.py` (ADR 0012), the grant test in
`tests/test_projects_permissions.py`. The Projects folders exist so the architecture test sees the context (ADR 0010).

## 3. The plan

Four stages. A stage with PostgreSQL in its title was not run for this file.

### Stage 1: the tests that name the new context and tables (SQLite)

**1a. Write the tests.**

- `tests/migrations_support.py` and `tests/test_migrations.py`: import `app.projects.adapters.outbound.sql` so the tables
  register on `Base`, as `access` and `audit` already do.
- `tests/test_migrations.py`: `test_migrations_create_todays_schema` now expects the tables `accounts`, `audit_entries`,
  `projects`, `memberships`; new `test_the_project_tables_have_the_columns_of_the_ontology` (`id, name, created_by,
  created_at` and `project_id, account_id, added_by, added_at`); the head revision is `0004`; new
  `test_the_project_migration_can_run_twice` and `test_the_database_sets_when_a_project_and_a_membership_were_added`.
  The head-revision assertion (`at == "0004"`) is not a test of its own: it sits at the end of the existing
  `test_the_roles_migration_can_run_twice`, which then fails too, as does `test_migrations_match_the_models` (the models
  now have tables that no migration makes).
- `tests/test_architecture.py`: the contexts test now expects `projects` as well, and the migration-imports test accepts
  `app.projects.adapters.outbound.sql`.

Run `uv run pytest -q`. **Expect** a collection error, `ModuleNotFoundError: No module named 'app.projects'` (checked).

### Stage 2: the context folders and the table definitions (SQLite)

**2a. Make the folders** `app/projects/` with `domain/`, `application/`, `adapters/inbound/`, `adapters/outbound/`, each
with an empty `__init__.py` (ADR 0010). Add one line to `migrations/env.py` so Alembic sees the tables:

```python
# migrations/env.py
import app.projects.adapters.outbound.sql  # noqa: F401 - registers the project tables on Base
```

**2b. Write the two table classes** in `app/projects/adapters/outbound/sql.py`. At `7481263` that file also holds the
repository `SqlProjects` of later tasks; these are the two classes of this task, copied from it, with its imports
`from datetime import datetime`, `from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func`,
`from sqlalchemy.orm import Mapped, mapped_column` and `from app.infrastructure.db import Base`:

```python
# app/projects/adapters/outbound/sql.py
class ProjectRow(Base):
    __tablename__ = "projects"
    # A random UUID string made by the application, so an id reveals nothing about count or order (ADR 0015).
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(String)
    # The database sets the time, never the application (RULE-L2).
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


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

Run `uv run pytest -q`. **Expect** `6 failed, 188 passed, 46 skipped`: six migration tests fail because no
migration makes the tables yet (checked): `test_migrations_create_todays_schema`,
`test_the_project_tables_have_the_columns_of_the_ontology`, `test_migrations_match_the_models`,
`test_the_roles_migration_can_run_twice`, `test_the_project_migration_can_run_twice` and
`test_the_database_sets_when_a_project_and_a_membership_were_added`.

### Stage 3: the migration makes the tables (SQLite)

Write `migrations/versions/0004_projects.py`. This is the stage shape, not the final file: the header, `revision`
ids, `UTC_NOW`, `_role_name` and `upgrade` up to the two `create_table` calls, then `if not postgres: return`. The final
file is in stage 4.

Run `uv run pytest -q`. **Expect** `194 passed, 46 skipped` (checked with the final file, which differs from this shape
only in code that runs on PostgreSQL; this shape on its own was not run).

### Stage 4: the grants and the grant test (PostgreSQL, not run)

**4a. Write the test** `tests/test_projects_permissions.py`, every test marked `@pytest.mark.ac("AC-95")` and skipped
without `TEST_DATABASE_URL`. A fixture `roles` yields the API engine and the owner engine on a migrated database holding
two projects (`p-1` with a member, `p-9` with none) and one membership. The tests:

- one for each statement in `REFUSED` (parametrized): the API role is refused with `42501`, the rows are unchanged, and
  the owner runs the same statement as the control
- the API role can add and read projects and memberships, and the database filled `created_at` and `added_at`
- the API role can remove a membership
- a person is in a project once (`23505`); a membership needs an existing project (`23503`)
- the API role may insert only the columns the application sets, and holds no UPDATE on any column

Also in `tests/test_audit_permissions.py`, the allow list of tables the API role may touch gains
`"projects": {"SELECT"}` and `"memberships": {"SELECT", "DELETE"}` (INSERT is on chosen columns only, tested above).

The statements and the first test, copied:

```python
# tests/test_projects_permissions.py
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

Run with `TEST_DATABASE_URL` (always the `playground_test` database) and `TEST_MIGRATION_DATABASE_URL` set:
`uv run pytest tests/test_projects_permissions.py -q`. **Expect** the allow-side tests (add a project and read it, remove a membership, insert only the columns the application
sets) to fail while the migration has no grant lines, because the API role then holds no privilege at all. The
`REFUSED` cases would still pass, since an API role with no grants is refused everything (reasoned, not run:
`TEST_DATABASE_URL` was not set when this file was written, so no count is known).

**4b. Add the grants and finish the migration.** This is the final file, `migrations/versions/0004_projects.py`:

```python
# migrations/versions/0004_projects.py
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

**Expect** all of `tests/test_projects_permissions.py` and `tests/test_audit_permissions.py` to pass on PostgreSQL (not
run). The commit message records `240 passed` on PostgreSQL after this task; that figure was not reproduced here.

## 4. Check it yourself

On SQLite (checked at `7481263`):

```
uv run pytest tests/test_migrations.py -q        # 10 passed, 2 skipped
uv run pytest tests/test_architecture.py -q      # 21 passed
uv run pytest tests/test_projects_permissions.py tests/test_audit_permissions.py -q   # all skipped without TEST_DATABASE_URL
```

Right after this task alone the whole suite was `194 passed, 46 skipped` (checked; the 46 includes the 17 PostgreSQL-only tests of `test_projects_permissions.py`, which skip without `TEST_DATABASE_URL`).

On PostgreSQL, with `TEST_DATABASE_URL` and `TEST_MIGRATION_DATABASE_URL` pointing at `playground_test` (not run for
this file):

```
uv run pytest tests/test_projects_permissions.py tests/test_audit_permissions.py tests/test_migrations.py -q
```

## 5. Where this leaves things

- Source: `migrations/versions/0004_projects.py`, `migrations/env.py`, `app/projects/adapters/outbound/sql.py` (the
  `ProjectRow` and `MembershipRow` classes), the empty `app/projects/` folders
- Tests: `tests/test_projects_permissions.py`, `tests/test_migrations.py`, `tests/test_audit_permissions.py`,
  `tests/test_architecture.py`, `tests/migrations_support.py`
- ADR: 0015 (tables and grants), 0012 (migrations), 0010 (layout); no new ADR.
- Not here: writing to the tables (`SqlProjects`, TSK-P1.3).

## Where the real build differs

- One commit, `48064f7`, built the task, and the grant test was written with the migration. Stage 4 splits them to show
  the test first; that split was not run.
- The PostgreSQL grant test could not be run for this file (`TEST_DATABASE_URL` unset), so no Expect in stage 4 is
  checked and the 240 figure is from the commit message only.
- `app/projects/adapters/outbound/sql.py` was 30 lines in this commit (the two table classes). Later tasks added
  `SqlProjects` to the same file; only this task's part is quoted.
- The test file and the migration are unchanged between `48064f7` and `7481263`.

## Review

Not reviewed. Write `Reviewed by <name> at <hash>` here when the plan has been read against the code.
