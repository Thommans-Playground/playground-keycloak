from typing import Protocol

from app.projects.domain.project import Project


class ProjectRepository(Protocol):
    def add(self, project: Project) -> None: ...
    def by_id(self, project_id: str) -> Project | None: ...
