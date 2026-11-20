"""What the trail keeps: an entry, and the people in it as they were when it happened (BC-AUDIT, OBJ-L1).

Pure: standard library only. There is no time here: the database sets it when the entry is stored (RULE-L2).
"""

from dataclasses import dataclass
from enum import StrEnum


class Kind(StrEnum):
    account = "account"
    project = "project"


@dataclass(frozen=True)
class Person:
    """An account or a project as it was named at that moment. Old entries have no name or email."""

    id: str
    name: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class AuditEntry:
    """One fact: who did what to which account or project, with whom involved, and why."""

    actor: Person | None  # nobody for a system action, such as a person's first request
    action: str
    kind: Kind
    target: Person
    details: tuple[Person, ...] = ()  # the people involved: a project's first members, or the member of a change
    reason: str | None = None
