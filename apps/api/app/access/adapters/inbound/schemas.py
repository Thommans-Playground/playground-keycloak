"""What goes over HTTP: request and response models. They are not the domain objects."""

from datetime import datetime

from pydantic import BaseModel

from app.access.domain.account import Account, Role, Status


class AccountOut(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    status: Status
    created: datetime
    created_by: str | None

    @classmethod
    def of(cls, a: Account) -> "AccountOut":
        return cls(**{f: getattr(a, f) for f in cls.model_fields})


class ChangedOut(AccountOut):
    keycloak_updated: bool | None = None  # only a deactivation reports it (AC-58)


class DuplicateOut(BaseModel):
    id: str
    name: str
    status: Status


class ListedAccountOut(AccountOut):
    """An account as the administrator's list shows it: with the other accounts that share its email (AC-73)."""

    duplicate_of: list[DuplicateOut] = []

    @classmethod
    def listed(cls, a: Account, duplicates: list[Account]) -> "ListedAccountOut":
        return cls(
            **AccountOut.of(a).model_dump(),
            duplicate_of=[DuplicateOut(id=d.id, name=d.name, status=d.status) for d in duplicates],
        )


class ReasonIn(BaseModel):
    reason: str | None = None
