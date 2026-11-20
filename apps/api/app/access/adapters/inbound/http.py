"""The Access routes. Translates HTTP into use cases of AccessService and back (inbound adapter).

The guards below turn a token into the caller's account and refuse by status and role. The composition root hands in
the two things this module must not build itself: how to get an AccessService, and the token verifier.
"""

from collections.abc import Callable

from fastapi import APIRouter, Depends, Header, HTTPException

from app.access.adapters.inbound.schemas import (
    AccountOut,
    ChangedOut,
    ListedAccountOut,
    ReasonIn,
)
from app.access.application.ports import InvalidToken, Principal, TokenVerifier
from app.access.application.service import AccessService
from app.access.domain.account import Account, Action, Role, Status


def build_router(
    service: Callable[..., AccessService], verifier: TokenVerifier
) -> APIRouter:
    router = APIRouter()

    def principal(authorization: str | None = Header(default=None)) -> Principal:
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(
                401,
                {"code": "missing_token", "message": "Sign in first."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            return verifier.verify(token)
        except InvalidToken:
            raise HTTPException(
                401,
                {"code": "invalid_token", "message": "The token is not valid."},
                headers={"WWW-Authenticate": "Bearer"},
            )

    def any_account(
        p: Principal = Depends(principal), svc: AccessService = Depends(service)
    ) -> Account:
        """The caller's account, made on first sight, whatever its status."""
        return svc.account_for(p.identity, p.name, p.email, p.email_verified)

    def not_deactivated(a: Account = Depends(any_account)) -> Account:
        if a.status is Status.deactivated:
            raise HTTPException(
                403,
                {
                    "code": "account_deactivated",
                    "message": "Your account is deactivated.",
                },
            )
        return a

    def active_account(a: Account = Depends(not_deactivated)) -> Account:
        if a.status is Status.pending:
            raise HTTPException(
                403,
                {
                    "code": "account_pending",
                    "message": "Your account is waiting for approval.",
                },
            )
        return a

    def administrator(a: Account = Depends(active_account)) -> Account:
        if a.role is not Role.administrator:
            raise HTTPException(
                403, {"code": "forbidden", "message": "Administrators only."}
            )
        return a

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
        return [
            ListedAccountOut.listed(a, d)
            for a, d in svc.list_accounts(status.value if status else None)
        ]

    def _change(action: Action):
        def endpoint(
            account_id: str,
            body: ReasonIn | None = None,
            actor: Account = Depends(administrator),
            svc: AccessService = Depends(service),
        ):
            result = svc.change(
                actor, account_id, action, body.reason if body else None
            )
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

    @router.get("/audit")
    def audit(
        _: Account = Depends(administrator), svc: AccessService = Depends(service)
    ):
        return svc.audit.entries()

    return router
