"""The Projects routes. Composition hands in how to get a ProjectsService and how to turn the signed-in person
(after the Access guard chain) into Projects' Caller. Who may create is decided by the use case, not here."""

from collections.abc import Callable

from fastapi import APIRouter, Depends

from app.projects.adapters.inbound.schemas import CreateProjectIn, ProjectOut
from app.projects.application.service import ProjectsService
from app.projects.domain.caller import Caller


def build_router(
    service_dependency: Callable[..., ProjectsService], caller_dependency: Callable[..., Caller]
) -> APIRouter:
    router = APIRouter()

    @router.post("/projects", status_code=201, response_model=ProjectOut)
    def create_project(
        body: CreateProjectIn,
        who: Caller = Depends(caller_dependency),
        svc: ProjectsService = Depends(service_dependency),
    ):
        return ProjectOut.of(svc.create(who, body.name, body.members))

    return router
