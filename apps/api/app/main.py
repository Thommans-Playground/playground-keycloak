from contextlib import asynccontextmanager
from datetime import datetime
from typing import Iterator

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters.keycloak_admin import KeycloakAdmin
from app.adapters.sql import Base, SqlAccounts, SqlAudit
from app.auth import InvalidToken, Principal, TokenVerifier
from app.config import Settings, get_settings
from app.domain.account import Account, Action, DomainError, Role, Status
from app.service import AccessService


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


class ReasonIn(BaseModel):
    reason: str | None = None


def create_app(settings: Settings | None = None, verifier: TokenVerifier | None = None,
               idp=None, engine=None) -> FastAPI:
    settings = settings or get_settings()
    if engine is None:
        kwargs = {"connect_args": {"check_same_thread": False}} if settings.database_url.startswith("sqlite") else {}
        engine = create_engine(settings.database_url, **kwargs)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(engine, expire_on_commit=False)
    verifier = verifier or TokenVerifier.from_jwks(settings.issuer, settings.api_audience, settings.internal_realm_url)
    idp = idp or KeycloakAdmin(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    app = FastAPI(title="Playground API", lifespan=lifespan)

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse({"code": exc.code, "message": exc.message}, status_code=exc.http_status)

    def db() -> Iterator[Session]:
        with sessions() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def service(session: Session = Depends(db)) -> AccessService:
        return AccessService(SqlAccounts(session), SqlAudit(session), idp, settings.bootstrap_admins)

    def principal(authorization: str | None = Header(default=None)) -> Principal:
        scheme, _, token = (authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(401, {"code": "missing_token", "message": "Sign in first."},
                                headers={"WWW-Authenticate": "Bearer"})
        try:
            return verifier.verify(token)
        except InvalidToken:
            raise HTTPException(401, {"code": "invalid_token", "message": "The token is not valid."},
                                headers={"WWW-Authenticate": "Bearer"})

    def any_account(p: Principal = Depends(principal), svc: AccessService = Depends(service)) -> Account:
        """The caller's account, made on first sight, whatever its status."""
        return svc.account_for(p.identity, p.name, p.email, p.email_verified)

    def not_deactivated(a: Account = Depends(any_account)) -> Account:
        if a.status is Status.deactivated:
            raise HTTPException(403, {"code": "account_deactivated", "message": "Your account is deactivated."})
        return a

    def active_account(a: Account = Depends(not_deactivated)) -> Account:
        if a.status is Status.pending:
            raise HTTPException(403, {"code": "account_pending", "message": "Your account is waiting for approval."})
        return a

    def administrator(a: Account = Depends(active_account)) -> Account:
        if a.role is not Role.administrator:
            raise HTTPException(403, {"code": "forbidden", "message": "Administrators only."})
        return a

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/me", response_model=AccountOut)
    def me(a: Account = Depends(not_deactivated)):
        # A pending person sees only this (FR-2).
        return AccountOut.of(a)

    @app.get("/accounts", response_model=list[AccountOut])
    def accounts(status: Status | None = None, _: Account = Depends(administrator),
                 svc: AccessService = Depends(service)):
        return [AccountOut.of(a) for a in svc.accounts.list(status.value if status else None)]

    def _change(action: Action):
        def endpoint(account_id: str, body: ReasonIn | None = None, actor: Account = Depends(administrator),
                     svc: AccessService = Depends(service)):
            return AccountOut.of(svc.change(actor, account_id, action, body.reason if body else None))
        return endpoint

    for action in Action:
        app.add_api_route(f"/accounts/{{account_id}}/{action.value}", _change(action), methods=["POST"],
                          response_model=AccountOut, name=action.value)

    @app.get("/audit")
    def audit(_: Account = Depends(administrator), svc: AccessService = Depends(service)):
        return svc.audit.entries()

    return app
