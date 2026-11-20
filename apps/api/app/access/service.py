"""Use cases of the Access context. Ports in, domain rules applied, audit written."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.access.domain.account import (
    REASON_ACTIONS,
    Account,
    AccountNotFound,
    Action,
    DomainError,
    Status,
    clean_reason,
    decide,
    duplicates_by_email,
    is_repeat_deactivation,
    new_account,
)
from app.access.ports import AccountRepository, AuditLog, IdentityProvider, UnitOfWork


class IdentityProviderUnavailable(DomainError):
    code = "identity_provider_unavailable"


@dataclass(frozen=True)
class ChangeResult:
    account: Account
    keycloak_updated: bool = True


class AccessService:
    def __init__(
        self,
        accounts: AccountRepository,
        audit: AuditLog,
        idp: IdentityProvider,
        bootstrap_admins: set[str],
        now: Callable[[], datetime] = lambda: _utc_now(),
        *,
        uow: UnitOfWork,
    ):
        self.accounts, self.audit, self.idp, self.bootstrap_admins = (
            accounts,
            audit,
            idp,
            bootstrap_admins,
        )
        self.uow = uow
        self._now = now  # a clock that a test can fix

    def account_for(
        self, identity: str, name: str, email: str, email_verified: bool
    ) -> Account:
        """Find the person's account, or make one the first time they are seen (FR-3).

        Name and email are copied from the token each time. The link is the identity, never the email.
        """
        existing = self.accounts.by_identity(identity)
        if existing:
            if (existing.name, existing.email) != (name, email):
                existing = existing.with_(name=name, email=email)
                self.accounts.save(existing)
            return existing
        account = new_account(
            identity,
            name,
            email,
            email_verified,
            self.bootstrap_admins,
            self.accounts.count_active_administrators(),
            self._now,
        )
        self.accounts.add(account)
        self.audit.record(
            None,
            "register"
            if account.status is Status.pending
            else "create_bootstrap_admin",
            account.id,
            None,
            self._now(),
        )
        return account

    def list_accounts(
        self, status: str | None = None
    ) -> list[tuple[Account, list[Account]]]:
        """The accounts, each with the other accounts that share its email. The duplicates are found among all
        accounts, whatever the filter, so a deactivated twin still shows."""
        everyone = self.accounts.list()
        duplicates = duplicates_by_email(everyone)
        return [
            (a, duplicates[a.id])
            for a in everyone
            if status is None or a.status.value == status
        ]

    def change(
        self, actor: Account, target_id: str, action: Action, reason: str | None = None
    ) -> ChangeResult:
        target = self.accounts.by_id(target_id)
        if not target:
            raise AccountNotFound("No such account.")
        cleaned = clean_reason(reason) if action in REASON_ACTIONS else None
        updated = decide(
            action, actor, target, self.accounts.count_active_administrators()
        )

        if action is Action.deactivate:
            # Realises UC-A4 AC-58 (ADR 0009): commit the deactivation first, then call Keycloak, and report a failure.
            if not is_repeat_deactivation(action, target):
                self.accounts.save(updated)
            self.audit.record(
                actor.id, action.value, target.id, cleaned, self._now(), "done"
            )
            self.uow.commit()
            try:
                self.idp.disable_user(target.identity)
                self.idp.end_sessions(target.identity)
            except Exception:  # noqa: BLE001 - any adapter failure means "not updated"
                self.audit.set_outcome(target.id, action.value, "keycloak_not_updated")
                return ChangeResult(updated, keycloak_updated=False)
            return ChangeResult(updated)

        # Keycloak first. If it fails nothing changes on our side (BC-ACCESS question 6).
        try:
            if action is Action.reinstate:
                self.idp.enable_user(target.identity)
        except Exception as exc:
            raise IdentityProviderUnavailable(
                "Keycloak could not be reached. Nothing was changed."
            ) from exc

        self.accounts.save(updated)
        self.audit.record(actor.id, action.value, target.id, cleaned, self._now())
        return ChangeResult(updated)


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
