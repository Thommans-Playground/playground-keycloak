"""Two administrators change each other at the same moment, on a real PostgreSQL (ADR 0009, AC-62).

Skipped unless TEST_DATABASE_URL names a PostgreSQL database (always a *_test one). SQLite cannot lock rows.
"""

import os
import threading
from datetime import datetime

import pytest
from sqlalchemy.orm import sessionmaker

from app.access.adapters.outbound.sql import SqlAccounts, SqlUnitOfWork
from app.access.application.service import AccessService
from app.access.domain.account import Account, Action, LastAdministrator, Role, Status
from app.audit.adapters.outbound.sql import SqlAuditEntries
from app.audit.application.service import AuditService
from app.composition.bridges import AccessAuditBridge, ProjectsAuditBridge
from tests.conftest import make_engine

URL = os.environ.get("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not URL.startswith("postgresql"),
    reason="needs TEST_DATABASE_URL pointing at a PostgreSQL *_test database (SQLite cannot lock rows)",
)

NOW = datetime(2026, 11, 20, 9, 0, 0)


class MeetBeforeSaving(SqlAccounts):
    """Makes both threads decide before either one writes, so a missing lock shows. With the lock the second
    thread waits for the first, so the meeting gives up after a second instead of waiting forever."""

    barrier: threading.Barrier

    def save(self, a):
        try:
            self.barrier.wait(timeout=1)
        except threading.BrokenBarrierError:
            pass
        super().save(a)


@pytest.mark.ac("AC-62")
def test_two_administrators_demoting_each_other_at_once_leave_exactly_one():
    engine = make_engine()  # migrated by Alembic as the owner
    sessions = sessionmaker(engine, expire_on_commit=False)
    ids = {}
    with sessions() as s:
        for key in ("a", "b"):
            acc = Account(
                f"id-{key}",
                f"sub-{key}",
                key,
                f"{key}@x.test",
                Role.administrator,
                Status.active,
                NOW,
            )
            SqlAccounts(s).add(acc)
            ids[key] = acc.id
        s.commit()

    barrier = threading.Barrier(2)
    outcomes: dict[str, object] = {}

    def demote(actor_key: str, target_key: str):
        class Repo(MeetBeforeSaving):
            pass

        Repo.barrier = barrier
        with sessions() as s:
            repo = Repo(s)
            svc = AccessService(
                repo,
                AccessAuditBridge(AuditService(SqlAuditEntries(s))),
                None,
                set(),
                now=lambda: NOW,
                uow=SqlUnitOfWork(s),
            )
            actor = repo.by_id(ids[actor_key])
            try:
                svc.change(actor, ids[target_key], Action.demote, "stepping down")
                s.commit()  # the route's commit semantics
                outcomes[actor_key] = "done"
            except Exception as exc:  # noqa: BLE001 - asserted below
                s.rollback()
                outcomes[actor_key] = exc

    threads = [
        threading.Thread(target=demote, args=("a", "b")),
        threading.Thread(target=demote, args=("b", "a")),
    ]
    [t.start() for t in threads]
    [t.join(timeout=20) for t in threads]

    results = list(outcomes.values())
    assert sorted(type(r).__name__ for r in results) == ["LastAdministrator", "str"], results
    assert any(isinstance(r, LastAdministrator) for r in results)
    with sessions() as s:
        assert SqlAccounts(s).count_active_administrators() == 1
    engine.dispose()


@pytest.mark.ac("AC-90")
def test_two_administrators_adding_the_same_person_at_once_leave_one_membership_and_one_entry():
    from sqlalchemy import func, select

    from app.audit.adapters.outbound.sql import AuditRow
    from app.projects.adapters.outbound.sql import MembershipRow, SqlProjects
    from app.projects.application.service import ProjectsService
    from app.projects.domain.caller import Caller
    from app.projects.domain.project import Project
    from tests.fakes import FakeAccountStatus, FakePeople

    engine = make_engine()
    sessions = sessionmaker(engine, expire_on_commit=False)
    admins = [Caller("acc-ada", True), Caller("acc-bo", True)]
    with sessions() as s:
        project = Project.create(admins[0], "Alpha", [])
        SqlProjects(s).add(project)
        s.commit()

    barrier = threading.Barrier(2)
    outcomes: dict[str, object] = {}

    class MeetBeforeInserting(SqlProjects):
        """Both requests have read the project and decided before either one inserts, so the unique key decides."""

        def add_member(self, project_id, membership):
            try:
                barrier.wait(timeout=2)
            except threading.BrokenBarrierError:
                pass
            return super().add_member(project_id, membership)

    def add(caller: Caller):
        with sessions() as s:
            svc = ProjectsService(
                MeetBeforeInserting(s),
                FakeAccountStatus(),
                ProjectsAuditBridge(AuditService(SqlAuditEntries(s)), FakePeople()),
                FakePeople(),
            )
            try:
                got = svc.add_member(caller, project.id, "acc-maya")
                s.commit()
                outcomes[caller.account_id] = got.members
            except Exception as exc:  # noqa: BLE001 - asserted below
                s.rollback()
                outcomes[caller.account_id] = exc

    threads = [threading.Thread(target=add, args=(a,)) for a in admins]
    [t.start() for t in threads]
    [t.join(timeout=20) for t in threads]

    assert all(o == frozenset({"acc-maya"}) for o in outcomes.values()), outcomes  # neither call failed
    assert len(outcomes) == 2
    with sessions() as s:
        assert s.scalar(select(func.count()).select_from(MembershipRow)) == 1
        entries = s.scalars(select(AuditRow.action).where(AuditRow.kind == "project")).all()
    assert entries == ["add_member"]  # the loser wrote none
    engine.dispose()
