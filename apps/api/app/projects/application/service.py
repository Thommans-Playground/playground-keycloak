"""Use cases of the Projects context."""

from collections.abc import Iterable

from app.projects.application.ports import AccountStatus, AuditLog, People, ProjectEvent, ProjectRepository
from app.projects.application.view import ProjectView
from app.projects.domain.caller import Caller
from app.projects.domain.errors import MemberNotEligible, NotAnAdministrator, ProjectNotFound
from app.projects.domain.project import Membership, Project, can_see, is_well_formed


class ProjectsService:
    def __init__(self, projects: ProjectRepository, accounts: AccountStatus, audit: AuditLog, people: People):
        self._projects = projects
        self._accounts = accounts
        self._audit = audit
        self._people = people

    def _views(self, projects: list[Project]) -> list[ProjectView]:
        """The projects with the names of their members, from one lookup for all the members (no N+1). The names are
        as they are in Access, whatever the status of the account (ADR 0016)."""
        ids = sorted({i for p in projects for i in p.members})
        known = self._people.names_of(ids) if ids else {}
        return [ProjectView(p, {i: known[i][0] if i in known else None for i in sorted(p.members)}) for p in projects]

    def _view(self, project: Project) -> ProjectView:
        return self._views([project])[0]

    @staticmethod
    def authorise_creation(caller: Caller) -> None:
        """Only an administrator creates a project. The route calls it before it reads the body (AC-11, AC-93)."""
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")

    def create(self, caller: Caller, name: str, member_ids: Iterable[str]) -> ProjectView:
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
        return self._view(project)

    def list_projects(self, caller: Caller) -> list[ProjectView]:
        """The projects the caller may see: all for an administrator, their own otherwise, maybe none (AC-55, AC-86).
        A read: no audit entry (decision 22)."""
        if caller.is_administrator:
            return self._views(self._projects.list_all())
        return self._views(self._projects.list_for_member(caller.account_id))

    def open_project(self, caller: Caller, project_id: str) -> ProjectView:
        return self._view(self._visible(caller, project_id))

    def _visible(self, caller: Caller, project_id: str) -> Project:
        """The project, or ProjectNotFound for one that is missing, malformed or not the caller's to see: one answer
        (AC-26, AC-27, RULE-P4). An id that is not a UUID is not looked up at all."""
        project = self._projects.by_id(project_id) if is_well_formed(project_id) else None
        if project is None or not can_see(caller, project):
            raise ProjectNotFound
        return project

    def authorise_member_change(self, caller: Caller, project_id: str) -> Project:
        """The order of UC-P2 step 4: the project is looked at first, so a stranger gets the missing-project answer
        (AC-84, RULE-P4), then the role (AC-60). The route calls it before it reads the body (AC-93)."""
        project = self._visible(caller, project_id)
        if not caller.is_administrator:
            raise NotAnAdministrator("Administrators only.")
        return project

    def add_member(self, caller: Caller, project_id: str, account_id: str) -> ProjectView:
        """Add a person with an active account (AC-17, AC-18). One already in is no change: nothing is written and no
        entry (AC-88). A request that loses a race to the unique key is that case too (AC-90). The entry follows the
        row, in the request's own transaction, and only for a change that happened (AC-30)."""
        project = self.authorise_member_change(caller, project_id)
        if account_id not in self._accounts.active_among({account_id}):
            raise MemberNotEligible  # pending, deactivated or unknown: one answer (AC-18)
        updated, changed = project.add_member(caller, account_id)
        if not changed:
            return self._view(project)
        if not self._projects.add_member(project.id, Membership(account_id, added_by=caller.account_id)):
            return self._view(self._projects.by_id(project.id) or project)  # another request added them first
        self._audit.record(ProjectEvent("add_member", caller.account_id, project.id, project.name, (account_id,)))
        return self._view(updated)

    def remove_member(self, caller: Caller, project_id: str, account_id: str) -> ProjectView:
        """Remove a member, whatever the state of their account (AC-20). A person who is not a member is refused and
        nothing is written (AC-87)."""
        project = self.authorise_member_change(caller, project_id)
        updated = project.remove_member(account_id)
        if not self._projects.remove_member(project.id, account_id):
            raise MemberNotEligible  # removed by another request in the meantime
        self._audit.record(ProjectEvent("remove_member", caller.account_id, project.id, project.name, (account_id,)))
        return self._view(updated)
