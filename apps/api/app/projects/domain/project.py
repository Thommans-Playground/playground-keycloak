"""The Project aggregate and the Membership inside it (BC-PROJECTS, OBJ-P1, OBJ-P2). Pure: standard library only."""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass

from app.projects.domain.caller import Caller
from app.projects.domain.errors import InvalidRequest
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
