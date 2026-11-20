"""The bridges between contexts. This is the only place that knows both sides (ADR 0010, decision 14)."""

from app.access.application.ports import AccountEvent
from app.access.domain.account import Account
from app.audit.application.service import AuditService
from app.audit.domain.caller import Caller
from app.audit.domain.entry import AuditEntry, Kind, Person


class AccessAuditBridge:
    """Access's AuditLog port, answered by Audit's use case, on the same session as the request."""

    def __init__(self, audit: AuditService):
        self._audit = audit

    def record(self, event: AccountEvent) -> None:
        actor = event.actor
        self._audit.record(
            AuditEntry(
                actor=Person(actor.id, actor.name, actor.email) if actor else None,
                action=event.action,
                kind=Kind.account,
                target=Person(event.target.id, event.target.name, event.target.email),
                reason=event.reason,
            )
        )


def audit_caller(account: Account) -> Caller:
    """The guard's account, in Audit's words. Whether that may read is for AuditService.read to say."""
    return Caller(account.id, is_administrator=account.is_active_administrator)
