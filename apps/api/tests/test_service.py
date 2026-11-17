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


def test_first_sight_makes_a_pending_account_stamped_by_the_injected_clock():  # Verifies AC-76
    svc, accounts, audit, _ = make()
    a = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    assert (a.status, a.role, a.created) == (Status.pending, Role.user, NOW)
    assert audit.rows == [(None, "register", a.id, None, NOW)]


def test_the_same_person_again_makes_no_second_account():  # Verifies AC-77
    svc, accounts, _, _ = make()
    first = svc.account_for("sub-1", "Maya", "maya@x.test", True)
    again = svc.account_for("sub-1", "Maya R", "maya@x.test", True)
    assert again.id == first.id and len(accounts.rows) == 1 and again.name == "Maya R"


def test_an_unverified_email_cannot_claim_the_first_administrator():
    svc, _, _, _ = make()
    a = svc.account_for("sub-ada", "Ada", "ada@x.test", False)
    assert (a.role, a.status) == (Role.user, Status.pending)


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
