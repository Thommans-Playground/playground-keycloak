from dataclasses import dataclass
from typing import Protocol

from app.access.domain.account import Account


class IdentityProvider(Protocol):
    """What we ask of Keycloak as an administrator. Sign in itself is Keycloak's."""

    def enable_user(self, identity: str) -> None: ...
    def disable_user(self, identity: str) -> None: ...
    def end_sessions(self, identity: str) -> None: ...


class AccountRepository(Protocol):
    def by_identity(self, identity: str) -> Account | None: ...
    def by_id(self, account_id: str) -> Account | None: ...
    def add(self, account: Account) -> None: ...
    def save(self, account: Account) -> None: ...
    def list(self, status: str | None = None) -> list[Account]: ...
    def count_active_administrators(self) -> int: ...
    def lock_active_administrators(self) -> "list[Account]": ...


class UnitOfWork(Protocol):
    """Makes what was saved so far permanent (ADR 0009: commit before Keycloak)."""

    def commit(self) -> None: ...


@dataclass(frozen=True)
class AccountRef:
    """An account as it is named at the moment of the change (copied, so a later rename does not rewrite it)."""

    id: str
    name: str
    email: str

    @classmethod
    def of(cls, account: Account) -> "AccountRef":
        return cls(account.id, account.name, account.email)


@dataclass(frozen=True)
class AccountEvent:
    """What Access did: who (nobody for a first request), what, to which account, and why where a reason was asked."""

    actor: AccountRef | None
    action: str
    target: AccountRef
    reason: str | None


class AuditLog(Protocol):
    """Where Access says what it changed, in its own words. It cannot read the trail, edit an entry or set the time."""

    def record(self, event: AccountEvent) -> None: ...


class SecurityLog(Protocol):
    """Where Access says that it refused a request, for the operators (decision 17). Never a token or typed text."""

    def event(
        self,
        name: str,
        result: str,
        person_id: str | None = None,
        session_id: str | None = None,
        reason: str | None = None,
    ) -> None: ...


@dataclass(frozen=True)
class Principal:
    """Who the token says the caller is. What they may do is decided from our own database, never from this."""

    identity: str
    name: str
    email: str
    email_verified: bool


class InvalidToken(Exception):
    """The token is not acceptable. The reason is for the server's log; the caller only learns it was refused."""


class TokenVerifier(Protocol):
    def verify(self, token: str) -> Principal: ...
