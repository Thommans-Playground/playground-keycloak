"""How HTTP answers each rule. The domain only says what went wrong, so the map lives at the web edge."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.access.application.service import IdentityProviderUnavailable
from app.access.domain.account import (
    AccountNotFound,
    CannotChangeSelf,
    DomainError,
    InvalidTransition,
    LastAdministrator,
    ReasonRequired,
)

HTTP_STATUS: dict[type[DomainError], int] = {
    ReasonRequired: 422,
    CannotChangeSelf: 403,
    LastAdministrator: 409,
    InvalidTransition: 409,
    AccountNotFound: 404,
    IdentityProviderUnavailable: 502,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse(
            {"code": exc.code, "message": exc.message},
            status_code=HTTP_STATUS.get(type(exc), 400),
        )
