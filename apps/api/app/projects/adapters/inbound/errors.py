"""How HTTP answers Projects' refusals: the same body the web reads for every other refusal (detail.code).
Later slices add their error and its status to HTTP_STATUS."""

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.projects.domain.errors import InvalidProjectName, InvalidRequest, NotAnAdministrator, ProjectsError

HTTP_STATUS: dict[type[ProjectsError], int] = {NotAnAdministrator: 403, InvalidProjectName: 422, InvalidRequest: 422}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProjectsError)
    async def projects_error(request: Request, exc: ProjectsError):
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
        return JSONResponse({"detail": {"code": error.code, "message": error.message}}, status_code=422)
