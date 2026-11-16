# 00 - Requirements Engineering

> **What this is.** The single place that records who wants what and why. It goes breadth first, then depth on
> what survives prioritisation. Ids are append-only (see [naming conventions](00-naming-conventions.md));
> `/vbench:v-1-requirements` and the `requirements-engineering` skill keep it honest. Delete the guidance
> lines (the quoted ones) as you fill each section.

## 0. Problems

> What people struggle with, from their side of the glass, with no solution in it. One row per problem. Who is
> affected and what leaving it costs are what make it worth solving. If you cannot write one, you are not ready to
> write requirements. A discovery brief (`vbench new discovery`) is where they are worked out; the agreed ones land
> here, and each request in §1.2 names the problem it addresses.

| ID | Problem | Who is affected | Cost of leaving it |
|----|---------|-----------------|--------------------|
| **STK-PRB-001** | Small pieces of text (shopping lists, meeting points, half ideas) end up scattered across files and chats. | The author | They write the same thing twice, or never find it again. |
| **STK-PRB-002** | Once there are many notes, finding one means opening them all. | The author | Time is lost, and ideas are abandoned because they are too slow to get back to. |
| **STK-PRB-003** | A note saved over by mistake loses what it said before. | The author | Work is lost for good, and the author stops trusting the notes. |

## 1. Stakeholders and requests

> Who cares, and what they asked for in their own words. A stakeholder has an interest; an actor interacts with
> the system. Not every stakeholder is an actor.

### 1.1 Stakeholder register

| ID | Stakeholder | Type | Interest |
|----|-------------|------|----------|
| **STK-PER-001** | The author | Primary actor | Keeps notes and finds them again without friction. |

### 1.2 Raw requests

| ID | Raised by | Problem | The ask, in their words |
|----|-----------|---------|-------------------------|
| **STK-REQ-001** | STK-PER-001 | STK-PRB-001 | "I want to keep notes: write one, read it later, and fix it when I got something wrong." |
| **STK-REQ-002** | STK-PER-001 | STK-PRB-002 | "When I have a lot of notes I want to find the one I mean without opening them all." |

## 2. Vocabulary (ubiquitous language)

> One definition per term, no synonyms. Code, tests and acceptance criteria use these words.

| Term | Definition | Context | Not to be confused with |
|------|------------|---------|-------------------------|
| Note | A piece of text the author keeps, with an optional title and a body. | Notes | Document, memo |
| Body | The text of a note. It is required and at most 100 KB. | Notes | Content, text |
| Author | The one person who writes and reads their notes. | Notes | User |

## 3. System context

> What is inside the boundary and what is outside it.

- **Inside:** creating, reading and editing a note.
- **Outside:** sign-in, sharing, search, deleting, and where notes are stored long term.

| Actor / external system | Direction | What crosses the boundary |
|---|---|---|
| Author | in | A title and a body to save, an id to read, changes to apply |

## 4. Functional requirements (outline)

> Everything the system must *do*, one line each. Breadth before depth. Group by bounded context. Maturity is
> derived from the code: ✅ built and verified, 🟡 partial, ⚪ specified only. Each requirement has a user
> story, the *why* in one sentence: `As a <role>, I want <goal> so that <benefit>`. Its Given/When/Then
> criteria, the *done*, are written in §7.

| ID | Functional requirement | User story | Satisfies | UC | Maturity |
|----|------------------------|------------|-----------|----|----------|
| **REQ-FR-001** | The system shall let the author create a note from a body and an optional title. | As an author, I want to save a note with an optional title so that I do not lose it. | STK-REQ-001 | UC-N-001 | ✅ |
| **REQ-FR-002** | The system shall let the author read a saved note by its id. | As an author, I want to open a note I saved so that I can use what I wrote. | STK-REQ-001 | UC-N-002 | ⚪ |
| **REQ-FR-003** | The system shall let the author edit the title or body of a saved note. | As an author, I want to correct a saved note so that it stays right. | STK-REQ-001 | UC-N-003 | ⚪ |

## 5. Non-functional requirements (outline)

> The qualities, not the behaviour: security, privacy, performance, availability, auditability, observability,
> accessibility, retention. Name and scope them here; the measurable scenario goes in §8.

| ID | Quality | Requirement (outline) | Satisfies | Evidence / ADR |
|----|---------|------------------------|-----------|----------------|
| **REQ-NFR-001** | Durability | A saved note is still there after the application restarts. | STK-REQ-001 | none yet |
| **REQ-NFR-002** | Input limits | A note body is at most 100 KB, so one note cannot exhaust memory. | STK-REQ-001 | UC-N-001 |

## 6. Prioritise

> MoSCoW. A Won't is a decision with a trigger ("when we would build it"), not an omission.

| Priority | Requirements | Rationale |
|----------|--------------|-----------|
| **MUST** | (ids) | (the product cannot exist without these) |
| **SHOULD** | (ids) | (high value, shipped after the core) |
| **COULD** | (ids) | (low regret if absent) |
| **WON'T** (this release) | (ids) | (deferred on purpose, and the trigger to revisit) |

## 7. Detail the functional requirements

> A requirement is done when its **acceptance criteria** pass. Each is a Given/When/Then row (`AC-<area>-<nnn>`)
> in the spec of the use case that realises the requirement, next to the flows, pre- and post-conditions and
> alternates, and names the requirement it satisfies. The story above says why; the criteria say what is observable.
> This map from use case to requirement to spec is generated from each spec's *Realises* row (edit the spec, then run `vbench sync`), so a
> requirement cannot go unowned and the map cannot go stale.

<!-- vbench:begin fr-map -->
| Use case | Realises | Spec |
|---|---|---|
| **UC-N-001** Create note | REQ-FR-001, REQ-NFR-002 | [UC-N-001-create-note.md](usecase-diagrams/UC-N-001-create-note.md) |
| **UC-N-002** Read note | REQ-FR-002 | [UC-N-002-read-note.md](usecase-diagrams/UC-N-002-read-note.md) |
| **UC-N-003** Edit note | REQ-FR-003 | [UC-N-003-edit-note.md](usecase-diagrams/UC-N-003-edit-note.md) |
<!-- vbench:end fr-map -->

## 8. Detail the non-functional requirements

> Each quality becomes a **quality attribute scenario** someone can check. "Secure" and "fast" are not
> criteria: the *response measure* is the number, threshold or checkable yes/no. The six parts: who or what
> raises the event (source), the event (stimulus), the part of the system it hits (artifact), the state the
> system is in (environment), what the system does (response) and how that is measured (response measure). The v-1
> skill has a checklist of concerns and example scenarios.

| ID | Quality | Source | Stimulus | Artifact | Environment | Response | Response measure |
|----|---------|--------|----------|----------|-------------|----------|------------------|
| **REQ-NFR-001** | Durability | The operator | Restarts the application | The note store | After normal use, with notes saved | Every saved note can be read back | All saved notes are returned unchanged |
| **REQ-NFR-002** | Input limits | The author | Saves a note with a very large body | Note creation | Normal operation | Accepts a body at the limit and refuses one over it | A 100 KB body is accepted; 100 KB plus one byte is refused |

## 9. Fold into the architecture

> Which requirement forces which decision. The style, the logical view (contexts), the layering inside a
> context, and the data and integration views. Each load-bearing choice gets an
> [ADR](02-architecture-decision-record.md).

## 10. Review

| Date | Reviewer | Outcome |
|---|---|---|
| (YYYY-MM-DD) | (name) | (approved / changes requested) |
