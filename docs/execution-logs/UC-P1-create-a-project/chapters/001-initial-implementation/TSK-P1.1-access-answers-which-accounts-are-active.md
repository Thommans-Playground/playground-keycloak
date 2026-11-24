# Task P1.1: Access answers which accounts are active

**Task ID:** TSK-P1.1 · **Use Case:** UC-P1 · **Criteria:** AC-13 and AC-18 (afterwards): this task builds the question they ask and carries no criterion marker of its own · **Code matched at:** `7481263`

What this does and why: [summary, task P1.1](summary.md#p11-access-answers-which-accounts-are-active).

Run from `apps/api/`: `uv run pytest tests/test_adapters_sql.py tests/test_domain.py tests/test_service.py -q`

Work test first in each step: write the test, run it, see it fail, then write the code.

---

## Step 1: an account knows it is active

**Test** (Unit):

```python
# apps/api/tests/test_domain.py
def test_only_an_active_account_is_active():
    assert acct("a", status=Status.active).is_active
    assert not acct("p", status=Status.pending).is_active
    assert not acct("d", status=Status.deactivated).is_active
```

**Code**:

```python
# apps/api/app/access/domain/account.py
    @property
    def is_active(self) -> bool:
        return self.status is Status.active
```

```python
# apps/api/app/access/domain/account.py
    @property
    def is_active_administrator(self) -> bool:
        return self.is_active and self.role is Role.administrator
```

**Logic.** `is_active` is the one place that says what active means. `is_active_administrator` reuses it instead of testing the status
again.

---

## Step 2: the repository finds many accounts in one query

**Test** (Unit):

```python
# apps/api/tests/test_adapters_sql.py
def test_by_ids_gives_the_accounts_asked_for_and_skips_unknown_ids(accounts):
    for n in (1, 2, 3):
        accounts.add(acct(n))
    got = accounts.by_ids(["id-3", "id-1", "nope"])
    assert sorted(a.id for a in got) == ["id-1", "id-3"]
    assert {a.id: a for a in got}["id-1"] == acct(1)
```

```python
# apps/api/tests/test_adapters_sql.py
def test_by_ids_with_no_ids_answers_empty_without_a_query(accounts, session):
    from sqlalchemy import event

    seen = []
    event.listen(session.get_bind(), "before_cursor_execute", lambda *a: seen.append(a[2]))
    assert accounts.by_ids([]) == []
    assert seen == []
```

```python
# apps/api/tests/test_adapters_sql.py
def test_by_ids_is_one_query(accounts, session):
    from sqlalchemy import event

    for n in (1, 2, 3):
        accounts.add(acct(n))
    seen = []
    event.listen(session.get_bind(), "before_cursor_execute", lambda *a: seen.append(a[2]))
    accounts.by_ids(["id-1", "id-2", "id-3"])
    assert len(seen) == 1
```

**Code**:

```python
# apps/api/app/access/application/ports.py
class AccountRepository(Protocol):
    def by_identity(self, identity: str) -> Account | None: ...
    def by_id(self, account_id: str) -> Account | None: ...
    def by_ids(self, account_ids: list[str]) -> list[Account]: ...
    def add(self, account: Account) -> None: ...
    def save(self, account: Account) -> None: ...
    def list(self, status: str | None = None) -> list[Account]: ...
    def count_active_administrators(self) -> int: ...
    def lock_active_administrators(self) -> "list[Account]": ...
```

```python
# apps/api/app/access/adapters/outbound/sql.py, inside class SqlAccounts
    def by_ids(self, account_ids: list[str]) -> list[Account]:
        if not account_ids:
            return []
        return [_to_domain(r) for r in self._s.scalars(select(AccountRow).where(AccountRow.id.in_(account_ids)))]
```

The fake lives in `tests/fakes.py` and serves the service tests of stage 3; its duplicate removal mirrors the service:

```python
# apps/api/tests/fakes.py, inside class FakeAccounts
    def by_ids(self, account_ids):
        return [self.rows[i] for i in dict.fromkeys(account_ids) if i in self.rows]
```

**Logic.** The port block is the whole `AccountRepository` protocol at the final commit, so it holds other methods that belong to other
tasks; `by_ids` is the one this task adds. An empty list returns before any query, and the rest is one `IN` query.

---

## Step 3: the service answers

**Test** (Unit):

```python
# apps/api/tests/test_service.py
def _three_people():
    svc, accounts, _, _ = make()
    ids = {}
    for status in (Status.active, Status.pending, Status.deactivated):
        a = svc.account_for(f"sub-{status.value}", status.value.title(), f"{status.value}@x.test", True)
        accounts.save(a.with_(status=status))
        ids[status] = a.id
    return svc, accounts, ids
```

```python
# apps/api/tests/test_service.py
def test_active_among_returns_only_the_active_accounts():
    svc, _, ids = _three_people()
    got = svc.active_among([ids[Status.active], ids[Status.pending], ids[Status.deactivated], "unknown"])
    assert set(got) == {ids[Status.active]}
```

```python
# apps/api/tests/test_service.py
def test_active_among_counts_a_duplicate_once_and_an_empty_list_answers_empty():
    svc, _, ids = _three_people()
    got = svc.active_among([ids[Status.active], ids[Status.active]])
    assert list(got) == [ids[Status.active]]
    assert list(svc.active_among([])) == []
```

```python
# apps/api/tests/test_service.py
def test_people_gives_id_name_and_email_as_they_are_now_and_omits_unknown_ids():
    svc, accounts, ids = _three_people()
    accounts.save(accounts.by_id(ids[Status.pending]).with_(name="Renamed", email="new@x.test"))
    got = svc.people([ids[Status.pending], ids[Status.active], "unknown"])
    assert {p.id: (p.name, p.email) for p in got} == {
        ids[Status.pending]: ("Renamed", "new@x.test"),
        ids[Status.active]: ("Active", "active@x.test"),
    }
    assert svc.people([]) == []
```

**Code**:

```python
# apps/api/app/access/application/ports.py
@dataclass(frozen=True)
class AccountSummary:
    """Who an account is now, as Access tells another context (never the entity itself)."""

    id: str
    name: str
    email: str
```

```python
# apps/api/app/access/application/service.py, inside class AccessService
    def active_among(self, ids: list[str]) -> list[str]:
        """Of these account ids, the ones that belong to active accounts (for another context)."""
        return [a.id for a in self.accounts.by_ids(list(set(ids))) if a.is_active]
```

```python
# apps/api/app/access/application/service.py, inside class AccessService
    def people(self, ids: list[str]) -> list[AccountSummary]:
        """Id, name and email as they are now, for the known ids (for another context)."""
        return [AccountSummary(a.id, a.name, a.email) for a in self.accounts.by_ids(list(set(ids)))]
```

`AccountSummary` is also added to the `from app.access.application.ports import (...)` list at the top of `service.py`.

**Logic.** `set(ids)` removes duplicates before the one query. `active_among` keeps the accounts whose `is_active` is true, so an unknown,
pending and deactivated id all vanish the same way. `people` skips the filter and returns the summary of each known id.
