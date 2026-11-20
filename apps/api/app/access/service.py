"""Use cases of the Access context. Ports in, domain rules applied, audit written."""

from datetime import datetime, timezone
from typing import Callable

from app.access.domain.account import (
    Account, AccountNotFound, Action, DomainError, REASON_ACTIONS, Status, clean_reason, decide, duplicates_by_email, new_account,
)
from app.access.ports import AccountRepository, AuditLog, IdentityProvider


class IdentityProviderUnavailable(DomainError):
    code = "identity_provider_unavailable"


class AccessService:
    def __init__(self, accounts: AccountRepository, audit: AuditLog, idp: IdentityProvider,
                 bootstrap_admins: set[str], now: Callable[[], datetime] = lambda: _utc_now()):
        self.accounts, self.audit, self.idp, self.bootstrap_admins = accounts, audit, idp, bootstrap_admins
        self._now = now  # a clock that a test can fix

    def account_for(self, identity: str, name: str, email: str, email_verified: bool) -> Account:
        """Find the person's account, or make one the first time they are seen (FR-3).

        Name and email are copied from the token each time. The link is the identity, never the email.
        """
        existing = self.accounts.by_identity(identity)
        if existing:
            if (existing.name, existing.email) != (name, email):
                existing = existing.with_(name=name, email=email)
                self.accounts.save(existing)
            return existing
        account = new_account(identity, name, email, email_verified, self.bootstrap_admins,
                               self.accounts.count_active_administrators(), self._now)
        self.accounts.add(account)
        self.audit.record(None, "register" if account.status is Status.pending else "create_bootstrap_admin", account.id, None, self._now())
        return account

    def list_accounts(self, status: str | None = None) -> list[tuple[Account, list[Account]]]:
        """The accounts, each with the other accounts that share its email. The duplicates are found among all
        accounts, whatever the filter, so a deactivated twin still shows."""
        everyone = self.accounts.list()
        duplicates = duplicates_by_email(everyone)
        return [(a, duplicates[a.id]) for a in everyone if status is None or a.status.value == status]

    def change(self, actor: Account, target_id: str, action: Action, reason: str | None = None) -> Account:
        target = self.accounts.by_id(target_id)
        if not target:
            raise AccountNotFound("No such account.")
        cleaned = clean_reason(reason) if action in REASON_ACTIONS else None
        updated = decide(action, actor, target, self.accounts.count_active_administrators())

        # Keycloak first. If it fails nothing changes on our side (BC-ACCESS question 6).
        try:
            if action is Action.deactivate:
                self.idp.disable_user(target.identity)
                self.idp.end_sessions(target.identity)
            elif action is Action.reinstate:
                self.idp.enable_user(target.identity)
        except Exception as exc:  # noqa: BLE001 - any adapter failure means "not done"
            raise IdentityProviderUnavailable("Keycloak could not be reached. Nothing was changed.") from exc

        self.accounts.save(updated)
        self.audit.record(actor.id, action.value, target.id, cleaned, self._now())
        return updated


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
