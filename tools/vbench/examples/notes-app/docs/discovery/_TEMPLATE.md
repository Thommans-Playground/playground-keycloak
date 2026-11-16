# Discovery: <idea>

> **What this is.** The analysis done before any requirement exists. `/vbench:discovery` interviews you and
> fills this in, so the understanding survives the chat (`vbench new discovery --title "..."` creates the file).
> It starts as `draft`; read it, correct it, and set Status to `approved`. Then `/vbench:v-1-requirements` turns
> it into requests (`STK-REQ`), requirements (`REQ-FR`, `REQ-NFR`) and use cases.

| Field | Value |
|---|---|
| **Status** | draft / approved |
| **Date** | (YYYY-MM-DD) |
| **Raised by** | (STK id or name) |

## Problem
(What is wrong or missing today, and for whom. One paragraph. No solution yet.)

## Actors
| Actor | Goal |
|---|---|
| (who) | (what they are trying to achieve) |

## Vocabulary
> New or contested terms only; the settled glossary lives in the requirements doc.

| Term | Definition |
|---|---|
| (term) | (one line) |

## Scope
- **In:** (what this covers)
- **Out:** (what it deliberately does not, so nobody assumes it)

## Assumptions and constraints
- (what we are taking as true, and what limits us: time, platform, data, people)

## Decisions
> From the interview. Each with the reason, so it can be revisited.

| # | Decision | Because |
|---|---|---|
| D1 | (what was decided) | (the reason) |

## Open questions
| # | Question | Who can answer |
|---|---|---|
| Q1 | (what is still unknown) | (person or evidence) |

## Becomes
> Filled in by `/vbench:v-1-requirements` once the brief is approved.

| Kind | Ids |
|---|---|
| Requests | REQ-… |
| Functional / non-functional | FR-…, NFR-… |
| Use cases | UC-… |
