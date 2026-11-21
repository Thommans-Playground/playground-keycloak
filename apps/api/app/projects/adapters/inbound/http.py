"""The Projects routes. Composition hands in how to get a ProjectsService and how to turn the signed-in person
(after the Access guard chain) into Projects' Caller. Who may create is decided by the use case, not here."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Body, Depends
from pydantic import ValidationError

from app.projects.adapters.inbound.schemas import AddMemberIn, CreateProjectIn, ProjectOut
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

    @router.get("/projects", response_model=list[ProjectOut])
    def list_projects(who: Caller = Depends(caller_dependency), svc: ProjectsService = Depends(service_dependency)):
        return [ProjectOut.of(p) for p in svc.list_projects(who)]

    @router.get("/projects/{project_id}", response_model=ProjectOut)
    def open_project(
        project_id: str, who: Caller = Depends(caller_dependency), svc: ProjectsService = Depends(service_dependency)
    ):
        return ProjectOut.of(svc.open_project(who, project_id))

    @router.post("/projects/{project_id}/members", response_model=ProjectOut)
    def add_member(
        project_id: str,
        raw: dict[str, Any] = Body(),
        who: Caller = Depends(caller_dependency),
        svc: ProjectsService = Depends(service_dependency),
    ):
        svc.authorise_member_change(who, project_id)  # the project, then the role, then the input (AC-84, AC-60, AC-93)
        try:
            body = AddMemberIn.model_validate(raw)
        except ValidationError:  # no detail: it would echo the input
            raise InvalidRequest("The request is not valid.") from None
        return ProjectOut.of(svc.add_member(who, project_id, body.account_id))

    @router.delete("/projects/{project_id}/members/{account_id}", response_model=ProjectOut)
    def remove_member(
        project_id: str,
        account_id: str,
        who: Caller = Depends(caller_dependency),
        svc: ProjectsService = Depends(service_dependency),
    ):
        return ProjectOut.of(svc.remove_member(who, project_id, account_id))

    return router
