"""The use cases of Audit, tested with an in-memory port: no database, no HTTP (UC-L1, D2, D3, D4, D5)."""

import dataclasses
import inspect

import pytest

from app.audit.application.ports import AuditEntries
from app.audit.application.service import AuditService
from app.audit.domain.caller import Caller
from app.audit.domain.entry import AuditEntry, Kind, Person
from app.audit.domain.errors import AuditError, NotAnAdministrator
from tests.fakes import FakeAuditEntries

ADA = Person("acc-ada", "Ada", "ada@x.test")
MAYA = Person("acc-maya", "Maya", "maya@x.test")


def entry(action="approve", reason=None, actor=ADA, target=MAYA, kind=Kind.account, details=()):
    return AuditEntry(actor=actor, action=action, kind=kind, target=target, details=details, reason=reason)


def make():
    port = FakeAuditEntries()
    return AuditService(port), port


ADMIN = Caller("acc-ada", is_administrator=True)
USER = Caller("acc-maya", is_administrator=False)


@pytest.mark.ac("AC-56")
def test_record_adds_the_entry_to_the_port_and_read_gives_it_back_to_an_administrator():
    svc, port = make()
    e = entry("deactivate", "left the team")
    svc.record(e)
    (got,) = svc.read(ADMIN)
    assert got.entry == e
    assert (got.entry.actor, got.entry.target, got.entry.reason) == (ADA, MAYA, "left the team")


@pytest.mark.ac("AC-56")
def test_read_lists_the_newest_first_account_and_project_entries_together():
    svc, _ = make()
    svc.record(entry("approve"))
    svc.record(entry("create_project", kind=Kind.project, target=Person("p1", "Apollo"), details=(MAYA,)))
    svc.record(entry("deactivate", "left"))
    assert [r.entry.action for r in svc.read(ADMIN)] == ["deactivate", "create_project", "approve"]
    assert svc.read(ADMIN)[1].entry.details == (MAYA,)


@pytest.mark.ac("AC-68")
def test_read_refuses_a_caller_who_is_not_an_administrator_and_shows_nothing():
    svc, _ = make()
    svc.record(entry())
    with pytest.raises(NotAnAdministrator) as refused:
        svc.read(USER)
    assert isinstance(refused.value, AuditError)


@pytest.mark.ac("AC-69")
def test_an_empty_trail_is_an_empty_list_not_an_error():
    svc, _ = make()
    assert svc.read(ADMIN) == []


@pytest.mark.ac("AC-82")
def test_reading_writes_no_entry():
    svc, port = make()
    svc.record(entry())
    svc.read(ADMIN)
    with pytest.raises(NotAnAdministrator):
        svc.read(USER)
    assert len(port.stored) == 1


@pytest.mark.rule("RULE-L2")
def test_no_part_of_the_domain_or_the_application_can_set_the_time():
    assert "at" not in {f.name for f in dataclasses.fields(AuditEntry)}
    with pytest.raises(TypeError):
        AuditEntry(actor=ADA, action="approve", kind=Kind.account, target=MAYA, at=object())  # type: ignore[call-arg]
    assert list(inspect.signature(AuditService.record).parameters) == ["self", "entry"]
    assert list(inspect.signature(AuditEntries.add).parameters) == ["self", "entry"]


def test_the_entry_keeps_the_names_it_was_given_and_cannot_be_changed():
    e = entry()
    assert (e.actor.name, e.actor.email, e.target.name, e.target.email) == ("Ada", "ada@x.test", "Maya", "maya@x.test")
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.reason = "rewritten"  # type: ignore[misc]


def test_an_entry_with_no_actor_is_allowed_for_a_system_action():
    svc, _ = make()
    svc.record(entry("register", actor=None))
    assert svc.read(ADMIN)[0].entry.actor is None
