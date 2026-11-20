"""How HTTP answers Audit's refusal: the same 403 body the web reads for every other refusal (detail.code)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.audit.application.ports import SecurityLog
from app.audit.domain.errors import AuditError, NotAnAdministrator

HTTP_STATUS: dict[type[AuditError], int] = {NotAnAdministrator: 403}


def register_error_handlers(app: FastAPI, security_log: SecurityLog) -> None:
    @app.exception_handler(AuditError)
    async def audit_error(request: Request, exc: AuditError):
        security_log.event(
            "request_refused", "refused", person_id=getattr(request.state, "person_id", None), reason=exc.code
        )
        return JSONResponse(
            {"detail": {"code": exc.code, "message": exc.message}},
            status_code=HTTP_STATUS.get(type(exc), 400),
        )
