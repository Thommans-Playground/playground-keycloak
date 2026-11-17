"""In-memory stand-ins for the ports, so a use case can be tested with no database and no Keycloak."""

from datetime import datetime


class FakeIdp:
    """Stands in for Keycloak's admin API and records what it was asked."""

    def __init__(self):
        self.calls: list[tuple[str, str]] = []
        self.fail = False

    def _do(self, what: str, identity: str):
        if self.fail:
            raise RuntimeError("keycloak down")
        self.calls.append((what, identity))

    def enable_user(self, identity): self._do("enable", identity)
    def disable_user(self, identity): self._do("disable", identity)
    def end_sessions(self, identity): self._do("logout", identity)


class FakeAccounts:
    def __init__(self):
        self.rows: dict[str, object] = {}

    def by_identity(self, identity):
        return next((a for a in self.rows.values() if a.identity == identity), None)

    def by_id(self, account_id): return self.rows.get(account_id)
    def add(self, account): self.rows[account.id] = account
    def save(self, account): self.rows[account.id] = account

    def list(self, status=None):
        return [a for a in self.rows.values() if status is None or a.status.value == status]

    def count_active_administrators(self):
        return sum(1 for a in self.rows.values() if a.is_active_administrator)


class FakeAudit:
    def __init__(self):
        self.rows: list[tuple[str | None, str, str, str | None, datetime]] = []

    def record(self, actor_id, action, target_id, reason, at): self.rows.append((actor_id, action, target_id, reason, at))
    def entries(self): return [dict(zip(("actor_id", "action", "target_id", "reason", "at"), r)) for r in self.rows]
