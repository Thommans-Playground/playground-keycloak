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


# TSK-P1.7: the bridges that answer Projects' People and AuditLog ports


def access_with(*people):
    from app.access.application.service import AccessService
    from tests.fakes import FakeAccounts, FakeAudit, FakeIdp, FakeUnitOfWork

    accounts = FakeAccounts()
    for acc_id, name, email in people:
        accounts.add(
            Account(acc_id, f"sub-{acc_id}", name, email, Role.user, Status.active, datetime(2026, 1, 1), None)
        )
    return AccessService(accounts, FakeAudit(), FakeIdp(), set(), uow=FakeUnitOfWork())


@pytest.mark.ac("AC-29")
def test_the_people_bridge_answers_through_accesss_people_and_leaves_out_the_unknown():
    from app.composition.bridges import PeopleBridge

    bridge = PeopleBridge(access_with(("a", "Ada", "ada@x.test"), ("m", "Maya", "maya@x.test")))
    assert bridge.names_of(["a", "m", "ghost"]) == {"a": ("Ada", "ada@x.test"), "m": ("Maya", "maya@x.test")}
    assert bridge.names_of([]) == {}


@pytest.mark.ac("AC-29")
def test_the_audit_bridge_turns_a_project_event_into_a_project_entry_with_the_names_now():
    from app.audit.application.service import AuditService
    from app.audit.domain.entry import Kind, Person
    from app.composition.bridges import ProjectsAuditBridge
    from app.projects.application.ports import ProjectEvent
    from tests.fakes import FakeAuditEntries, FakePeople

    port = FakeAuditEntries()
    people = FakePeople({"a": ("Ada", "ada@x.test"), "m": ("Maya", "maya@x.test")})
    ProjectsAuditBridge(AuditService(port), people).record(
        ProjectEvent("create_project", "a", "p-1", "Alpha", ("m", "a"))
    )
    (stored,) = port.stored
    e = stored.entry
    assert (e.kind, e.action, e.reason) == (Kind.project, "create_project", None)
    assert e.actor == Person("a", "Ada", "ada@x.test")
    assert e.target == Person("p-1", "Alpha", None)
    assert e.details == (Person("m", "Maya", "maya@x.test"), Person("a", "Ada", "ada@x.test"))
    assert people.asked == [{"a", "m"}]  # one question, for the actor and the members together


@pytest.mark.ac("AC-29")
def test_the_audit_bridge_keeps_an_id_it_has_no_name_for():
    from app.audit.application.service import AuditService
    from app.audit.domain.entry import Person
    from app.composition.bridges import ProjectsAuditBridge
    from app.projects.application.ports import ProjectEvent
    from tests.fakes import FakeAuditEntries, FakePeople

    port = FakeAuditEntries()
    ProjectsAuditBridge(AuditService(port), FakePeople()).record(
        ProjectEvent("create_project", "a", "p", "Alpha", ("m",))
    )
    e = port.stored[0].entry
    assert (e.actor, e.details) == (Person("a"), (Person("m"),))
