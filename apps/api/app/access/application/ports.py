from dataclasses import dataclass
from datetime import datetime
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


class AuditLog(Protocol):
    def record(
        self,
        actor_id: str | None,
        action: str,
        target_id: str,
        reason: str | None,
        at: datetime,
        outcome: str | None = None,
    ) -> None: ...
    def set_outcome(self, target_id: str, action: str, outcome: str) -> None: ...
    def entries(self) -> list[dict]: ...


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
