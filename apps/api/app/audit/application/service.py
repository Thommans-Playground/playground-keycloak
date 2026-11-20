"""Use cases of the Audit context: record what happened, and let an administrator read it."""

from app.audit.application.ports import AuditEntries, RecordedEntry
from app.audit.domain.caller import Caller
from app.audit.domain.entry import AuditEntry
from app.audit.domain.errors import NotAnAdministrator


class AuditService:
    def __init__(self, entries: AuditEntries):
        self._entries = entries

    def record(self, entry: AuditEntry) -> None:
        """Add one entry. The database gives it its time (RULE-L2); nothing here can."""
        self._entries.add(entry)

    def read(self, caller: Caller) -> list[RecordedEntry]:
        """Every entry, the newest first. Only an administrator reads (UC-L1, AC-68). An empty trail is a valid answer (AC-69)."""
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")
        return self._entries.list_newest_first()
