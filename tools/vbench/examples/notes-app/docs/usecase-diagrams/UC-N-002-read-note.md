# UC-N-002 - Read note

> **Use-case specification.** **Code is the source of truth.**

| Field | Value |
|-------|-------|
| **Use Case ID** | UC-N-002 |
| **Bounded context** | Notes |
| **Primary actor** | Author |
| **Rigor** | light |
| **Maturity** | ⚪ specified only |
| **Realises** | REQ-FR-002 |
| **Epic** | EPC-N-001 |
| **Depends on** | UC-N-001 |
| **Diagrams** | - |
| **Lifecycle** | none |
| **ADRs** | - |

## Description
The author opens a note they saved earlier and reads its title and body.

## Preconditions
- At least one note exists (UC-N-001).

## Main flow
1. The author asks for a note by its id.
2. The system returns the note with its title, body and timestamps.

## Alternative & exception flows
- **Unknown id:** the system says no such note exists.

## Postconditions
- Nothing changes.

## Acceptance criteria

| AC id | Given / when / then | Satisfies |
|---|---|---|
| **AC-N-004** | Given a saved note, when the author asks for it by id, then the title, body and timestamps are returned unchanged. | REQ-FR-002 |
| **AC-N-005** | Given an id that was never issued, when the author asks for it, then the system reports that no such note exists. | REQ-FR-002 |

## Design decisions
(Standard and full tiers: D1…Dn with the force behind each choice.)

## Verification plan
(Standard and full tiers: each AC -> planned test file and rung.)

## Delivery tasks

| Task id | Description | Closes ACs |
|---|---|---|
| **TSK-N-003** | Look a note up by id, or report that it does not exist | AC-N-004, AC-N-005 |

## Known gaps
- Not built yet.
