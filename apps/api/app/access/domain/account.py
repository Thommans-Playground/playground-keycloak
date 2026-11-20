"""The Account and its rules. No framework, database or HTTP in here (BC-ACCESS)."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class Role(StrEnum):
    user = "user"
    administrator = "administrator"


class Status(StrEnum):
    pending = "pending"
    active = "active"
    deactivated = "deactivated"


class Action(StrEnum):
    approve = "approve"
    deactivate = "deactivate"
    reinstate = "reinstate"
    promote = "promote"
    demote = "demote"


class DomainError(Exception):
    """A rule refused something. It says what went wrong, never how HTTP answers: the web layer maps that."""

    code = "domain_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ReasonRequired(DomainError):  # RULE-A3
    code = "reason_required"


class CannotChangeSelf(DomainError):  # RULE-A2
    code = "cannot_change_self"


class LastAdministrator(DomainError):  # RULE-A1
    code = "last_administrator"


class InvalidTransition(DomainError):
    code = "invalid_transition"


class AccountNotFound(DomainError):
    code = "account_not_found"


@dataclass(frozen=True)
class Account:
    id: str
    identity: str  # the Keycloak `sub`. Never the email.
    name: str
    email: str
    role: Role
    status: Status
    created: datetime
    created_by: str | None = None

    @property
    def is_active(self) -> bool:
        return self.status is Status.active

    @property
    def is_active_administrator(self) -> bool:
        return self.is_active and self.role is Role.administrator

    def with_(self, **changes) -> "Account":
        return replace(self, **changes)


def new_account(
    identity: str,
    name: str,
    email: str,
    email_verified: bool,
    setup_emails: set[str],
    active_admins: int,
    clock: Callable[[], datetime],
) -> Account:
    """A person seen for the first time (RULE-A5).

    Only a verified setup email, while no active administrator exists, makes an active administrator.
    Everyone else waits for approval.
    """
    first_admin = active_admins == 0 and email_verified and email.strip().lower() in setup_emails
    return Account(
        id=str(uuid.uuid4()),
        identity=identity,
        name=name,
        email=email,
        role=Role.administrator if first_admin else Role.user,
        status=Status.active if first_admin else Status.pending,
        created=clock(),
    )


def duplicates_by_email(accounts: list[Account]) -> dict[str, list[Account]]:
    """For each account id, the OTHER accounts with the same email (case and spaces ignored).

    Only a warning for the administrator. Identity is the sub, so nothing is merged or blocked (decision 10).
    """
    by_email: dict[str, list[Account]] = {}
    for a in accounts:
        by_email.setdefault(a.email.strip().lower(), []).append(a)
    return {a.id: [o for o in by_email[a.email.strip().lower()] if o.id != a.id] for a in accounts}


REASON_ACTIONS = {Action.deactivate, Action.reinstate, Action.promote, Action.demote}


def clean_reason(reason: str | None) -> str:
    """A reason must say something: at least three letters. Empty or noise is refused."""
    text = (reason or "").strip()
    if sum(c.isalpha() for c in text) < 3:
        raise ReasonRequired("A reason that says something is required.")
    return text


def is_repeat_deactivation(action: Action, target: Account) -> bool:
    """Deactivating a deactivated account: the one exception to the wrong state refusal (AC-77, decision 18)."""
    return action is Action.deactivate and target.status is Status.deactivated


def decide(action: Action, actor: Account, target: Account, active_admins: int) -> Account:
    """Return the target as it will be after `action`, or raise the rule that refuses it.

    The caller has already checked that `actor` is an active administrator.
    """
    if action in (Action.deactivate, Action.demote) and actor.id == target.id:
        raise CannotChangeSelf("Nobody can deactivate or demote their own account.")

    if action is Action.approve:
        _need(target.status is Status.pending, "Only a pending account can be approved.")
        return target.with_(status=Status.active)
    if is_repeat_deactivation(action, target):
        return target  # Realises UC-A4 AC-77: nothing changes, only Keycloak is told again
    if action is Action.deactivate:
        _need(target.status is Status.active, "Only an active account can be deactivated.")
        _keep_an_administrator(target, active_admins)
        return target.with_(status=Status.deactivated)
    if action is Action.reinstate:
        _need(target.status is Status.deactivated, "Only a deactivated account can be reinstated.")
        return target.with_(status=Status.active)
    if action is Action.promote:
        _need(target.status is Status.active, "Only an active account can be promoted.")
        _need(target.role is Role.user, "That account is already an administrator.")
        return target.with_(role=Role.administrator)
    if action is Action.demote:
        _need(target.role is Role.administrator, "That account is not an administrator.")
        _keep_an_administrator(target, active_admins)
        return target.with_(role=Role.user)
    raise InvalidTransition(f"Unknown action {action}")


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise InvalidTransition(message)


def _keep_an_administrator(target: Account, active_admins: int) -> None:
    if target.is_active_administrator and active_admins <= 1:
        raise LastAdministrator("There must always be at least one active administrator.")
