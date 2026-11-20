"""Use cases of the Projects context."""

from collections.abc import Iterable

from app.projects.application.ports import AccountStatus, AuditLog, ProjectEvent, ProjectRepository
from app.projects.domain.caller import Caller
from app.projects.domain.errors import MemberNotEligible, NotAnAdministrator
from app.projects.domain.project import Project


class ProjectsService:
    def __init__(self, projects: ProjectRepository, accounts: AccountStatus, audit: AuditLog):
        self._projects = projects
        self._accounts = accounts
        self._audit = audit

    @staticmethod
    def authorise_creation(caller: Caller) -> None:
        """Only an administrator creates a project. The route calls it before it reads the body (AC-11, AC-93)."""
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")

    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> Project:
        """Create a project with its first members (AC-9, AC-10). Only an administrator may, and that is checked
        before the input is (AC-11, AC-32); then the name and the cap on first members are (AC-12, AC-91, AC-92); then that every person named has an
        active account (AC-13), each counted once (AC-89). The audit entry is written after saving, in the request's own
        transaction, and only when the project was created (AC-29)."""
        self.authorise_creation(caller)
        project = Project.create(caller, name, member_ids)
        named = set(project.members)  # each person once (AC-89)
        if named and not named <= self._accounts.active_among(named):
            raise MemberNotEligible  # pending, deactivated or unknown: one answer (AC-13)
        self._projects.add(project)
        self._audit.record(
            ProjectEvent(
                "create_project",
                caller.account_id,
                project.id,
                project.name,
                tuple(m.account_id for m in project.memberships),
            )
        )
        return project
