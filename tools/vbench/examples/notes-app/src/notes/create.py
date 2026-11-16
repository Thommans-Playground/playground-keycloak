"""Create a note and keep it through a repository port.

Realises UC-N-001 · Spec: docs/usecase-diagrams/UC-N-001-create-note.md
"""

from __future__ import annotations

from typing import Protocol

from .note import Note


class NoteRepository(Protocol):
    def add(self, note: Note) -> None: ...


class InMemoryNotes:
    """The adapter used until persistence (REQ-NFR-001) is built."""

    def __init__(self) -> None:
        self.items: dict[str, Note] = {}

    def add(self, note: Note) -> None:
        self.items[note.id] = note


def create_note(repo: NoteRepository, title: str | None, body: str) -> Note:  # Realises UC-N-001 · STP-N-001
    note = Note.create(title, body)  # Realises UC-N-001 · STP-N-002 (raises InvalidNote before anything is stored)
    repo.add(note)  # Realises UC-N-001 · STP-N-004
    return note  # Realises UC-N-001 · STP-N-005
