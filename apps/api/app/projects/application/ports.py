from dataclasses import dataclass
from typing import Protocol

from app.projects.domain.project import Membership, Project


@dataclass(frozen=True)
class ProjectEvent:
    """What happened to a project, in Projects' words: ids only, the names are looked up when it is written."""

    action: str  # create_project, add_member or remove_member
    actor_id: str
    project_id: str
    project_name: str
    member_ids: tuple[str, ...] = ()  # the first members, each once, or the one member of a change
    reason: str | None = None  # none for a creation


class AccountStatus(Protocol):
    def active_among(self, ids: set[str]) -> set[str]:
        """Of these account ids, the ones whose people may be members."""
        ...


class People(Protocol):
    def names_of(self, ids: list[str]) -> dict[str, tuple[str, str]]:
        """For each known id, (name, email) as they are now. Unknown ids are left out."""
        ...


class AuditLog(Protocol):
    def record(self, event: ProjectEvent) -> None:
        """Write one entry in the trail, in the request's own transaction."""
        ...


class SecurityLog(Protocol):
    """Where Projects says that it refused a request, for the operators (ADR 0013). Never an audit entry."""

    def event(
        self,
        name: str,
        result: str,
        person_id: str | None = None,
        session_id: str | None = None,
        reason: str | None = None,
    ) -> None: ...


class ProjectRepository(Protocol):
    def add(self, project: Project) -> None: ...
    def by_id(self, project_id: str) -> Project | None: ...
    def add_member(self, project_id: str, membership: Membership) -> bool:
        """Write one membership. False if the person was already in (also when another request got there first):
        nothing of ours was written."""
        ...

    def remove_member(self, project_id: str, account_id: str) -> bool:
        """Delete one membership. False if there was none."""
        ...

    def list_all(self) -> list[Project]: ...
    def list_for_member(self, account_id: str) -> list[Project]: ...
