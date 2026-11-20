"""How HTTP answers Projects' refusals: the same body the web reads for every other refusal (detail.code).
Later slices add their error and its status to HTTP_STATUS."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.projects.domain.errors import NotAnAdministrator, ProjectsError

HTTP_STATUS: dict[type[ProjectsError], int] = {NotAnAdministrator: 403}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ProjectsError)
    async def projects_error(request: Request, exc: ProjectsError):
        return JSONResponse(
            {"detail": {"code": exc.code, "message": exc.message}},
            status_code=HTTP_STATUS.get(type(exc), 400),
        )
