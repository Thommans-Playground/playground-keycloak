"""The use cases of Access, tested with in-memory ports: no database, no Keycloak, no HTTP, a fixed clock."""

from datetime import datetime

import pytest

from app.access.application.service import AccessService, IdentityProviderUnavailable
from app.access.domain.account import (
    Action,
    InvalidReason,
    InvalidTransition,
    LastAdministrator,
    Role,
    Status,
)
from tests.fakes import FakeAccounts, FakeAudit, FakeIdp, FakeUnitOfWork

NOW = datetime(2026, 11, 17, 9, 0, 0)


def make(admins=("ada@x.test",)):
    accounts, audit, idp = FakeAccounts(), FakeAudit(), FakeIdp()
    return (
        AccessService(accounts, audit, idp, set(admins), now=lambda: NOW, uow=FakeUnitOfWork()),
        accounts,
        audit,
        idp,
    )


@pytest.mark.ac("AC-3")
def test_first_sight_makes_a_pending_account_stamped_by_the_injected_clock():
    svc, accounts, audit, _ = make()
    a = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    assert (a.status, a.role, a.created) == (Status.pending, Role.user, NOW)
    assert audit.shapes() == [(None, "register", a.id, None)]


@pytest.mark.ac("AC-3")
def test_the_same_person_again_makes_no_second_account():
    svc, accounts, _, _ = make()
    first = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    again = svc.account_for("sub-1", "Maya R", "maya@x.test", True)
    assert again.id == first.id and len(accounts.rows) == 1 and again.name == "Maya R"


@pytest.mark.ac("AC-75")
@pytest.mark.rule("RULE-A5")
def test_an_unverified_email_cannot_claim_the_first_administrator():
    svc, _, _, _ = make()
    a = svc.account_for("sub-ada", "Ada", "ada@x.test", False)
    assert (a.role, a.status) == (Role.user, Status.pending)


@pytest.mark.ac("AC-74")
@pytest.mark.rule("RULE-A5")
def test_with_no_active_administrator_the_verified_setup_email_makes_the_administrator():
    svc, accounts, audit, _ = make()
    a = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    assert (a.role, a.status) == (Role.administrator, Status.active)
    assert audit.shapes() == [(None, "create_bootstrap_admin", a.id, None)]


@pytest.mark.ac("AC-61")
@pytest.mark.rule("RULE-A5")
def test_with_an_active_administrator_the_setup_email_is_only_pending():
    svc, accounts, audit, _ = make()
    first = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    assert accounts.count_active_administrators() == 1
    second = svc.account_for("sub-ada-2", "Ada again", "ada@x.test", True)
    assert (second.role, second.status) == (Role.user, Status.pending)
    assert audit.shapes()[-1] == (None, "register", second.id, None)
    assert accounts.count_active_administrators() == 1 and accounts.by_id(first.id).role is Role.administrator


def test_deactivate_calls_keycloak_before_changing_anything():
    svc, accounts, audit, idp = make()
    admin = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    svc.change(admin, maya.id, Action.approve)
    svc.change(admin, maya.id, Action.deactivate, "left the team")
    assert idp.calls == [("disable", "sub-1"), ("logout", "sub-1")]
    assert accounts.by_id(maya.id).status is Status.deactivated
    assert audit.shapes()[-1] == (admin.id, "deactivate", maya.id, "left the team")


@pytest.mark.ac("AC-59")
def test_a_keycloak_failure_changes_nothing():
    svc, accounts, audit, idp = make()
    admin = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    svc.change(admin, maya.id, Action.approve)
    svc.change(admin, maya.id, Action.deactivate, "left the team")
    idp.fail = True
    before = len(audit.shapes())
    with pytest.raises(IdentityProviderUnavailable):
        svc.change(admin, maya.id, Action.reinstate, "came back")
    assert accounts.by_id(maya.id).status is Status.deactivated and len(audit.shapes()) == before


@pytest.mark.ac("AC-73")
def test_the_list_shows_for_each_account_the_others_with_the_same_email_whatever_the_filter():
    svc, accounts, _, _ = make()
    svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    one = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    two = svc.account_for("sub-2", "Maya B", "Maya@x.test", True)
    rows = {a.id: dups for a, dups in svc.list_accounts("pending")}
    assert set(rows) == {one.id, two.id}  # the filter still filters
    assert [d.id for d in rows[one.id]] == [two.id]
    assert [d.id for d in rows[two.id]] == [one.id]


@pytest.mark.ac("AC-58")
def test_deactivating_commits_first_and_a_keycloak_failure_still_leaves_it_deactivated_and_audited():
    events: list[str] = []
    accounts, audit, idp, uow = (
        FakeAccounts(),
        FakeAudit(),
        FakeIdp(events),
        FakeUnitOfWork(events),
    )
    svc = AccessService(accounts, audit, idp, {"ada@x.test"}, now=lambda: NOW, uow=uow)
    admin = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    svc.change(admin, maya.id, Action.approve)
    events.clear()
    idp.fail = True

    raised, result = None, None
    try:
        result = svc.change(admin, maya.id, Action.deactivate, "left the team")
    except Exception as exc:  # noqa: BLE001 - the assertion below names it
        raised = exc

    assert raised is None
    assert result.account.status is Status.deactivated and result.keycloak_updated is False
    assert accounts.by_id(maya.id).status is Status.deactivated
    assert events == ["commit", "disable_user"]
    assert [
        e["action"]
        for e in audit.entries()
        if e["target_id"] == maya.id and e["action"] in ("deactivate", "keycloak_not_updated")
    ] == [
        "deactivate",
        "keycloak_not_updated",
    ]


def _deactivated_while_keycloak_was_down():
    events: list[str] = []
    accounts, audit, idp, uow = (
        FakeAccounts(),
        FakeAudit(),
        FakeIdp(events),
        FakeUnitOfWork(events),
    )
    svc = AccessService(accounts, audit, idp, {"ada@x.test"}, now=lambda: NOW, uow=uow)
    admin = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    svc.change(admin, maya.id, Action.approve)
    idp.fail = True
    svc.change(admin, maya.id, Action.deactivate, "left the team")
    idp.fail = False
    idp.calls.clear()
    events.clear()
    return svc, accounts, audit, idp, events, admin, maya


@pytest.mark.ac("AC-77")
def test_deactivating_again_retries_keycloak_and_records_one_new_done_entry():
    svc, accounts, audit, idp, events, admin, maya = _deactivated_while_keycloak_was_down()
    before = accounts.by_id(maya.id)

    raised, result = None, None
    try:
        result = svc.change(admin, maya.id, Action.deactivate, "retry the Keycloak call")
    except Exception as exc:  # noqa: BLE001 - the assertion below names it
        raised = exc

    assert raised is None
    assert result.keycloak_updated is True
    assert result.account == before and accounts.by_id(maya.id) == before
    assert before.status is Status.deactivated
    assert idp.calls == [("disable", "sub-1"), ("logout", "sub-1")]
    assert [
        e["action"]
        for e in audit.entries()
        if e["target_id"] == maya.id and e["action"] in ("deactivate", "keycloak_not_updated")
    ] == [
        "deactivate",
        "keycloak_not_updated",
        "deactivate",
    ]


@pytest.mark.ac("AC-77")
def test_deactivating_again_while_keycloak_is_still_down_reports_it_and_does_not_raise():
    svc, accounts, audit, idp, events, admin, maya = _deactivated_while_keycloak_was_down()
    idp.fail = True

    raised, result = None, None
    try:
        result = svc.change(admin, maya.id, Action.deactivate, "retry the Keycloak call")
    except Exception as exc:  # noqa: BLE001 - the assertion below names it
        raised = exc

    assert raised is None
    assert result.keycloak_updated is False
    assert accounts.by_id(maya.id).status is Status.deactivated


@pytest.mark.ac("AC-66")
def test_a_pending_account_still_cannot_be_deactivated():
    events: list[str] = []
    accounts, audit, idp, uow = (
        FakeAccounts(),
        FakeAudit(),
        FakeIdp(events),
        FakeUnitOfWork(events),
    )
    svc = AccessService(accounts, audit, idp, {"ada@x.test"}, now=lambda: NOW, uow=uow)
    admin = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    with pytest.raises(InvalidTransition):
        svc.change(admin, maya.id, Action.deactivate, "not yet approved")
    assert idp.calls == []


@pytest.mark.ac("AC-62")
def test_a_change_locks_the_active_administrators_before_saving_and_decides_on_the_locked_rows():
    events: list[str] = []

    class LockSeesOne(FakeAccounts):
        """Two administrators are stored, but the locked read (the truth under the lock) finds one."""

        def lock_active_administrators(self):
            super().lock_active_administrators()
            return [a for a in self.rows.values() if a.is_active_administrator][:1]

    accounts = LockSeesOne(events)
    svc = AccessService(
        accounts,
        FakeAudit(),
        FakeIdp(events),
        {"ada@x.test"},
        now=lambda: NOW,
        uow=FakeUnitOfWork(events),
    )
    ada = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    bob = svc.account_for("sub-bob", "Bob", "bob@x.test", True)
    svc.change(ada, bob.id, Action.approve)
    svc.change(ada, bob.id, Action.promote, "needs access")
    assert accounts.count_active_administrators() == 2
    events.clear()

    with pytest.raises(LastAdministrator):
        svc.change(ada, bob.id, Action.demote, "stepping down")

    assert events and events[0] == "lock_active_administrators"
    assert accounts.by_id(bob.id).role is Role.administrator and "save" not in events


@pytest.mark.ac("AC-62")
def test_an_actor_demoted_a_moment_ago_is_refused_on_fresh_state():
    svc, accounts, audit, idp = make()
    ada = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    bob = svc.account_for("sub-bob", "Bob", "bob@x.test", True)
    svc.change(ada, bob.id, Action.approve)
    svc.change(ada, bob.id, Action.promote, "needs access")
    svc.change(ada, bob.id, Action.demote, "stepping down")
    stale_bob = bob.with_(role=Role.administrator, status=Status.active)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    with pytest.raises(InvalidTransition):
        svc.change(stale_bob, maya.id, Action.approve)
    assert accounts.by_id(maya.id).status is Status.pending


def _for(audit, account):
    return [
        e
        for e in audit.entries()
        if e["target_id"] == account.id and e["action"] in ("deactivate", "keycloak_not_updated")
    ]


@pytest.mark.ac("AC-58")
@pytest.mark.rule("RULE-L3")
def test_a_keycloak_failure_after_a_deactivation_adds_its_own_entry_and_never_edits_the_first():
    svc, accounts, audit, idp, events, admin, maya = _deactivated_while_keycloak_was_down()
    entries = _for(audit, maya)
    assert [e["action"] for e in entries] == ["deactivate", "keycloak_not_updated"]
    first, second = entries
    assert first["reason"] == "left the team" and first["actor_id"] == admin.id
    assert second["target_id"] == first["target_id"] and second["actor_id"] == first["actor_id"]
    assert second["reason"] in (first["reason"], None)


@pytest.mark.ac("AC-77")
@pytest.mark.rule("RULE-L3")
def test_a_repeated_deactivation_adds_one_entry_for_the_retry():
    svc, accounts, audit, idp, events, admin, maya = _deactivated_while_keycloak_was_down()
    svc.change(admin, maya.id, Action.deactivate, "retry the Keycloak call")
    entries = _for(audit, maya)
    assert [e["action"] for e in entries] == ["deactivate", "keycloak_not_updated", "deactivate"]
    assert entries[2]["reason"] == "retry the Keycloak call"


@pytest.mark.ac("AC-77")
@pytest.mark.rule("RULE-L3")
def test_a_repeated_deactivation_that_fails_again_adds_the_retry_and_a_second_keycloak_not_updated_entry():
    svc, accounts, audit, idp, events, admin, maya = _deactivated_while_keycloak_was_down()
    idp.fail = True
    svc.change(admin, maya.id, Action.deactivate, "retry the Keycloak call")
    entries = _for(audit, maya)
    assert [e["action"] for e in entries] == [
        "deactivate",
        "keycloak_not_updated",
        "deactivate",
        "keycloak_not_updated",
    ]
    assert entries[2]["reason"] == "retry the Keycloak call"


@pytest.mark.rule("RULE-L1")
def test_the_audit_log_has_no_way_to_edit_an_entry():
    from app.access.application.ports import AuditLog

    assert not hasattr(AuditLog, "set_outcome")
    assert not hasattr(FakeAudit, "set_outcome")


# UC-L1 TSK-L1.4: Access builds the entry from the accounts it holds, with their names as they are at that moment.
def _ref(account):
    from app.access.application.ports import AccountRef

    return AccountRef(account.id, account.name, account.email)


@pytest.mark.ac("AC-56")
def test_a_new_account_is_recorded_with_no_actor_and_the_new_account_as_target_with_its_name_and_email():
    svc, _, audit, _ = make()
    a = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    (event,) = audit.rows
    assert event.actor is None
    assert event.target == _ref(a) and (event.target.name, event.target.email) == ("Maya", "maya@x.test")


@pytest.mark.ac("AC-56")
def test_a_change_is_recorded_with_the_names_of_both_accounts_as_they_are_now():
    svc, accounts, audit, _ = make()
    admin = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    svc.account_for("sub-1", "Maya Renamed", "maya2@x.test", True)  # renamed in Keycloak before the change
    svc.change(admin, maya.id, Action.approve)
    event = audit.rows[-1]
    assert event.action == "approve"
    assert event.actor == _ref(admin) and (event.actor.name, event.actor.email) == ("Ada", "ada@x.test")
    assert (event.target.id, event.target.name, event.target.email) == (maya.id, "Maya Renamed", "maya2@x.test")
    assert event.reason is None


@pytest.mark.ac("AC-56")
def test_a_keycloak_not_updated_entry_carries_the_names_too():
    svc, accounts, audit, idp, events, admin, maya = _deactivated_while_keycloak_was_down()
    event = audit.rows[-1]
    assert event.action == "keycloak_not_updated"
    assert (event.actor.name, event.target.name) == ("Ada", "Maya")


# What Access answers for another context (UC-P1 slice 1): who is active, and who someone is now.
def _three_people():
    svc, accounts, _, _ = make()
    ids = {}
    for status in (Status.active, Status.pending, Status.deactivated):
        a = svc.account_for(f"sub-{status.value}", status.value.title(), f"{status.value}@x.test", True)
        accounts.save(a.with_(status=status))
        ids[status] = a.id
    return svc, accounts, ids


def test_active_among_returns_only_the_active_accounts():
    svc, _, ids = _three_people()
    got = svc.active_among([ids[Status.active], ids[Status.pending], ids[Status.deactivated], "unknown"])
    assert set(got) == {ids[Status.active]}


def test_active_among_counts_a_duplicate_once_and_an_empty_list_answers_empty():
    svc, _, ids = _three_people()
    got = svc.active_among([ids[Status.active], ids[Status.active]])
    assert list(got) == [ids[Status.active]]
    assert list(svc.active_among([])) == []


def test_people_gives_id_name_and_email_as_they_are_now_and_omits_unknown_ids():
    svc, accounts, ids = _three_people()
    accounts.save(accounts.by_id(ids[Status.pending]).with_(name="Renamed", email="new@x.test"))
    got = svc.people([ids[Status.pending], ids[Status.active], "unknown"])
    assert {p.id: (p.name, p.email) for p in got} == {
        ids[Status.pending]: ("Renamed", "new@x.test"),
        ids[Status.active]: ("Active", "active@x.test"),
    }
    assert svc.people([]) == []


@pytest.mark.ac("AC-81")
@pytest.mark.rule("RULE-A3")
@pytest.mark.parametrize("bad", ["a" * 501, "Left the\nteam", "Left the team\u202e"])
@pytest.mark.parametrize("action", [Action.deactivate, Action.reinstate, Action.promote, Action.demote])
def test_a_refused_reason_changes_nothing_and_adds_no_audit_entry(action, bad):
    svc, accounts, audit, idp = make()
    admin = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    svc.change(admin, maya.id, Action.approve)
    if action is Action.reinstate:
        svc.change(admin, maya.id, Action.deactivate, "left the team")
    if action is Action.demote:
        svc.change(admin, maya.id, Action.promote, "helps approve")
    before_account, before_audit, before_calls = accounts.by_id(maya.id), len(audit.shapes()), list(idp.calls)
    with pytest.raises(InvalidReason):
        svc.change(admin, maya.id, action, bad)
    assert accounts.by_id(maya.id) == before_account
    assert len(audit.shapes()) == before_audit and idp.calls == before_calls
