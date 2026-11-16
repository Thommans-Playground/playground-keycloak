"""The Note aggregate.

Realises UC-N-001 · Spec: docs/usecase-diagrams/UC-N-001-create-note.md
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

MAX_BODY_BYTES = 100 * 1024  # REQ-NFR-002


class InvalidNote(ValueError):
    """The body is missing or too large. The message names the body and, when relevant, the limit."""


@dataclass(frozen=True)
class Note:
    id: str
    title: str
    body: str
    created_at: datetime
    updated_at: datetime = field(compare=False)

    @staticmethod
    def create(title: str | None, body: str) -> Note:
        """An invalid note cannot be built: the invariants are checked here, once."""
        if not body or not body.strip():
            raise InvalidNote("The body is required.")  # Realises UC-N-001 · STP-N-003
        if len(body.encode("utf-8")) > MAX_BODY_BYTES:
            raise InvalidNote(f"The body is over the limit of {MAX_BODY_BYTES // 1024} KB.")
        now = datetime.now(UTC)
        return Note(
            id=f"note_{uuid.uuid4().hex[:12]}", title=(title or "").strip(), body=body, created_at=now, updated_at=now
        )
