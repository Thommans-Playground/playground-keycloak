"""The Audit route: GET /audit. There is no other verb, so PUT, PATCH and DELETE find nothing (AC-79).

Composition hands in how to get an AuditService and how to turn the signed-in person into Audit's Caller.
Who may read is decided by AuditService.read, not here.
"""

from collections.abc import Callable

from fastapi import APIRouter, Depends

from app.audit.adapters.inbound.schemas import EntryOut
from app.audit.application.service import AuditService
from app.audit.domain.caller import Caller


def build_router(service: Callable[..., AuditService], caller: Callable[..., Caller]) -> APIRouter:
    router = APIRouter()

    @router.get("/audit", response_model=list[EntryOut])
    def audit(who: Caller = Depends(caller), svc: AuditService = Depends(service)):
        return [EntryOut.of(r) for r in svc.read(who)]

    return router
