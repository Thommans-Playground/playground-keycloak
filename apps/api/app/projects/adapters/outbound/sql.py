"""The projects and memberships tables (PostgreSQL, Amazon RDS PostgreSQL on AWS). The tables are owned by the owner
role and created by Alembic; the API role gets column level grants only (ADR 0011, 0012, 0015, AC-95)."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.infrastructure.db import Base
from app.projects.domain.project import Membership, Project


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


class SqlProjects:
    """Writes a project and its memberships in the request's session, so they commit together (ADR 0015). The
    application names neither created_at nor added_at: the database sets them, and the API role may not."""

    def __init__(self, session: Session):
        self._s = session

    def add(self, project: Project) -> None:
        self._s.add(ProjectRow(id=project.id, name=project.name, created_by=project.created_by))
        self._s.flush()  # the project row first: the memberships point at it, and there is no relationship to order them
        self._s.add_all(
            MembershipRow(project_id=project.id, account_id=m.account_id, added_by=m.added_by)
            for m in project.memberships
        )
        self._s.flush()

    def by_id(self, project_id: str) -> Project | None:
        row = self._s.get(ProjectRow, project_id)
        return self._with_members([row])[0] if row else None

    def add_member(self, project_id: str, membership: Membership) -> bool:
        """INSERT one row. The unique key on (project, account) decides a race: the loser's insert fails, inside a
        savepoint so the request's transaction goes on, and is reported as 'already a member' (AC-90)."""
        try:
            with self._s.begin_nested():
                self._s.add(
                    MembershipRow(project_id=project_id, account_id=membership.account_id, added_by=membership.added_by)
                )
        except IntegrityError:
            return False
        return True

    def remove_member(self, project_id: str, account_id: str) -> bool:
        """DELETE one row, and say whether there was one. Never an UPDATE: the API role may not (ADR 0015)."""
        gone = self._s.execute(
            delete(MembershipRow)
            .where(MembershipRow.project_id == project_id, MembershipRow.account_id == account_id)
            .execution_options(synchronize_session="fetch")
        )
        return gone.rowcount > 0

    def list_all(self) -> list[Project]:
        return self._with_members(self._s.scalars(self._ordered(select(ProjectRow))).all())

    def list_for_member(self, account_id: str) -> list[Project]:
        mine = select(MembershipRow.project_id).where(MembershipRow.account_id == account_id)
        return self._with_members(
            self._s.scalars(self._ordered(select(ProjectRow).where(ProjectRow.id.in_(mine)))).all()
        )

    @staticmethod
    def _ordered(query):
        return query.order_by(ProjectRow.created_at, ProjectRow.id)

    def _with_members(self, rows: Sequence[ProjectRow]) -> list[Project]:
        """The projects with their members: one query for all the members of these projects, never one each."""
        members: dict[str, list[Membership]] = {row.id: [] for row in rows}
        if rows:
            found = self._s.scalars(
                select(MembershipRow).where(MembershipRow.project_id.in_(members)).order_by(MembershipRow.account_id)
            )
            for m in found:
                members[m.project_id].append(Membership(m.account_id, m.added_by))
        return [Project(r.id, r.name, r.created_by, tuple(members[r.id])) for r in rows]
