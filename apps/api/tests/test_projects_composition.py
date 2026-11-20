"""The Caller of Projects is made in composition/, the one place that knows both contexts (ADR 0002, 0015)."""

from datetime import datetime

import pytest

from app.access.domain.account import Account, Role, Status
from app.composition.bridges import projects_caller
from app.projects.domain.caller import Caller


def account(role=Role.user, status=Status.active):
    return Account("acc-1", "sub-1", "Ada", "ada@x.test", role, status, datetime(2026, 1, 1), None)


@pytest.mark.ac("AC-10")
def test_the_guards_account_becomes_projects_caller():
    assert projects_caller(account(Role.administrator)) == Caller("acc-1", is_administrator=True)
    assert projects_caller(account(Role.user)) == Caller("acc-1", is_administrator=False)


def test_a_deactivated_administrator_is_not_an_administrator_for_projects():
    assert projects_caller(account(Role.administrator, Status.deactivated)).is_administrator is False


@pytest.mark.ac("AC-13")
def test_the_account_status_bridge_answers_through_accesss_own_is_active_rule():
    from app.access.application.service import AccessService
    from app.composition.bridges import AccountStatusBridge
    from tests.fakes import FakeAccounts, FakeAudit, FakeIdp, FakeUnitOfWork

    accounts = FakeAccounts()
    for acc_id, status in (("a", Status.active), ("p", Status.pending), ("d", Status.deactivated)):
        accounts.add(
            Account(acc_id, f"sub-{acc_id}", acc_id, f"{acc_id}@x.test", Role.user, status, datetime(2026, 1, 1), None)
        )
    access = AccessService(accounts, FakeAudit(), FakeIdp(), set(), uow=FakeUnitOfWork())
    bridge = AccountStatusBridge(access)
    assert bridge.active_among({"a", "p", "d", "unknown"}) == {"a"}
    assert bridge.active_among(set()) == set()
    assert isinstance(bridge.active_among({"a"}), set)
