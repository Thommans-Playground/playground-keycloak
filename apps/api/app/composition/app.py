"""The composition root: the one place that picks the adapters and wires them to the use cases (ADR 0001, 0010)."""

from collections.abc import Iterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.access.adapters.inbound.errors import register_error_handlers
from app.access.adapters.inbound.http import build_guards, build_router
from app.access.adapters.outbound.keycloak_admin import KeycloakAdmin
from app.access.adapters.outbound.sql import SqlAccounts, SqlUnitOfWork
from app.access.adapters.outbound.token_verifier import JwtTokenVerifier
from app.access.application.service import AccessService
from app.audit.adapters.inbound.errors import register_error_handlers as register_audit_error_handlers
from app.audit.adapters.inbound.http import build_router as build_audit_router
from app.audit.adapters.outbound.sql import SqlAuditEntries
from app.audit.application.service import AuditService
from app.composition.bridges import (
    AccessAuditBridge,
    AccountStatusBridge,
    PeopleBridge,
    ProjectsAuditBridge,
    audit_caller,
    projects_caller,
)
from app.infrastructure.config import Settings, get_settings
from app.infrastructure.role_check import check_start
from app.infrastructure.security_log import JsonStdoutSecurityLog
from app.projects.adapters.inbound.errors import register_error_handlers as register_projects_error_handlers
from app.projects.adapters.inbound.http import build_router as build_projects_router
from app.projects.adapters.outbound.sql import SqlProjects
from app.projects.application.service import ProjectsService


def create_app(
    settings: Settings | None = None,
    verifier: JwtTokenVerifier | None = None,
    idp=None,
    engine=None,
    security_log=None,
) -> FastAPI:
    settings = settings or get_settings()
    if engine is None:
        kwargs = {"connect_args": {"check_same_thread": False}} if settings.database_url.startswith("sqlite") else {}
        engine = create_engine(settings.database_url, **kwargs)
    check_start(engine)  # refuses to start with an unsafe role or the owner's URL in the environment (ADR 0011)
    sessions = sessionmaker(engine, expire_on_commit=False)
    verifier = verifier or JwtTokenVerifier.from_jwks(
        settings.issuer, settings.api_audience, settings.internal_realm_url
    )
    idp = idp or KeycloakAdmin(settings)
    security_log = security_log or JsonStdoutSecurityLog()  # stdout, then CloudWatch via the awslogs driver (ADR 0013)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    app = FastAPI(title="Playground API", lifespan=lifespan)
    register_error_handlers(app, security_log)
    register_audit_error_handlers(app, security_log)
    register_projects_error_handlers(app, security_log)

    def db() -> Iterator[Session]:
        with sessions() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    def audit_service(session: Session = Depends(db)) -> AuditService:
        return AuditService(SqlAuditEntries(session))  # the request's session: a change and its entry commit together

    def service(session: Session = Depends(db), audit: AuditService = Depends(audit_service)) -> AccessService:
        return AccessService(
            SqlAccounts(session),
            AccessAuditBridge(audit),
            idp,
            settings.bootstrap_admins,
            uow=SqlUnitOfWork(session),
        )

    guards = build_guards(service, verifier, security_log)

    def caller(account=Depends(guards.active_account)):
        return audit_caller(
            account
        )  # the guard chain refuses 401, pending and deactivated; Audit decides administrator

    def projects_service(
        session: Session = Depends(db),
        access: AccessService = Depends(service),
        audit: AuditService = Depends(audit_service),
    ) -> ProjectsService:
        # the request's session, so the project, its members and its audit entry commit together
        return ProjectsService(
            SqlProjects(session), AccountStatusBridge(access), ProjectsAuditBridge(audit, PeopleBridge(access))
        )

    def project_caller(account=Depends(guards.active_account)):
        return projects_caller(account)  # the same guard chain as every route: 401, pending and deactivated are refused

    app.include_router(build_router(service, guards))
    app.include_router(build_audit_router(audit_service, caller, security_log))
    app.include_router(build_projects_router(projects_service, project_caller))
    return app
