"""The SQL adapters keep the promises of the ports. Characterization tests: SQLite by default, PostgreSQL with TEST_DATABASE_URL."""

import os
from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.access.adapters.outbound.sql import SqlAccounts
from app.access.domain.account import Account, Role, Status
from tests.conftest import make_engine
from tests.migrations_support import drop_everything, owner_engine

T0 = datetime(2026, 1, 1, 12, 0, 0)


@pytest.fixture
def session():
    engine = make_engine()  # migrated to head by Alembic, as the owner
    with Session(engine) as s:
        yield s
    engine.dispose()
    if os.environ.get("TEST_DATABASE_URL"):
        owner = owner_engine()
        drop_everything(owner)
        owner.dispose()


@pytest.fixture
def accounts(session):
    return SqlAccounts(session)


def acct(n: int, role=Role.user, status=Status.active, created=None, created_by=None) -> Account:
    return Account(
        f"id-{n}",
        f"sub-{n}",
        f"Person {n}",
        f"p{n}@x.test",
        role,
        status,
        created or T0 + timedelta(minutes=n),
        created_by,
    )


def test_add_then_get_by_id_and_by_identity(accounts):
    a = acct(1, Role.administrator, Status.active, created_by="id-0")
    accounts.add(a)
    assert accounts.by_id("id-1") == a
    assert accounts.by_identity("sub-1") == a


def test_unknown_id_and_identity_give_nothing(accounts):
    accounts.add(acct(1))
    assert accounts.by_id("nope") is None
    assert accounts.by_identity("nope") is None


def test_a_second_account_with_the_same_identity_is_refused(accounts):
    accounts.add(acct(1))
    clash = Account("id-other", "sub-1", "Other", "o@x.test", Role.user, Status.pending, T0)
    with pytest.raises(IntegrityError):
        accounts.add(clash)


def test_a_second_account_with_the_same_id_is_refused(accounts):
    accounts.add(acct(1))
    with pytest.raises(IntegrityError):
        accounts.add(Account("id-1", "sub-9", "Other", "o@x.test", Role.user, Status.pending, T0))


# the count of active administrators is what the last administrator rule reads
@pytest.mark.rule("RULE-A1")
def test_count_counts_only_active_administrators(accounts):
    accounts.add(acct(1, Role.administrator, Status.active))
    accounts.add(acct(2, Role.administrator, Status.pending))
    accounts.add(acct(3, Role.administrator, Status.deactivated))
    accounts.add(acct(4, Role.user, Status.active))
    assert accounts.count_active_administrators() == 1


@pytest.mark.rule("RULE-A1")
def test_count_is_zero_with_no_accounts_and_follows_a_save(accounts):
    assert accounts.count_active_administrators() == 0
    a = acct(1, Role.administrator, Status.active)
    accounts.add(a)
    assert accounts.count_active_administrators() == 1
    accounts.save(a.with_(status=Status.deactivated))
    assert accounts.count_active_administrators() == 0
    accounts.save(a.with_(status=Status.active, role=Role.user))
    assert accounts.count_active_administrators() == 0


def test_list_is_oldest_first_and_can_filter_by_status(accounts):
    accounts.add(acct(3, status=Status.pending))
    accounts.add(acct(1, status=Status.active))
    accounts.add(acct(2, status=Status.pending))
    assert [a.id for a in accounts.list()] == ["id-1", "id-2", "id-3"]
    assert [a.id for a in accounts.list("pending")] == ["id-2", "id-3"]
    assert accounts.list("deactivated") == []


def test_save_updates_name_email_role_and_status(accounts):
    a = acct(1, Role.user, Status.pending)
    accounts.add(a)
    changed = a.with_(name="New Name", email="new@x.test", role=Role.administrator, status=Status.active)
    accounts.save(changed)
    assert accounts.by_id("id-1") == changed


def test_save_does_not_change_identity_created_or_created_by(accounts):
    a = acct(1, created_by="id-0")
    accounts.add(a)
    accounts.save(a.with_(identity="sub-changed", created=T0 + timedelta(days=9), created_by="id-9"))
    got = accounts.by_id("id-1")
    assert (got.identity, got.created, got.created_by) == (a.identity, a.created, a.created_by)


def test_save_of_an_unknown_account_fails(accounts):
    # The port does not say; the adapter raises AttributeError (None has no attributes). Pinned here.
    with pytest.raises(AttributeError):
        accounts.save(acct(1))
