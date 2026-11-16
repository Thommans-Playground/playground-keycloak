"""Verifies UC-N-001 · acceptance rung (the create flow) and unit rung (the Note invariants)."""

import pytest
from notes.create import InMemoryNotes, create_note
from notes.note import MAX_BODY_BYTES, InvalidNote, Note


@pytest.mark.ac("AC-N-001")
def test_a_saved_note_has_an_id_and_both_timestamps():
    """Verifies UC-N-001 · STP-N-001, STP-N-002, STP-N-004, STP-N-005 · acceptance rung."""
    repo = InMemoryNotes()
    note = create_note(repo, "Shopping", "milk, eggs")
    assert repo.items[note.id] == note
    assert note.id.startswith("note_") and note.created_at == note.updated_at


@pytest.mark.ac("AC-N-002")
@pytest.mark.parametrize("body", ["", "   ", "\n\t"])
def test_an_empty_or_blank_body_is_refused_and_nothing_is_stored(body):
    """Verifies UC-N-001 · STP-N-003 · unit rung."""
    repo = InMemoryNotes()
    with pytest.raises(InvalidNote, match="body is required"):
        create_note(repo, "Title", body)
    assert repo.items == {}


@pytest.mark.ac("AC-N-003")
def test_a_body_one_byte_over_the_limit_is_refused_and_the_limit_is_accepted():
    """Verifies UC-N-001 · STP-N-003 · unit rung."""
    assert Note.create(None, "x" * MAX_BODY_BYTES).body
    with pytest.raises(InvalidNote, match="100 KB"):
        Note.create(None, "x" * (MAX_BODY_BYTES + 1))
