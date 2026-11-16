"""The Account and its rules. No framework, database or HTTP in here (BC-ACCESS)."""

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
    code = "domain_error"
    http_status = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ReasonRequired(DomainError):  # RULE-A3
    code = "reason_required"
    http_status = 422


class CannotChangeSelf(DomainError):  # RULE-A2
    code = "cannot_change_self"
    http_status = 403


class LastAdministrator(DomainError):  # RULE-A1
    code = "last_administrator"
    http_status = 409


class InvalidTransition(DomainError):
    code = "invalid_transition"
    http_status = 409


class AccountNotFound(DomainError):
    code = "account_not_found"
    http_status = 404


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
    def is_active_administrator(self) -> bool:
        return self.status is Status.active and self.role is Role.administrator

    def with_(self, **changes) -> "Account":
        return replace(self, **changes)


REASON_ACTIONS = {Action.deactivate, Action.reinstate, Action.promote, Action.demote}


def clean_reason(reason: str | None) -> str:
    """A reason must say something: at least three letters. Empty or noise is refused."""
    text = (reason or "").strip()
    if sum(c.isalpha() for c in text) < 3:
        raise ReasonRequired("A reason that says something is required.")
    return text


def decide(action: Action, actor: Account, target: Account, active_admins: int) -> Account:
    """Return the target as it will be after `action`, or raise the rule that refuses it.

    The caller has already checked that `actor` is an active administrator.
    """
    if action in (Action.deactivate, Action.demote) and actor.id == target.id:
        raise CannotChangeSelf("Nobody can deactivate or demote their own account.")

    if action is Action.approve:
        _need(target.status is Status.pending, "Only a pending account can be approved.")
        return target.with_(status=Status.active)
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
