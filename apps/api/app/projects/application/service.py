"""Use cases of the Projects context."""

from collections.abc import Iterable

from app.projects.application.ports import ProjectRepository
from app.projects.domain.caller import Caller
from app.projects.domain.errors import NotAnAdministrator
from app.projects.domain.project import Project


class ProjectsService:
    def __init__(self, projects: ProjectRepository):
        self._projects = projects

    @staticmethod
    def authorise_creation(caller: Caller) -> None:
        """Only an administrator creates a project. The route calls it before it reads the body (AC-11, AC-93)."""
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")

    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> Project:
        """Create a project with its first members (AC-9, AC-10). Only an administrator may, and that is checked
        before the input is (AC-11, AC-32); then the name and the cap on first members are (AC-12, AC-91, AC-92)."""
        self.authorise_creation(caller)
        project = Project.create(caller, name, member_ids)
        self._projects.add(project)
        return project
