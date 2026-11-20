"""What goes over HTTP for a project. The lists files, endpoints and evaluations are empty placeholders (decision 23)."""

from pydantic import BaseModel, ConfigDict

from app.projects.application.view import ProjectView


class CreateProjectIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # mass assignment: an unknown field is refused, not ignored (AC-93)

    name: str
    members: list[str] = []  # the first members, as account ids


class AddMemberIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # an unknown field is refused, not ignored (AC-93)

    account_id: str


class MemberOut(BaseModel):
    id: str
    name: str | None  # None when Access does not know the id: the page then shows the id (ADR 0016)


class ProjectOut(BaseModel):
    id: str
    name: str
    created_by: str
    members: list[MemberOut]
    files: list[str] = []
    endpoints: list[str] = []
    evaluations: list[str] = []

    @classmethod
    def of(cls, v: ProjectView) -> "ProjectOut":
        members = [MemberOut(id=i, name=n) for i, n in sorted(v.names.items())]
        return cls(id=v.id, name=v.name, created_by=v.created_by, members=members)
