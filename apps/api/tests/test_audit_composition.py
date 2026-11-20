"""The bridge and the caller translation live in composition/, the one place that knows both contexts (D4, D7)."""

from datetime import datetime

import pytest

from app.access.application.ports import AccountEvent, AccountRef
from app.access.domain.account import Account, Role, Status
from app.audit.application.service import AuditService
from app.audit.domain.caller import Caller
from app.audit.domain.entry import Kind, Person
from app.composition.bridges import AccessAuditBridge, audit_caller
from tests.fakes import FakeAuditEntries


def account(role=Role.user, status=Status.active):
    return Account("acc-1", "sub-1", "Ada", "ada@x.test", role, status, datetime(2026, 1, 1), None)


@pytest.mark.ac("AC-56")
def test_the_bridge_turns_an_access_event_into_an_account_entry_with_the_names():
    port = FakeAuditEntries()
    AccessAuditBridge(AuditService(port)).record(
        AccountEvent(AccountRef("a", "Ada", "ada@x.test"), "deactivate", AccountRef("m", "Maya", "maya@x.test"), "left")
    )
    (stored,) = port.stored
    e = stored.entry
    assert e.kind is Kind.account and e.action == "deactivate" and e.reason == "left" and e.details == ()
    assert e.actor == Person("a", "Ada", "ada@x.test") and e.target == Person("m", "Maya", "maya@x.test")


def test_the_bridge_passes_no_actor_for_a_registration():
    port = FakeAuditEntries()
    AccessAuditBridge(AuditService(port)).record(
        AccountEvent(None, "register", AccountRef("m", "Maya", "m@x.test"), None)
    )
    assert port.stored[0].entry.actor is None


@pytest.mark.ac("AC-68")
def test_the_guards_account_becomes_audits_caller():
    assert audit_caller(account(Role.administrator)) == Caller("acc-1", is_administrator=True)
    assert audit_caller(account(Role.user)) == Caller("acc-1", is_administrator=False)
