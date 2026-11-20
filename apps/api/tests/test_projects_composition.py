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
