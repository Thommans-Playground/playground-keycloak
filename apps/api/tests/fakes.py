"""In-memory stand-ins for the ports, so a use case can be tested with no database and no Keycloak."""


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

    def enable_user(self, identity):
        self._do("enable", identity)

    def disable_user(self, identity):
        self.events.append("disable_user")
        self._do("disable", identity)

    def end_sessions(self, identity):
        self._do("logout", identity)


class FakeAccounts:
    def __init__(self, events: list[str] | None = None):
        self.rows: dict[str, object] = {}
        self.events = events if events is not None else []

    def by_identity(self, identity):
        return next((a for a in self.rows.values() if a.identity == identity), None)

    def by_id(self, account_id):
        return self.rows.get(account_id)

    def by_ids(self, account_ids):
        return [self.rows[i] for i in dict.fromkeys(account_ids) if i in self.rows]

    def add(self, account):
        self.rows[account.id] = account

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
    """Stands in for Access's own AuditLog port: keeps the events Access built, with the names it passed."""

    def __init__(self):
        self.rows: list = []

    def record(self, event):
        self.rows.append(event)

    def entries(self):
        return [
            {
                "actor_id": e.actor.id if e.actor else None,
                "action": e.action,
                "target_id": e.target.id,
                "reason": e.reason,
            }
            for e in self.rows
        ]

    def shapes(self):
        """(actor id, action, target id, reason) for each event, in the order they were recorded."""
        return [(e["actor_id"], e["action"], e["target_id"], e["reason"]) for e in self.entries()]


class FakeAuditEntries:
    """Stands in for Audit's AuditEntries port. Like the database, it sets the time itself (RULE-L2)."""

    def __init__(self, clock=None):
        from datetime import UTC, datetime

        self.stored: list = []
        self._clock = clock or (lambda: datetime.now(UTC).replace(tzinfo=None))

    def add(self, entry):
        from app.audit.application.ports import RecordedEntry

        self.stored.append(RecordedEntry(len(self.stored) + 1, self._clock(), entry))

    def list_newest_first(self):
        return list(reversed(self.stored))


class FakeUnitOfWork:
    """Records commit() into an event list that can be shared with FakeIdp, to prove the order."""

    def __init__(self, events: list[str] | None = None):
        self.events = events if events is not None else []

    def commit(self):
        self.events.append("commit")


class FakeSecurityLog:
    """Records the security events, so a test can see what was raised. Satisfies both contexts' SecurityLog ports."""

    def __init__(self):
        self.events: list[dict] = []

    def event(self, name, result, person_id=None, session_id=None, reason=None):
        self.events.append(
            {"event": name, "result": result, "person_id": person_id, "session_id": session_id, "reason": reason}
        )


class FakeProjects:
    """Stands in for Projects' ProjectRepository port: keeps the projects in memory."""

    def __init__(self):
        self.rows: dict[str, object] = {}

    def add(self, project):
        self.rows[project.id] = project

    def by_id(self, project_id):
        return self.rows.get(project_id)
