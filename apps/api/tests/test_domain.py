from datetime import datetime

import pytest

from app.access.domain.account import (
    Account, AccountNotFound, Action, CannotChangeSelf, InvalidTransition, LastAdministrator, ReasonRequired, Role,
    Status, clean_reason, decide,
)


def acct(id: str, role=Role.user, status=Status.active) -> Account:
    return Account(id, f"sub-{id}", id, f"{id}@x.test", role, status, datetime(2026, 1, 1))


def test_rule_a3_reason_must_say_something():  # Verifies RULE-A3
    for bad in (None, "", "   ", "?!", "ab"):
        with pytest.raises(ReasonRequired):
            clean_reason(bad)
    assert clean_reason("  Left the team ") == "Left the team"


def test_rule_a2_nobody_deactivates_or_demotes_themselves():  # Verifies RULE-A2
    admin = acct("a", Role.administrator)
    for action in (Action.deactivate, Action.demote):
        with pytest.raises(CannotChangeSelf):
            decide(action, admin, admin, active_admins=2)


def test_rule_a1_last_administrator_is_kept():  # Verifies RULE-A1, AC-51
    actor, last = acct("a", Role.administrator), acct("b", Role.administrator)
    for action in (Action.deactivate, Action.demote):
        with pytest.raises(LastAdministrator):
            decide(action, actor, last, active_admins=1)
    assert decide(Action.demote, actor, last, active_admins=2).role is Role.user


def test_transitions():  # Verifies AC-66
    admin = acct("a", Role.administrator)
    assert decide(Action.approve, admin, acct("p", status=Status.pending), 1).status is Status.active
    assert decide(Action.deactivate, admin, acct("u"), 1).status is Status.deactivated
    assert decide(Action.reinstate, admin, acct("d", status=Status.deactivated), 1).status is Status.active
    assert decide(Action.promote, admin, acct("u"), 1).role is Role.administrator
    with pytest.raises(InvalidTransition):
        decide(Action.approve, admin, acct("u"), 1)
    with pytest.raises(InvalidTransition):
        decide(Action.reinstate, admin, acct("u"), 1)
    with pytest.raises(InvalidTransition):
        decide(Action.promote, admin, acct("p", status=Status.pending), 1)


def test_domain_errors_say_what_went_wrong_and_not_how_http_answers():
    # The domain does not know HTTP. The web layer maps a rule to a status (NFR-3).
    for cls in (ReasonRequired, CannotChangeSelf, LastAdministrator, InvalidTransition, AccountNotFound):
        assert not hasattr(cls, "http_status"), cls.__name__
