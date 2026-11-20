from datetime import datetime

from sqlalchemy import DateTime, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.access.domain.account import Account, Role, Status
from app.infrastructure.db import Base


class AccountRow(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    identity: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    created: Mapped[datetime] = mapped_column(DateTime)
    created_by: Mapped[str | None] = mapped_column(String, nullable=True)


def _to_domain(r: AccountRow) -> Account:
    return Account(
        r.id,
        r.identity,
        r.name,
        r.email,
        Role(r.role),
        Status(r.status),
        r.created,
        r.created_by,
    )


class SqlAccounts:
    def __init__(self, session: Session):
        self._s = session

    def by_identity(self, identity: str) -> Account | None:
        r = self._s.scalar(select(AccountRow).where(AccountRow.identity == identity))
        return _to_domain(r) if r else None

    def by_id(self, account_id: str) -> Account | None:
        r = self._s.get(AccountRow, account_id)
        return _to_domain(r) if r else None

    def add(self, a: Account) -> None:
        self._s.add(
            AccountRow(
                id=a.id,
                identity=a.identity,
                name=a.name,
                email=a.email,
                role=a.role.value,
                status=a.status.value,
                created=a.created,
                created_by=a.created_by,
            )
        )
        self._s.flush()

    def save(self, a: Account) -> None:
        r = self._s.get(AccountRow, a.id)
        r.name, r.email, r.role, r.status = (
            a.name,
            a.email,
            a.role.value,
            a.status.value,
        )
        self._s.flush()

    def list(self, status: str | None = None) -> list[Account]:
        q = select(AccountRow).order_by(AccountRow.created)
        if status:
            q = q.where(AccountRow.status == status)
        return [_to_domain(r) for r in self._s.scalars(q)]

    def count_active_administrators(self) -> int:
        q = (
            select(func.count())
            .select_from(AccountRow)
            .where(
                AccountRow.role == Role.administrator.value,
                AccountRow.status == Status.active.value,
            )
        )
        return self._s.scalar(q) or 0

    def lock_active_administrators(self) -> "list[Account]":
        # Realises UC-A4 AC-62 (ADR 0009): lock the rows in id order; populate_existing re-reads them fresh.
        q = (
            select(AccountRow)
            .where(
                AccountRow.role == Role.administrator.value,
                AccountRow.status == Status.active.value,
            )
            .order_by(AccountRow.id)
            .execution_options(populate_existing=True)
        )
        if self._s.get_bind().dialect.name != "sqlite":  # SQLite has no row locks
            q = q.with_for_update()
        return [_to_domain(r) for r in self._s.scalars(q)]


class SqlUnitOfWork:
    def __init__(self, session: Session):
        self._s = session

    def commit(self) -> None:
        self._s.commit()
