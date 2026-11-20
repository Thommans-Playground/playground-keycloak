"""The Projects routes. Composition hands in how to get a ProjectsService and how to turn the signed-in person
(after the Access guard chain) into Projects' Caller. Who may create is decided by the use case, not here."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Body, Depends
from pydantic import ValidationError

from app.projects.adapters.inbound.schemas import CreateProjectIn, ProjectOut
from app.projects.application.service import ProjectsService
from app.projects.domain.caller import Caller
from app.projects.domain.errors import InvalidRequest


def build_router(
    service_dependency: Callable[..., ProjectsService], caller_dependency: Callable[..., Caller]
) -> APIRouter:
    router = APIRouter()

    @router.post("/projects", status_code=201, response_model=ProjectOut)
    def create_project(
        raw: dict[str, Any] = Body(),
        who: Caller = Depends(caller_dependency),
        svc: ProjectsService = Depends(service_dependency),
    ):
        svc.authorise_creation(who)  # the role first, then the input (AC-11, AC-93)
        try:
            body = CreateProjectIn.model_validate(raw)
        except ValidationError:  # no detail: it would echo the input
            raise InvalidRequest("The request is not valid.") from None
        return ProjectOut.of(svc.create(who, body.name, body.members))

    return router
