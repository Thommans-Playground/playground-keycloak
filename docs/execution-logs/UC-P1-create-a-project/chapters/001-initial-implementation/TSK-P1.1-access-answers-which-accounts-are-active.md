# TSK-P1.1: Access answers which accounts are active among some ids

AC-13 and AC-18 are built afterwards, on top of this; no test here carries an AC marker · plan status: **draft, not reviewed** · matches the code at `7481263`

Ground rules, the layout and the commands are in the [chapter summary](summary.md).

This is the plan someone follows to build this task. It was written by working backwards from the code that exists, so
its final code is that code: each block marked `# file` is a copy of that file at the commit above. All paths are
relative to `apps/api/`.

## 1. What we are building, and why

Projects must know whether a first member has an active account (AC-13), and later whether a person being added is one
(AC-18). Projects never reads an account, so Access answers. This task is the Access side only, built before Projects.

| AC | Given | Then | Why it exists |
|---|---|---|---|
| AC-13 (afterwards, TSK-P1.6) | an administrator creates a project naming a first member who is not active or does not exist | it is refused, with one answer for an account that cannot be a member | A project member is someone who can sign in. Access owns "active", so Projects asks it and never reads a status itself. |
| AC-18 (afterwards, UC-P2) | an administrator adds an account that is pending, deactivated or unknown | it is refused, with one answer for all three | The same question, asked when a member is added later. One answer for three cases so the refusal does not tell which account exists. |

This task has no criterion of its own to prove: it builds the question both will ask. Its tests prove the question
(which of these ids are active), and the two criteria get their markers when the refusal is built.

## 2. The logic

1. **"Active" is a rule of the account, so it sits on `Account`.** `is_active` is true only for status `active`; pending
   and deactivated are not (AC-13, AC-18). `is_active_administrator` already tested the same status, so it now reuses it.
2. **Unknown, pending and deactivated ids are all left out of the answer.** The caller gets the active ones and nothing
   that tells the three apart (AC-13, AC-18).
3. **A duplicate id counts once, and an empty list asks nothing.** The service removes duplicates before it asks; the
   repository answers `[]` for no ids without running a query.
4. **One query for any number of ids.** `by_ids` is a single `IN` query, never one query per id.
5. **Plain values cross the boundary.** `active_among` returns a list of id strings, and `people` returns
   `AccountSummary` (id, name, email), never an `Account`. So Projects imports nothing from Access (ADR 0015); the bridge
   that connects them is `AccountStatusBridge`, built in TSK-P1.6 (the `people` bridge comes in TSK-P1.7).
6. **`people` rides along.** The slice text asks only for `active_among`. The commit also built `people(ids)` (name and
   email now, unknown ids left out) from the same query, for the audit entry of TSK-P1.7 and the member names of ADR 0016.
   It is shown here because it is in the code and shares `by_ids`.

**Where it lives:** the rule in `app/access/domain/account.py`, the use cases in `app/access/application/service.py`, the
port method in `app/access/application/ports.py`, the query in `app/access/adapters/outbound/sql.py`. All inside the
Access context (ADR 0010).

## 3. The plan

Four stages, each test first.

### Stage 1: an account knows it is active

**1a. Write the test** in `tests/test_domain.py`: `test_only_an_active_account_is_active` (active true; pending and
deactivated false).

Run `uv run pytest tests/test_domain.py -q`. **Expect** `1 failed, 8 passed`, the failure an `AttributeError` because
`Account` has no `is_active` (checked; the full suite read `1 failed, 184 passed, 29 skipped`).

**1b. Add the property** to `Account` in `app/access/domain/account.py`, and make `is_active_administrator` use it:

```python
# app/access/domain/account.py, inside class Account
    @property
    def is_active(self) -> bool:
        return self.status is Status.active

    @property
    def is_active_administrator(self) -> bool:
        return self.is_active and self.role is Role.administrator
```

**Expect** `9 passed` (checked).

### Stage 2: the repository finds many accounts in one query

**2a. Write the three tests** in `tests/test_adapters_sql.py`:

- `test_by_ids_gives_the_accounts_asked_for_and_skips_unknown_ids`: three accounts added, ask for `id-3`, `id-1`, `nope`,
  get exactly `id-1` and `id-3`
- `test_by_ids_with_no_ids_answers_empty_without_a_query`: a `before_cursor_execute` listener sees no statement
- `test_by_ids_is_one_query`: asking for three ids runs one statement

Run `uv run pytest tests/test_adapters_sql.py -q`. **Expect** `3 failed, 10 passed`, each an `AttributeError`
(checked).

**2b. Add `by_ids` to the port, the SQL adapter and the in-memory fake.** The fake lives in `tests/fakes.py` and serves
the service tests of stage 3; its duplicate removal mirrors the service. Final code:

```python
# app/access/application/ports.py, inside class AccountRepository
    def by_ids(self, account_ids: list[str]) -> list[Account]: ...
```

```python
# app/access/adapters/outbound/sql.py, inside class SqlAccounts
    def by_ids(self, account_ids: list[str]) -> list[Account]:
        if not account_ids:
            return []
        return [_to_domain(r) for r in self._s.scalars(select(AccountRow).where(AccountRow.id.in_(account_ids)))]
```

```python
# tests/fakes.py, inside class FakeAccounts
    def by_ids(self, account_ids):
        return [self.rows[i] for i in dict.fromkeys(account_ids) if i in self.rows]
```

**Expect** `13 passed` (checked).

### Stage 3: the service answers (AC-13 and AC-18 will call this)

**3a. Write the tests** in `tests/test_service.py`, with a helper that makes one active, one pending and one deactivated
account:

- `test_active_among_returns_only_the_active_accounts`: the three ids plus `"unknown"` give only the active id
- `test_active_among_counts_a_duplicate_once_and_an_empty_list_answers_empty`
- `test_people_gives_id_name_and_email_as_they_are_now_and_omits_unknown_ids`: a renamed pending account shows its new
  name and email; an unknown id is absent; an empty list gives `[]`

Run `uv run pytest tests/test_service.py -q`. **Expect** `3 failed, 21 passed` (checked).

**3b. Add the summary type and the two use cases.** This is the final code:

```python
# app/access/application/ports.py
@dataclass(frozen=True)
class AccountSummary:
    """Who an account is now, as Access tells another context (never the entity itself)."""

    id: str
    name: str
    email: str
```

```python
# app/access/application/service.py, inside class AccessService
    def active_among(self, ids: list[str]) -> list[str]:
        """Of these account ids, the ones that belong to active accounts (for another context)."""
        return [a.id for a in self.accounts.by_ids(list(set(ids))) if a.is_active]

    def people(self, ids: list[str]) -> list[AccountSummary]:
        """Id, name and email as they are now, for the known ids (for another context)."""
        return [AccountSummary(a.id, a.name, a.email) for a in self.accounts.by_ids(list(set(ids)))]
```

with `AccountSummary` added to the `from app.access.application.ports import (...)` list at the top of `service.py`.

**Expect** `24 passed` in `tests/test_service.py`, and the whole suite `191 passed, 29 skipped` (checked).

## 4. Check it yourself

```
uv run pytest tests/test_domain.py tests/test_adapters_sql.py tests/test_service.py -q -k "only_an_active or by_ids or active_among or test_people"
                                                  # the 7 tests of this task: 7 passed
uv run pytest -q                                  # at 7481263: 468 passed, 47 skipped
```

The full-suite count at `7481263` includes everything built after this task; it was run for this file. Right after this
task alone the suite was `191 passed, 29 skipped` on SQLite (checked above). The commit message also records 220 on
PostgreSQL; that was not run here (see the note below).

## 5. Where this leaves things

- Source: `app/access/domain/account.py`, `app/access/application/ports.py`, `app/access/application/service.py`,
  `app/access/adapters/outbound/sql.py`
- Tests: `tests/test_domain.py`, `tests/test_adapters_sql.py`, `tests/test_service.py`; the fake in `tests/fakes.py`
- ADR: 0015 (the decision that Access answers through a new use case); no new ADR.
- Not here: the bridge in `composition/` that calls `active_among` for Projects (`AccountStatusBridge`, first added in
  TSK-P1.6, commit `c5c6f64`), the refusal itself (TSK-P1.6, AC-13), and the bridge for `people` (TSK-P1.7, `58dc0f1`).

## Where the real build differs

- One commit, `5b3dd94`, built the task. It also built `people` (decision 6), which the slice text does not name.
- The commit message says tests were also run on PostgreSQL (220). They were not run for this file: `TEST_DATABASE_URL`
  was not set, so only the SQLite counts above are checked. No test of this task needs PostgreSQL.
- No test here has an `@pytest.mark.ac` marker, because the criteria belong to TSK-P1.6 and UC-P2.

## Review

Not reviewed. Write `Reviewed by <name> at <hash>` here when the plan has been read against the code.
