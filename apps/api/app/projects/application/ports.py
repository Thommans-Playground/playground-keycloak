from dataclasses import dataclass
from typing import Protocol

from app.projects.domain.project import Project


@dataclass(frozen=True)
class ProjectEvent:
    """What happened to a project, in Projects' words: ids only, the names are looked up when it is written."""

    action: str  # create_project
    actor_id: str
    project_id: str
    project_name: str
    member_ids: tuple[str, ...] = ()  # the first members, each once
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
