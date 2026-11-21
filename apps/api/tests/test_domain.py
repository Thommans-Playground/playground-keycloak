from datetime import datetime

import pytest

from app.access.domain.account import (
    Account,
    AccountNotFound,
    Action,
    CannotChangeSelf,
    InvalidReason,
    InvalidTransition,
    LastAdministrator,
    ReasonRequired,
    Role,
    Status,
    clean_reason,
    decide,
    duplicates_by_email,
    new_account,
)


def acct(id: str, role=Role.user, status=Status.active) -> Account:
    return Account(id, f"sub-{id}", id, f"{id}@x.test", role, status, datetime(2026, 1, 1))


@pytest.mark.rule("RULE-A3")
def test_rule_a3_reason_must_say_something():
    for bad in (None, "", "   ", "?!", "ab"):
        with pytest.raises(ReasonRequired):
            clean_reason(bad)
    assert clean_reason("  Left the team ") == "Left the team"


@pytest.mark.ac("AC-81")
@pytest.mark.rule("RULE-A3")
def test_rule_a3_a_reason_of_500_characters_is_accepted_and_501_is_refused():
    assert clean_reason("a" * 500) == "a" * 500
    with pytest.raises(InvalidReason):
        clean_reason("a" * 501)


@pytest.mark.ac("AC-81")
@pytest.mark.rule("RULE-A3")
def test_rule_a3_the_length_is_counted_after_trimming_and_the_stored_reason_is_the_trimmed_one():
    assert clean_reason("  " + "a" * 500 + "\t \n") == "a" * 500
    with pytest.raises(InvalidReason):
        clean_reason(" " + "a" * 501 + " ")


@pytest.mark.ac("AC-81")
@pytest.mark.rule("RULE-A3")
def test_rule_a3_the_length_counts_unicode_characters_so_an_emoji_is_one():
    smile = "\U0001f600"  # one character, though two UTF-16 units and four UTF-8 bytes
    assert clean_reason("abc" + smile * 497) == "abc" + smile * 497
    with pytest.raises(InvalidReason):
        clean_reason("abc" + smile * 498)


@pytest.mark.ac("AC-81")
@pytest.mark.rule("RULE-A3")
@pytest.mark.parametrize(
    "bad",
    [
        "Left the\nteam",
        "Left the\tteam",
        "Left\rthe team",
        "Left the\x00team",
        "Left the team\u202e",
        "Left \u2066the team",
        "Left the \u2069team",
        "Left the\u200eteam",
        "Left the\u200fteam",
        "Left the\u061cteam",
    ],
)
def test_rule_a3_a_control_or_bidirectional_character_is_refused(bad):
    with pytest.raises(InvalidReason) as refused:
        clean_reason(bad)
    assert bad not in refused.value.message  # the answer does not echo the reason


@pytest.mark.rule("RULE-A2")
def test_rule_a2_nobody_deactivates_or_demotes_themselves():
    admin = acct("a", Role.administrator)
    for action in (Action.deactivate, Action.demote):
        with pytest.raises(CannotChangeSelf):
            decide(action, admin, admin, active_admins=2)


@pytest.mark.rule("RULE-A1")
def test_rule_a1_last_administrator_is_kept():
    actor, last = acct("a", Role.administrator), acct("b", Role.administrator)
    for action in (Action.deactivate, Action.demote):
        with pytest.raises(LastAdministrator):
            decide(action, actor, last, active_admins=1)
    assert decide(Action.demote, actor, last, active_admins=2).role is Role.user


@pytest.mark.ac("AC-51")
def test_the_only_administrator_cannot_demote_themselves():
    # The actor IS the last administrator and the target. Two rules refuse it (A2 first, A1 behind it): an administrator remains.
    only = acct("a", Role.administrator)
    with pytest.raises((CannotChangeSelf, LastAdministrator)):
        decide(Action.demote, only, only, active_admins=1)


@pytest.mark.ac("AC-66")
def test_transitions():
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
    for cls in (ReasonRequired, InvalidReason, CannotChangeSelf, LastAdministrator, InvalidTransition, AccountNotFound):
        assert not hasattr(cls, "http_status"), cls.__name__


NOW = datetime(2026, 11, 17, 9, 0, 0)


def _new(email="ada@x.test", verified=True, setup=("ada@x.test",), admins=0):
    return new_account("sub-n", "Ada", email, verified, set(setup), admins, lambda: NOW)


@pytest.mark.rule("RULE-A5")
def test_rule_a5_only_a_verified_setup_email_with_no_active_administrator_makes_an_administrator():
    first = _new()
    assert (first.role, first.status, first.created, first.identity) == (
        Role.administrator,
        Status.active,
        NOW,
        "sub-n",
    )
    assert _new(email=" ADA@x.test ").role is Role.administrator  # case and spaces do not matter
    for other in (_new(admins=1), _new(verified=False), _new(email="bob@x.test"), _new(setup=())):
        assert (other.role, other.status) == (Role.user, Status.pending)


@pytest.mark.ac("AC-73")
def test_accounts_sharing_an_email_are_each_others_duplicates_ignoring_case_and_spaces():
    a = acct("a", status=Status.active).with_(email="Maya@x.test")
    b = acct("b", status=Status.pending).with_(email=" maya@X.test ")
    c = acct("c", status=Status.deactivated).with_(email="maya@x.test")
    d = acct("d")  # d@x.test, alone
    found = duplicates_by_email([a, b, c, d])
    assert [x.id for x in found["a"]] == ["b", "c"]
    assert [x.id for x in found["b"]] == ["a", "c"]
    assert [x.id for x in found["c"]] == ["a", "b"]
    assert found["d"] == []


def test_only_an_active_account_is_active():
    assert acct("a", status=Status.active).is_active
    assert not acct("p", status=Status.pending).is_active
    assert not acct("d", status=Status.deactivated).is_active
