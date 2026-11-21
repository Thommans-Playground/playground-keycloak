"""What the use cases answer: a project and the names of its members as they are now (ADR 0016). Not the domain."""

from dataclasses import dataclass

from app.projects.domain.project import Membership, Project


@dataclass(frozen=True)
class ProjectView:
    project: Project
    names: dict[str, str | None]  # member id -> name, or None when People does not know the id

    @property
    def id(self) -> str:
        return self.project.id

    @property
    def name(self) -> str:
        return self.project.name

    @property
    def created_by(self) -> str:
        return self.project.created_by

    @property
    def memberships(self) -> tuple[Membership, ...]:
        return self.project.memberships

    @property
    def members(self) -> frozenset[str]:
        return self.project.members
