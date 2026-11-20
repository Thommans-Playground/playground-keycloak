from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.audit.domain.entry import AuditEntry


@dataclass(frozen=True)
class RecordedEntry:
    """An entry as stored: with the id and the time that the database gave it (RULE-L2)."""

    id: int
    at: datetime
    entry: AuditEntry


class SecurityLog(Protocol):
    """Where Audit says that the trail was read, for the operators (decision 17). Never an audit entry (AC-82)."""

    def event(
        self,
        name: str,
        result: str,
        person_id: str | None = None,
        session_id: str | None = None,
        reason: str | None = None,
    ) -> None: ...


class AuditEntries(Protocol):
    """Add and read, nothing else: the trail only grows (decision 21, AC-79)."""

    def add(self, entry: AuditEntry) -> None: ...
    def list_newest_first(self) -> list[RecordedEntry]: ...
