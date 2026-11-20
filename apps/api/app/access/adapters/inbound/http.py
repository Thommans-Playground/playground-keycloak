"""The Access routes. Translates HTTP into use cases of AccessService and back (inbound adapter).

The guards below turn a token into the caller's account and refuse by status and role. The composition root hands in
the two things this module must not build itself: how to get an AccessService, and the token verifier.
"""

from collections.abc import Callable
from dataclasses import dataclass

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.access.adapters.inbound.schemas import (
    AccountOut,
    ChangedOut,
    ListedAccountOut,
    ReasonIn,
)
from app.access.application.ports import InvalidToken, Principal, SecurityLog, TokenVerifier
from app.access.application.service import AccessService
from app.access.domain.account import Account, Action, Role, Status


@dataclass(frozen=True)
class Guards:
    """The guard chain as dependencies, so composition can hand the same chain to another context's routes."""

    any_account: Callable[..., Account]
    not_deactivated: Callable[..., Account]
    active_account: Callable[..., Account]
    administrator: Callable[..., Account]


def build_guards(service: Callable[..., AccessService], verifier: TokenVerifier, security_log: SecurityLog) -> Guards:
    def refuse(status: int, code: str, message: str, person_id: str | None = None, **kw) -> HTTPException:
        """The one place a guard refuses: it writes one line to the security log, then returns the error to raise."""
        security_log.event("request_refused", "refused", person_id=person_id, reason=code)
        return HTTPException(status, {"code": code, "message": message}, **kw)

    def principal(authorization: str | None = Header(default=None)) -> Principal:
        scheme, _, token = (authorization or "").partition(" ")
        bearer = {"headers": {"WWW-Authenticate": "Bearer"}}
        if scheme.lower() != "bearer" or not token:
            raise refuse(401, "missing_token", "Sign in first.", **bearer)
        try:
            return verifier.verify(token)
        except InvalidToken:
            raise refuse(401, "invalid_token", "The token is not valid.", **bearer) from None

    def any_account(
        request: Request, p: Principal = Depends(principal), svc: AccessService = Depends(service)
    ) -> Account:
        """The caller's account, made on first sight, whatever its status."""
        account = svc.account_for(p.identity, p.name, p.email, p.email_verified)
        request.state.person_id = account.id  # so a later refusal, in any context, is logged with who it was
        return account

    def not_deactivated(a: Account = Depends(any_account)) -> Account:
        if a.status is Status.deactivated:
            raise refuse(403, "account_deactivated", "Your account is deactivated.", a.id)
        return a

    def active_account(a: Account = Depends(not_deactivated)) -> Account:
        if a.status is Status.pending:
            raise refuse(403, "account_pending", "Your account is waiting for approval.", a.id)
        return a

    def administrator(a: Account = Depends(active_account)) -> Account:
        if a.role is not Role.administrator:
            raise refuse(403, "forbidden", "Administrators only.", a.id)
        return a

    return Guards(any_account, not_deactivated, active_account, administrator)


def build_router(service: Callable[..., AccessService], guards: Guards) -> APIRouter:
    router = APIRouter()
    not_deactivated, administrator = guards.not_deactivated, guards.administrator

    @router.get("/health")
    def health():
        return {"status": "ok"}

    @router.get("/me", response_model=AccountOut)
    def me(a: Account = Depends(not_deactivated)):
        # A pending person sees only this (FR-3).
        return AccountOut.of(a)

    @router.get("/accounts", response_model=list[ListedAccountOut])
    def accounts(
        status: Status | None = None,
        _: Account = Depends(administrator),
        svc: AccessService = Depends(service),
    ):
        return [ListedAccountOut.listed(a, d) for a, d in svc.list_accounts(status.value if status else None)]

    def _change(action: Action):
        def endpoint(
            account_id: str,
            body: ReasonIn | None = None,
            actor: Account = Depends(administrator),
            svc: AccessService = Depends(service),
        ):
            result = svc.change(actor, account_id, action, body.reason if body else None)
            out = AccountOut.of(result.account).model_dump()
            if action is Action.deactivate:
                out["keycloak_updated"] = result.keycloak_updated
            return out

        return endpoint

    for action in Action:
        router.add_api_route(
            f"/accounts/{{account_id}}/{action.value}",
            _change(action),
            methods=["POST"],
            response_model=ChangedOut,
            response_model_exclude_none=True,
            name=action.value,
        )

    return router
