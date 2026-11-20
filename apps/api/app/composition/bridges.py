"""The bridges between contexts. This is the only place that knows both sides (ADR 0010, decision 14)."""

from app.access.application.ports import AccountEvent
from app.access.application.service import AccessService
from app.access.domain.account import Account
from app.audit.application.service import AuditService
from app.audit.domain.caller import Caller
from app.audit.domain.entry import AuditEntry, Kind, Person
from app.projects.application.ports import People, ProjectEvent
from app.projects.domain.caller import Caller as ProjectsCaller


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


class AccountStatusBridge:
    """Projects' AccountStatus port, answered by Access's use case, on the same session as the request."""

    def __init__(self, access: AccessService):
        self._access = access

    def active_among(self, ids: set[str]) -> set[str]:
        return set(self._access.active_among(list(ids)))


class PeopleBridge:
    """Projects' People port, answered by Access's use case, on the same session as the request."""

    def __init__(self, access: AccessService):
        self._access = access

    def names_of(self, ids: list[str]) -> dict[str, tuple[str, str]]:
        return {p.id: (p.name, p.email) for p in self._access.people(ids)}


class ProjectsAuditBridge:
    """Projects' AuditLog port, answered by Audit's use case, on the same session as the request. The names are the
    ones people have now, written into the entry so a later rename does not change it (RULE-L4)."""

    def __init__(self, audit: AuditService, people: People):
        self._audit = audit
        self._people = people

    def record(self, event: ProjectEvent) -> None:
        names = self._people.names_of([event.actor_id, *event.member_ids])

        def person(account_id: str) -> Person:
            name, email = names.get(account_id, (None, None))
            return Person(account_id, name, email)

        self._audit.record(
            AuditEntry(
                actor=person(event.actor_id),
                action=event.action,
                kind=Kind.project,
                target=Person(event.project_id, event.project_name),  # the project: id and name, no email
                details=tuple(person(i) for i in event.member_ids),
                reason=event.reason,
            )
        )


def audit_caller(account: Account) -> Caller:
    """The guard's account, in Audit's words. Whether that may read is for AuditService.read to say."""
    return Caller(account.id, is_administrator=account.is_active_administrator)


def projects_caller(account: Account) -> ProjectsCaller:
    """The guard's account, in Projects' words (ADR 0002, 0015). The guard chain has refused a deactivated, pending
    or unknown account before this is built; whether an administrator may act is for the use case to say."""
    return ProjectsCaller(account.id, is_administrator=account.is_active_administrator)
