"""The use cases of Access, tested with in-memory ports: no database, no Keycloak, no HTTP, a fixed clock."""

from datetime import datetime

import pytest

from app.access.domain.account import Action, Role, Status
from app.access.service import AccessService, IdentityProviderUnavailable

from tests.fakes import FakeAccounts, FakeAudit, FakeIdp

NOW = datetime(2026, 11, 17, 9, 0, 0)


def make(admins=("ada@x.test",)):
    accounts, audit, idp = FakeAccounts(), FakeAudit(), FakeIdp()
    return AccessService(accounts, audit, idp, set(admins), now=lambda: NOW), accounts, audit, idp


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
    assert accounts.count_active_administrators() == 1 and accounts.by_id(first.id).role is Role.administrator


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
    idp.fail = True
    before = len(audit.rows)
    with pytest.raises(IdentityProviderUnavailable):
        svc.change(admin, maya.id, Action.deactivate, "left the team")
    assert accounts.by_id(maya.id).status is Status.active and len(audit.rows) == before


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
