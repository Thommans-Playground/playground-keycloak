"""SqlAuditEntries keeps the promises of the AuditEntries port. SQLite by default, PostgreSQL with TEST_DATABASE_URL."""

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.audit.adapters.outbound.sql import SqlAuditEntries
from app.audit.domain.entry import AuditEntry, Kind, Person
from tests.conftest import make_engine
from tests.migrations_support import drop_everything, owner_engine

ADA = Person("acc-ada", "Ada", "ada@x.test")
MAYA = Person("acc-maya", "Maya", "maya@x.test")


@pytest.fixture
def session():
    engine = make_engine()
    with Session(engine) as s:
        yield s
    engine.dispose()
    if os.environ.get("TEST_DATABASE_URL"):
        owner = owner_engine()
        drop_everything(owner)
        owner.dispose()


@pytest.fixture
def entries(session):
    return SqlAuditEntries(session)


def entry(action="approve", reason=None, actor=ADA, target=MAYA, kind=Kind.account, details=()):
    return AuditEntry(actor=actor, action=action, kind=kind, target=target, details=details, reason=reason)


def test_an_entry_comes_back_with_all_its_fields(entries):
    entries.add(entry("deactivate", "left the company"))
    (got,) = entries.list_newest_first()
    assert got.id >= 1
    assert got.entry == entry("deactivate", "left the company")


def test_the_table_is_in_the_audit_context(entries):
    from app.audit.adapters.outbound.sql import AuditRow

    assert AuditRow.__tablename__ == "audit_entries"
    import app.access.adapters.outbound.sql as access_sql

    assert not hasattr(access_sql, "AuditRow") and not hasattr(access_sql, "SqlAudit")


def test_the_newest_entry_comes_first(entries):
    for action in ("approve", "deactivate", "reinstate"):
        entries.add(entry(action))
    assert [r.entry.action for r in entries.list_newest_first()] == ["reinstate", "deactivate", "approve"]


def test_an_empty_table_lists_nothing(entries):
    assert entries.list_newest_first() == []


def test_no_actor_and_no_reason_round_trip(entries):
    entries.add(entry("register", actor=None))
    (got,) = entries.list_newest_first()
    assert got.entry.actor is None and got.entry.reason is None


def test_a_project_entry_keeps_its_kind_and_the_people_involved(entries):
    people = (MAYA, Person("acc-bob", "Bob", "bob@x.test"))
    entries.add(entry("create_project", kind=Kind.project, target=Person("p1", "Apollo"), details=people))
    (got,) = entries.list_newest_first()
    assert got.entry.kind is Kind.project
    assert got.entry.target == Person("p1", "Apollo", None)
    assert got.entry.details == people


@pytest.mark.rule("RULE-L2")
def test_the_time_is_set_by_the_database_not_by_the_application(entries):
    before = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=5)
    entries.add(entry())
    (got,) = entries.list_newest_first()
    after = datetime.now(UTC).replace(tzinfo=None) + timedelta(seconds=5)
    assert before <= got.at <= after


@pytest.mark.rule("RULE-L2")
def test_the_adapter_never_names_the_time_or_the_id_in_its_insert(session, entries):
    from sqlalchemy import event

    seen: list[str] = []
    event.listen(session.get_bind(), "before_cursor_execute", lambda c, cur, stmt, *a: seen.append(stmt))
    entries.add(entry())
    insert = next(s for s in seen if s.lstrip().upper().startswith("INSERT INTO AUDIT_ENTRIES"))
    columns = insert[insert.index("(") + 1 : insert.index(")")]
    names = {c.strip() for c in columns.split(",")}
    assert "at" not in names and "id" not in names, insert


def test_the_table_has_the_columns_of_an_entry(session):
    columns = {c["name"] for c in inspect(session.get_bind()).get_columns("audit_entries")}
    assert columns == {
        "id", "at", "kind", "actor_id", "actor_name", "actor_email", "action",
        "target_id", "target_name", "target_email", "details", "reason",
    }
