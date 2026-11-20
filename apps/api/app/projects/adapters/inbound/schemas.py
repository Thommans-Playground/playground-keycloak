"""What goes over HTTP for a project. The lists files, endpoints and evaluations are empty placeholders (decision 23)."""

from pydantic import BaseModel

from app.projects.domain.project import Project


class CreateProjectIn(BaseModel):
    name: str
    members: list[str] = []  # the first members, as account ids


class ProjectOut(BaseModel):
    id: str
    name: str
    created_by: str
    members: list[str]
    files: list[str] = []
    endpoints: list[str] = []
    evaluations: list[str] = []

    @classmethod
    def of(cls, p: Project) -> "ProjectOut":
        return cls(id=p.id, name=p.name, created_by=p.created_by, members=sorted(p.members))
