# UC-N-001 - Create note

> **Use-case specification.** **Code is the source of truth.**

| Field | Value |
|-------|-------|
| **Use Case ID** | UC-N-001 |
| **Bounded context** | Notes |
| **Primary actor** | Author |
| **Rigor** | standard |
| **Maturity** | ✅ built and verified |
| **Realises** | REQ-FR-001, REQ-NFR-002 |
| **Epic** | EPC-N-001 |
| **Depends on** | - |
| **Diagrams** | [sequence](UC-N-001-create-note-sequence.puml), [state](UC-N-001-create-note-state.puml) |
| **Lifecycle** | yes |
| **ADRs** | - |

## Description
The author saves a new note, with an optional title and a body, so they can come back to it later.

## Preconditions
- The author has the notes app open.

## Main flow
1. The author enters a body, and optionally a title.
2. They save.
3. The system validates the body, stores the note, and returns it with an id and its timestamps.

## Alternative & exception flows
- **Empty body:** the system refuses the note and says the body is required.
- **Body over 100 KB:** the system refuses the note and says how large the limit is.

## Postconditions
- The note exists with a new id, `created_at` and `updated_at` set to the same instant.

## Acceptance criteria

| AC id | Given / when / then | Satisfies |
|---|---|---|
| **AC-N-001** | Given a title and a body, when the author saves, then the note is stored with an id and both timestamps. | REQ-FR-001 |
| **AC-N-002** | Given an empty or blank body, when the author saves, then nothing is stored and the reason names the body. | REQ-FR-001 |
| **AC-N-003** | Given a body over 100 KB, when the author saves, then nothing is stored and the reason gives the limit. | REQ-NFR-002 |

## Design decisions
- **D1.** `Note` is the one aggregate. Its invariants (body present, at most 100 KB) are checked on creation, so an invalid note cannot exist. Force: every other use case reads or changes a `Note`.
- **D2.** A `NoteRepository` port, with an in-memory adapter for now. Force: the tests need a fake, and persistence (REQ-NFR-001) is a later use case.
- **D3.** `Note` has a lifecycle (Draft, then Saved, with edits while Saved), so it gets a state diagram.

## Verification plan
| AC | Test | Rung |
|---|---|---|
| AC-N-001 | `tests/test_create_note.py` | acceptance |
| AC-N-002 | `tests/test_create_note.py` | unit |
| AC-N-003 | `tests/test_create_note.py` | unit |

## Delivery tasks

| Task id | Description | Closes ACs | Steps |
|---|---|---|---|
| **TSK-N-001** | A note refuses an empty or oversized body | AC-N-002, AC-N-003 | STP-N-003 |
| **TSK-N-002** | Creating a note stores it with an id and timestamps | AC-N-001 | STP-N-001, STP-N-002, STP-N-004, STP-N-005 |

## Known gaps
- Notes are kept in memory, so they do not survive a restart (REQ-NFR-001 is not yet realised by any use case).
