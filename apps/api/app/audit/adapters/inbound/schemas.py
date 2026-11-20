"""What goes over HTTP for the trail. The first six fields are the ones the web already reads."""

from datetime import datetime

from pydantic import BaseModel

from app.audit.application.ports import RecordedEntry


class PersonOut(BaseModel):
    id: str
    name: str | None
    email: str | None


class EntryOut(BaseModel):
    id: int
    at: datetime
    kind: str
    actor_id: str | None
    actor_name: str | None
    actor_email: str | None
    action: str
    target_id: str
    target_name: str | None
    target_email: str | None
    details: list[PersonOut]
    reason: str | None

    @classmethod
    def of(cls, r: RecordedEntry) -> "EntryOut":
        e = r.entry
        return cls(
            id=r.id,
            at=r.at,
            kind=e.kind.value,
            actor_id=e.actor.id if e.actor else None,
            actor_name=e.actor.name if e.actor else None,
            actor_email=e.actor.email if e.actor else None,
            action=e.action,
            target_id=e.target.id,
            target_name=e.target.name,
            target_email=e.target.email,
            details=[PersonOut(id=p.id, name=p.name, email=p.email) for p in e.details],
            reason=e.reason,
        )
