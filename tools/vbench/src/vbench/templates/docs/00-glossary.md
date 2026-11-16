# Glossary

Plain meanings for the words this method uses. **Level** says when you are likely to meet the word (see
[getting started](00-getting-started.md)): 0 straight away, 1 when a check first complains, 2 only when a use case
needs it.

## The cycle

| Term | In plain words | Level |
|---|---|---|
| **V-cycle** | The order of work: say what you want, plan it, build it, then prove it, with each thing you specified paired with a check that proves it. Drawn as a V. | 0 |
| **Phase** | One of the nine places on the V: requirements, system design, architecture, module design, code, and unit, integration, system and acceptance tests. The dashboard lists each phase's items and shows the V any item belongs to. | 0 |
| **Use case** | One thing a person can do with the product, from start to finish ("create a note"). It is the unit you plan, build and ship. | 0 |
| **Approval gate** | A point where the agent stops and waits for your yes before the next step. | 0 |
| **Discovery** | Agreeing the scope before writing requirements: who it is for, what is in, what is out. Saved as a brief. | 0 |
| **Stage** | Where a use case is right now: requirements, design, code, closing tests, or built. `vbench status` shows it. | 0 |
| **Wave** | A use case's place in the build order. Wave 0 depends on nothing, wave 1 on wave 0, and so on. | 0 |
| **Next step** | The one thing to do now, worked out from the files. `vbench next`, or `/vbench:next` to do it. | 0 |
| **Rigor tier** | How much design a use case gets: light (a few lines), standard (adds a sequence diagram), full (adds a class diagram, a domain model and a decision record). Start light. | 1 |

## What you write

| Term | In plain words | Level |
|---|---|---|
| **Problem** | What someone struggles with, from their side, with no solution in it, and what leaving it costs them (`STK-PRB-001`). There can be several. Each request names the problem it addresses, so a problem nobody has asked about yet is easy to see. | 0 |
| **Request, FR, NFR** | A stakeholder's ask in their own words (`STK-REQ-001`), a thing the system must do (`REQ-FR-001`, functional, with a user story), and how well it must do it (`REQ-NFR-001`, non-functional, such as "a note body is at most 100 KB", written as a six-part scenario). | 0 |
| **Acceptance criterion (AC)** | One checkable sentence: given a situation, when something happens, then this is observable. A use case is done when every criterion has a passing test. | 0 |
| **Task** | A small, commit-sized piece of a use case that ends with a passing test. Listed in the use case's task table. | 0 |
| **Step** | One numbered message of a use case's sequence diagram, with an id like `STP-N-002`. A task cites the steps it builds, the code that realises one says `Realises UC-N-001 · STP-N-002`, and the test that drives it says `Verifies UC-N-001 · STP-N-002 · unit rung.` `vbench trace UC-N-001` reads the chain back. | 2 |
| **Ontology** | The project's artifacts, ids, contexts and vocabulary written as facts (what realises what, which term is not which). `vbench ontology` derives it as OWL (Turtle or RDF/XML), JSON-LD or YAML; it is never edited by hand. | 2 |
| **Id** | The three-part name of an artifact, `<KIND>-<SCOPE>-<NNN>`: `REQ-FR-001`, `UC-A-001`, `AC-A-004`, `TSK-A-002`. Written once, never changed or reused. The first part says what it is, the second where it belongs, the third is a number. | 0 |
| **Id registry** | The table in `00-id-registry.md` that gives an id to everything that is found in the repo rather than written: contexts, models, diagrams, code files and tests (`COD-SRC-001`, `TST-UNT-001`). `vbench sync` only ever adds rows. | 1 |
| **User story** | One sentence that says why a functional requirement exists: *As a <role>, I want <goal> so that <benefit>*. The requirement says what, the story says why, the acceptance criteria say how you will know it is done. | 0 |
| **Quality attribute scenario** | A non-functional requirement written in six parts so it can be checked: source, stimulus, artifact, environment, response, response measure. "Fast" is not one; "a search of 10,000 notes finishes in under 150 ms" is. | 1 |
| **Spec** | The file for one use case: its actor, criteria, design decisions and tasks. | 0 |
| **Depends on** | The use cases that must be built before this one. The only place order is written; everything else is worked out from it. | 1 |
| **Decision record (ADR)** | A short note of an important choice and why, kept so nobody has to guess later. Only for choices that are expensive to reverse. | 2 |

## Building and proving

| Term | In plain words | Level |
|---|---|---|
| **TDD (test first)** | Write a test, watch it fail, write the least code that passes, then tidy up. A test you saw fail is one whose pass means something. | 0 |
| **Tag** | A plain-text label that ties code or a test to a use case: `Realises UC-N-001` on code, `Verifies UC-N-001 · unit rung.` on a test, plus the criterion's marker. The checks read these; in Python a tag counts only in a docstring, and the marker only on a real test (one that asserts something and is not skipped). | 1 |
| **Rung** | One level of proof, from smallest to largest: unit, integration, system, acceptance. A use case is "closed" at a rung when a test at that level verifies it. | 1 |
| **Gate** | An automatic check that fails when something is missing: `refs` (links resolve), `rungs` (code has a verifying test), `acs` (each criterion has a test), `links` (use-case order is valid), `diagrams`, `steps` (each numbered diagram message has a task, code and a test), `vocabulary` (no diagram draws a word the vocabulary rules out), `ontology` (generated ontology files match the project), `docs` and `commits`. A project's own checks (tests, lint, format, types and `boundaries`, the architecture rules) are gates too. Run by `vbench check`, by `run_gates.py` and in CI. | 1 |
| **Verify** | The independent re-check of a built use case, read-only, by someone who did not write it. | 1 |
| **Commit format** | Conventional Commits with the ids as the scope, `type(UC-id[/TSK-id]): description`, for example `feat(UC-N-001/TSK-N-001): reject an empty body`. It makes every commit traceable to a use case and a task. | 1 |

## Design words

| Term | In plain words | Level |
|---|---|---|
| **Bounded context** | A part of the product with its own words and rules (Notes, Sharing). Most small projects have one. | 2 |
| **Aggregate** | A group of things that must stay consistent together, with one of them in charge (a `Note`). | 2 |
| **Port and adapter** | A port is what the core needs from outside (a way to keep notes); an adapter is one way of providing it (in memory, a database). | 2 |
| **Context map** | A picture of how bounded contexts relate. Needed only once there are two or more. | 2 |
| **Domain model** | The picture of one context's aggregates and the words they use. | 2 |
| **Sequence diagram** | Who calls whom, in order, for one use case. | 1 |
| **State diagram** | The states a thing can be in and what moves it between them. Drawn only when a thing has a lifecycle. | 2 |

## The tool

| Term | In plain words | Level |
|---|---|---|
| **Stack standard** | The default technology choices (FastAPI, PostgreSQL, uv, Ruff, mypy and the layout around them), written down as decision records so designs can be checked against them. You may depart from one with a new decision record. | 1 |
| **Ruff** | One tool that both lints and formats the Python code. There is no separate formatter. | 1 |
| **Harness** | The tool as a whole: it guides and checks the work but does not do it for you. | 0 |
| **Skill** | A set of instructions the agent follows for one step, started with a slash command such as `/vbench:next`. | 0 |
| **Generated block** | Text between `vbench:begin` and `vbench:end` markers that `vbench sync` rewrites from the use-case files. Do not edit inside it; change the use case instead. | 1 |
| **Derived** | Worked out from the files each time, never stored. Progress, order and the next step are derived, so they cannot go out of date. | 1 |
| **Authored** | Written by a person or an agent with a person's approval: criteria, design decisions, the requirements text. | 1 |
