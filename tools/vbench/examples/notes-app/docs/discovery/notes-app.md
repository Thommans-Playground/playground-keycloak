# Discovery: A small notes app

> **What this is.** The analysis done before any requirement exists. `/vbench:discovery` interviews you and
> fills this in, so the understanding survives the chat (`vbench new discovery --title "..."` creates the file).
> It starts as `draft`; read it, correct it, and set Status to `approved`. Then `/vbench:v-1-requirements` turns
> it into requests (`STK-REQ`), requirements (`REQ-FR`, `REQ-NFR`) and use cases.

| Field | Value |
|---|---|
| **Status** | approved |
| **Date** | 2026-11-06 |
| **Raised by** | STK-PER-001, the author |

## Problem
The author keeps losing small pieces of text (shopping lists, meeting points, half ideas) because they are scattered
across files and chats. They want one place to write a note, find it again and correct it.

## Actors
| Actor | Goal |
|---|---|
| Author | Write a note, read it later, fix it when it is wrong. |

## Vocabulary
> New or contested terms only; the settled glossary lives in the requirements doc.

| Term | Definition |
|---|---|
| Note | A piece of text the author keeps, with an optional title and a body. |
| Body | The text of a note. Required, at most 100 KB. |

## Scope
- **In:** creating a note, reading one by its id, editing its title or body.
- **Out:** deleting, sharing, searching, sign-in, and long-term storage. Each is a separate idea for later.

## Assumptions and constraints
- One author, so there is no sign-in and no permissions to design.
- Notes are plain text. Formatting and attachments are not needed yet.
- Notes live in memory for now; keeping them across a restart is recorded as a requirement (durability) but is not built.

## Decisions
> From the interview. Each with the reason, so it can be revisited.

| # | Decision | Because |
|---|---|---|
| D1 | Three use cases: create, read, edit, in that order. | Read needs a note to exist, and edit needs to read one first. |
| D2 | A body is required; a title is optional. | A note with no text is meaningless, but people often skip titles. |
| D3 | Cap the body at 100 KB. | One note must not be able to exhaust memory. |

## Open questions
| # | Question | Who can answer |
|---|---|---|
| Q1 | Should notes survive a restart? | The author. Recorded as a requirement; no use case builds it yet. |

## Becomes
> Filled in by `/vbench:v-1-requirements` once the brief is approved.

| Kind | Ids |
|---|---|
| Requests | STK-REQ-001 |
| Functional / non-functional | REQ-FR-001, REQ-FR-002, REQ-FR-003, REQ-NFR-001, REQ-NFR-002 |
| Use cases | UC-N-001, UC-N-002, UC-N-003 |
