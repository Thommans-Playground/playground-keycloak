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
from app.composition.bridges import AccessAuditBridge
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
