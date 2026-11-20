"""Use cases of the Projects context."""

from collections.abc import Iterable

from app.projects.application.ports import ProjectRepository
from app.projects.domain.caller import Caller
from app.projects.domain.project import Project


class ProjectsService:
    def __init__(self, projects: ProjectRepository):
        self._projects = projects

    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> Project:
        """Create a project with its first members (AC-9, AC-10). The checks come in later slices."""
        project = Project.create(caller, name, member_ids)
        self._projects.add(project)
        return project
