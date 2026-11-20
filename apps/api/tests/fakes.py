"""In-memory stand-ins for the ports, so a use case can be tested with no database and no Keycloak."""

from datetime import datetime


class FakeIdp:
    """Stands in for Keycloak's admin API and records what it was asked."""

    def __init__(self, events: list[str] | None = None):
        self.calls: list[tuple[str, str]] = []
        self.fail = False
        self.events = events if events is not None else []

    def _do(self, what: str, identity: str):
        if self.fail:
            raise RuntimeError("keycloak down")
        self.calls.append((what, identity))

    def enable_user(self, identity): self._do("enable", identity)
    def disable_user(self, identity):
        self.events.append("disable_user")
        self._do("disable", identity)
    def end_sessions(self, identity): self._do("logout", identity)


class FakeAccounts:
    def __init__(self, events: list[str] | None = None):
        self.rows: dict[str, object] = {}
        self.events = events if events is not None else []

    def by_identity(self, identity):
        return next((a for a in self.rows.values() if a.identity == identity), None)

    def by_id(self, account_id): return self.rows.get(account_id)
    def add(self, account): self.rows[account.id] = account
    def save(self, account):
        self.events.append("save")
        self.rows[account.id] = account

    def list(self, status=None):
        return [a for a in self.rows.values() if status is None or a.status.value == status]

    def count_active_administrators(self):
        return sum(1 for a in self.rows.values() if a.is_active_administrator)

    def lock_active_administrators(self):
        self.events.append("lock_active_administrators")
        return [a for a in self.rows.values() if a.is_active_administrator]


class FakeAudit:
    def __init__(self):
        self.rows: list[tuple[str | None, str, str, str | None, datetime]] = []
        self.outcomes: list[str | None] = []  # parallel to rows

    def record(self, actor_id, action, target_id, reason, at, outcome=None):
        self.rows.append((actor_id, action, target_id, reason, at))
        self.outcomes.append(outcome)

    def set_outcome(self, target_id, action, outcome):
        i = max(i for i, r in enumerate(self.rows) if r[1] == action and r[2] == target_id)
        self.outcomes[i] = outcome

    def entries(self): return [dict(zip(("actor_id", "action", "target_id", "reason", "at"), r)) for r in self.rows]


class FakeUnitOfWork:
    """Records commit() into an event list that can be shared with FakeIdp, to prove the order."""

    def __init__(self, events: list[str] | None = None):
        self.events = events if events is not None else []

    def commit(self): self.events.append("commit")
