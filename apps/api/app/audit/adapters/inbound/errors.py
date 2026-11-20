"""How HTTP answers Audit's refusal: the same 403 body the web reads for every other refusal (detail.code)."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.audit.domain.errors import AuditError, NotAnAdministrator

HTTP_STATUS: dict[type[AuditError], int] = {NotAnAdministrator: 403}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuditError)
    async def audit_error(_: Request, exc: AuditError):
        return JSONResponse(
            {"detail": {"code": exc.code, "message": exc.message}},
            status_code=HTTP_STATUS.get(type(exc), 400),
        )
