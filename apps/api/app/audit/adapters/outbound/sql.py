"""The audit table and its adapter over PostgreSQL (Amazon RDS PostgreSQL on AWS). The table is owned by the owner
role and created by Alembic; the API role may add and read only (ADR 0011, 0012)."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Identity, Integer, String, Text, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.audit.application.ports import RecordedEntry
from app.audit.domain.entry import AuditEntry, Kind, Person
from app.infrastructure.db import Base


class AuditRow(Base):
    __tablename__ = "audit_entries"
    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    # The database sets the time, never the application (RULE-L2).
    at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    kind: Mapped[str] = mapped_column(String, server_default="account")
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_name: Mapped[str | None] = mapped_column(String, nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String)
    target_id: Mapped[str] = mapped_column(String)
    target_name: Mapped[str | None] = mapped_column(String, nullable=True)
    target_email: Mapped[str | None] = mapped_column(String, nullable=True)
    details: Mapped[list | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


def _person(id_: str, name: str | None, email: str | None) -> Person:
    return Person(id_, name, email)


def _to_domain(r: AuditRow) -> RecordedEntry:
    return RecordedEntry(
        r.id,
        r.at,
        AuditEntry(
            actor=_person(r.actor_id, r.actor_name, r.actor_email) if r.actor_id is not None else None,
            action=r.action,
            kind=Kind(r.kind),
            target=_person(r.target_id, r.target_name, r.target_email),
            details=tuple(_person(d["id"], d.get("name"), d.get("email")) for d in (r.details or [])),
            reason=r.reason,
        ),
    )


class SqlAuditEntries:
    def __init__(self, session: Session):
        self._s = session

    def add(self, entry: AuditEntry) -> None:
        actor = entry.actor
        self._s.add(
            AuditRow(
                kind=entry.kind.value,
                actor_id=actor.id if actor else None,
                actor_name=actor.name if actor else None,
                actor_email=actor.email if actor else None,
                action=entry.action,
                target_id=entry.target.id,
                target_name=entry.target.name,
                target_email=entry.target.email,
                details=[{"id": p.id, "name": p.name, "email": p.email} for p in entry.details],
                reason=entry.reason,
            )
        )
        self._s.flush()

    def list_newest_first(self) -> list[RecordedEntry]:
        return [_to_domain(r) for r in self._s.scalars(select(AuditRow).order_by(AuditRow.id.desc()))]
