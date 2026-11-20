from collections.abc import Iterator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.access.adapters.keycloak_admin import KeycloakAdmin
from app.access.adapters.sql import Base, SqlAccounts, SqlAudit, SqlUnitOfWork
from app.access.domain.account import (
    Account,
    AccountNotFound,
    Action,
    CannotChangeSelf,
    DomainError,
    InvalidTransition,
    LastAdministrator,
    ReasonRequired,
    Role,
    Status,
)
from app.access.service import AccessService, IdentityProviderUnavailable
from app.auth import InvalidToken, Principal, TokenVerifier
from app.config import Settings, get_settings

# How HTTP answers each rule. The domain only says what went wrong, so this map lives at the web edge.
HTTP_STATUS: dict[type[DomainError], int] = {
    ReasonRequired: 422,
    CannotChangeSelf: 403,
    LastAdministrator: 409,
    InvalidTransition: 409,
    AccountNotFound: 404,
    IdentityProviderUnavailable: 502,
}


class AccountOut(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    status: Status
    created: datetime
    created_by: str | None

    @classmethod
    def of(cls, a: Account) -> "AccountOut":
        return cls(**{f: getattr(a, f) for f in cls.model_fields})


class ChangedOut(AccountOut):
    keycloak_updated: bool | None = None  # only a deactivation reports it (AC-58)


class DuplicateOut(BaseModel):
    id: str
    name: str
    status: Status


class ListedAccountOut(AccountOut):
    """An account as the administrator's list shows it: with the other accounts that share its email (AC-73)."""

    duplicate_of: list[DuplicateOut] = []

    @classmethod
    def listed(cls, a: Account, duplicates: list[Account]) -> "ListedAccountOut":
        return cls(
            **AccountOut.of(a).model_dump(),
            duplicate_of=[
                DuplicateOut(id=d.id, name=d.name, status=d.status) for d in duplicates
            ],
        )


class ReasonIn(BaseModel):
    reason: str | None = None


def create_app(
    settings: Settings | None = None,
    verifier: TokenVerifier | None = None,
    idp=None,
    engine=None,
) -> FastAPI:
    settings = settings or get_settings()
    if engine is None:
        kwargs = (
            {"connect_args": {"check_same_thread": False}}
            if settings.database_url.startswith("sqlite")
            else {}
        )
        engine = create_engine(settings.database_url, **kwargs)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    verifier = verifier or TokenVerifier.from_jwks(
        settings.issuer, settings.api_audience, settings.internal_realm_url
    )
    idp = idp or KeycloakAdmin(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    app = FastAPI(title="Playground API", lifespan=lifespan)

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse(
            {"code": exc.code, "message": exc.message},
            status_code=HTTP_STATUS.get(type(exc), 400),
        )

    def db() -> Iterator[Session]:
        with sessions() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def service(session: Session = Depends(db)) -> AccessService:
        return AccessService(
            SqlAccounts(session),
            SqlAudit(session),
            idp,
            settings.bootstrap_admins,
            uow=SqlUnitOfWork(session),
        )

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

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/me", response_model=AccountOut)
    def me(a: Account = Depends(not_deactivated)):
        # A pending person sees only this (FR-3).
        return AccountOut.of(a)

    @app.get("/accounts", response_model=list[ListedAccountOut])
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
        app.add_api_route(
            f"/accounts/{{account_id}}/{action.value}",
            _change(action),
            methods=["POST"],
            response_model=ChangedOut,
            response_model_exclude_none=True,
            name=action.value,
        )

    @app.get("/audit")
    def audit(
        _: Account = Depends(administrator), svc: AccessService = Depends(service)
    ):
        return svc.audit.entries()

    return app
