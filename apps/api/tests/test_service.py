"""The use cases of Access, tested with in-memory ports: no database, no Keycloak, no HTTP, a fixed clock."""

from datetime import datetime

import pytest
from app.access.domain.account import (
    Action,
    InvalidTransition,
    LastAdministrator,
    Role,
    Status,
)
from app.access.service import AccessService, IdentityProviderUnavailable

from tests.fakes import FakeAccounts, FakeAudit, FakeIdp, FakeUnitOfWork

NOW = datetime(2026, 11, 17, 9, 0, 0)


def make(admins=("ada@x.test",)):
    accounts, audit, idp = FakeAccounts(), FakeAudit(), FakeIdp()
    return (
        AccessService(
            accounts, audit, idp, set(admins), now=lambda: NOW, uow=FakeUnitOfWork()
        ),
        accounts,
        audit,
        idp,
    )


@pytest.mark.ac("AC-3")
def test_first_sight_makes_a_pending_account_stamped_by_the_injected_clock():
    svc, accounts, audit, _ = make()
    a = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    assert (a.status, a.role, a.created) == (Status.pending, Role.user, NOW)
    assert audit.rows == [(None, "register", a.id, None, NOW)]


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
    assert audit.rows == [(None, "create_bootstrap_admin", a.id, None, NOW)]


@pytest.mark.ac("AC-61")
@pytest.mark.rule("RULE-A5")
def test_with_an_active_administrator_the_setup_email_is_only_pending():
    svc, accounts, audit, _ = make()
    first = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    assert accounts.count_active_administrators() == 1
    second = svc.account_for("sub-ada-2", "Ada again", "ada@x.test", True)
    assert (second.role, second.status) == (Role.user, Status.pending)
    assert audit.rows[-1] == (None, "register", second.id, None, NOW)
    assert (
        accounts.count_active_administrators() == 1
        and accounts.by_id(first.id).role is Role.administrator
    )


def test_deactivate_calls_keycloak_before_changing_anything():
    svc, accounts, audit, idp = make()
    admin = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    svc.change(admin, maya.id, Action.approve)
    svc.change(admin, maya.id, Action.deactivate, "left the team")
    assert idp.calls == [("disable", "sub-1"), ("logout", "sub-1")]
    assert accounts.by_id(maya.id).status is Status.deactivated
    assert audit.rows[-1] == (admin.id, "deactivate", maya.id, "left the team", NOW)


def test_a_keycloak_failure_changes_nothing():
    svc, accounts, audit, idp = make()
    admin = svc.account_for("sub-ada", "Ada", "ada@x.test", True)
    maya = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    svc.change(admin, maya.id, Action.approve)
    svc.change(admin, maya.id, Action.deactivate, "left the team")
    idp.fail = True
    before = len(audit.rows)
    with pytest.raises(IdentityProviderUnavailable):
        svc.change(admin, maya.id, Action.reinstate, "came back")
    assert (
        accounts.by_id(maya.id).status is Status.deactivated
        and len(audit.rows) == before
    )


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
    assert (
        result.account.status is Status.deactivated and result.keycloak_updated is False
    )
    assert accounts.by_id(maya.id).status is Status.deactivated
    assert events == ["commit", "disable_user"]
    entries = [o for r, o in zip(audit.rows, audit.outcomes) if r[1] == "deactivate"]
    assert entries == ["keycloak_not_updated"]


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
    svc, accounts, audit, idp, events, admin, maya = (
        _deactivated_while_keycloak_was_down()
    )
    before = accounts.by_id(maya.id)

    raised, result = None, None
    try:
        result = svc.change(
            admin, maya.id, Action.deactivate, "retry the Keycloak call"
        )
    except Exception as exc:  # noqa: BLE001 - the assertion below names it
        raised = exc

    assert raised is None
    assert result.keycloak_updated is True
    assert result.account == before and accounts.by_id(maya.id) == before
    assert before.status is Status.deactivated
    assert idp.calls == [("disable", "sub-1"), ("logout", "sub-1")]
    entries = [o for r, o in zip(audit.rows, audit.outcomes) if r[1] == "deactivate"]
    assert entries == ["keycloak_not_updated", "done"]


@pytest.mark.ac("AC-77")
def test_deactivating_again_while_keycloak_is_still_down_reports_it_and_does_not_raise():
    svc, accounts, audit, idp, events, admin, maya = (
        _deactivated_while_keycloak_was_down()
    )
    idp.fail = True

    raised, result = None, None
    try:
        result = svc.change(
            admin, maya.id, Action.deactivate, "retry the Keycloak call"
        )
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
