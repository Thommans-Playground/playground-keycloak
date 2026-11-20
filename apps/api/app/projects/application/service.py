"""Use cases of the Projects context."""

from collections.abc import Iterable

from app.projects.application.ports import ProjectRepository
from app.projects.domain.caller import Caller
from app.projects.domain.errors import NotAnAdministrator
from app.projects.domain.project import Project


class ProjectsService:
    def __init__(self, projects: ProjectRepository):
        self._projects = projects

    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> Project:
        """Create a project with its first members (AC-9, AC-10). Only an administrator may, and that is checked
        before the input is (AC-11, AC-32). The checks of the input come in later slices."""
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")
        project = Project.create(caller, name, member_ids)
        self._projects.add(project)
        return project
