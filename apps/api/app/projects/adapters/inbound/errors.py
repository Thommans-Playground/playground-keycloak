"""How HTTP answers Projects' refusals: the same body the web reads for every other refusal (detail.code).
Later slices add their error and its status to HTTP_STATUS."""

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.projects.application.ports import SecurityLog
from app.projects.domain.errors import (
    InvalidProjectName,
    InvalidRequest,
    MemberNotEligible,
    NotAnAdministrator,
    ProjectNotFound,
    ProjectsError,
)

HTTP_STATUS: dict[type[ProjectsError], int] = {
    NotAnAdministrator: 403,
    InvalidProjectName: 422,
    InvalidRequest: 422,
    MemberNotEligible: 422,
    ProjectNotFound: 404,
}


def register_error_handlers(app: FastAPI, security_log: SecurityLog) -> None:
    def refused(request: Request, code: str) -> None:
        """One line for each refusal Projects answers: the code and who, never the name or an id from the body."""
        security_log.event(
            "request_refused", "refused", person_id=getattr(request.state, "person_id", None), reason=code
        )

    @app.exception_handler(ProjectsError)
    async def projects_error(request: Request, exc: ProjectsError):
        refused(request, exc.code)
        return JSONResponse(
            {"detail": {"code": exc.code, "message": exc.message}},
            status_code=HTTP_STATUS.get(type(exc), 400),
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        """A body that is not even a JSON object, on /projects only. FastAPI's own answer echoes the input."""
        if request.url.path != "/projects" and not request.url.path.startswith("/projects/"):
            return await request_validation_exception_handler(request, exc)
        error = InvalidRequest("The request is not valid.")
        refused(request, error.code)
        return JSONResponse({"detail": {"code": error.code, "message": error.message}}, status_code=422)
