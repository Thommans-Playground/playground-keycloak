"""The composition root: the one place that picks the adapters and wires them to the use cases (ADR 0001, 0010)."""

from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.access.adapters.inbound.errors import register_error_handlers
from app.access.adapters.inbound.http import build_router
from app.access.adapters.outbound.keycloak_admin import KeycloakAdmin
from app.access.adapters.outbound.sql import SqlAccounts, SqlAudit, SqlUnitOfWork
from app.access.adapters.outbound.token_verifier import JwtTokenVerifier
from app.access.application.service import AccessService
from app.infrastructure.config import Settings, get_settings


def create_app(
    settings: Settings | None = None,
    verifier: JwtTokenVerifier | None = None,
    idp=None,
    engine=None,
) -> FastAPI:
    settings = settings or get_settings()
    if engine is None:
        kwargs = {"connect_args": {"check_same_thread": False}} if settings.database_url.startswith("sqlite") else {}
        engine = create_engine(settings.database_url, **kwargs)
    sessions = sessionmaker(engine, expire_on_commit=False)
    verifier = verifier or JwtTokenVerifier.from_jwks(settings.issuer, settings.api_audience, settings.internal_realm_url)
    idp = idp or KeycloakAdmin(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    app = FastAPI(title="Playground API", lifespan=lifespan)
    register_error_handlers(app)

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

    app.include_router(build_router(service, verifier))
    return app
