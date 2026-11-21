"""The Project aggregate and the Membership inside it (BC-PROJECTS, OBJ-P1, OBJ-P2). Pure: standard library only."""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass, replace

from app.projects.domain.caller import Caller
from app.projects.domain.errors import InvalidRequest, MemberNotEligible
from app.projects.domain.name import clean_name

MAX_FIRST_MEMBERS = 50


@dataclass(frozen=True)
class Membership:
    account_id: str
    added_by: str


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    created_by: str
    memberships: tuple[Membership, ...] = ()

    @property
    def members(self) -> frozenset[str]:
        return frozenset(m.account_id for m in self.memberships)

    @classmethod
    def create(cls, caller: Caller, name: str, member_ids: Iterable[str]) -> "Project":
        """A new project. Its id is random, so it reveals nothing about count or order (ADR 0015). Only the people
        named are members: the creator is one only if named (AC-10). The name is trimmed and checked (AC-12, AC-91);
        at most 50 distinct first members (AC-92)."""
        name = clean_name(name)
        ids = tuple(dict.fromkeys(member_ids))
        if len(ids) > MAX_FIRST_MEMBERS:
            raise InvalidRequest(f"A project starts with at most {MAX_FIRST_MEMBERS} members.")
        memberships = tuple(Membership(i, added_by=caller.account_id) for i in ids)
        return cls(str(uuid.uuid4()), name, caller.account_id, memberships)

    def add_member(self, caller: Caller, account_id: str) -> tuple["Project", bool]:
        """The project with one more member, and whether anything changed. A person already in is no change (AC-88),
        so the adapter writes no row and the use case no entry."""
        if account_id in self.members:
            return self, False
        return replace(self, memberships=(*self.memberships, Membership(account_id, added_by=caller.account_id))), True

    def remove_member(self, account_id: str) -> "Project":
        """The project without that member, possibly empty (AC-20). A person who is not a member is refused with the
        one Projects answer, and nothing is looked up in Access (AC-87, decision 23)."""
        if account_id not in self.members:
            raise MemberNotEligible
        return replace(self, memberships=tuple(m for m in self.memberships if m.account_id != account_id))


def is_well_formed(project_id: str) -> bool:
    """A project id is a UUID in its canonical form, as ids are made (ADR 0015). Anything else cannot exist."""
    try:
        return str(uuid.UUID(project_id)) == project_id
    except ValueError:
        return False


def can_see(caller: Caller, project: Project) -> bool:
    """RULE-P4: only the members and the administrators see inside a project."""
    return caller.is_administrator or caller.account_id in project.members
