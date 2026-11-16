# Naming and ID Conventions

The first part says the **kind**; the letter says the **area**. Edit the area table to match your product.

## Areas

| Code | Area | Bounded context(s) |
|------|------|---------------------|
| A | Authentication / identity | (name them) |
| C | Core product | (name them) |

A new area gets the next free letter.

## Identifiers

Every id has **three parts**, `<KIND>-<SCOPE>-<NNN>`: what it is, where it belongs, a three-digit number. Ids are
written once and never change.

| Artifact | Pattern | Example |
|---|---|---|
| Stakeholder | `STK-PER-<nnn>` | `STK-PER-001` |
| Problem (what someone struggles with) | `STK-PRB-<nnn>` | `STK-PRB-002` |
| Stakeholder request (the raw ask) | `STK-REQ-<nnn>` | `STK-REQ-003` |
| Functional requirement | `REQ-FR-<nnn>` | `REQ-FR-012` |
| Non-functional requirement | `REQ-NFR-<nnn>` | `REQ-NFR-005` |
| Epic | `EPC-<area>-<nnn>` | `EPC-C-001` |
| Use case | `UC-<area>-<nnn>` | `UC-A-001` |
| Acceptance criterion | `AC-<area>-<nnn>` | `AC-A-004` |
| Delivery task | `TSK-<area>-<nnn>` | `TSK-A-002` |
| Architecture decision | `ADR-DEC-<nnn>` | `ADR-DEC-013` |
| Context, domain model, diagram, code file, test | `<AREA>-<KIND>-<nnn>`, from the id registry | `SYS-CTX-001`, `ARC-DOM-001`, `MOD-SEQ-001`, `COD-SRC-001`, `TST-UNT-001` |

The area letter is the code from the table above. Criteria and tasks are numbered per area, not per use case; each
belongs to the use case whose spec declares it. Requirements, decisions and requests are global: one requirement can
serve several use cases, and area-coding it would force a false owner.

**The id registry.** A context, a domain model, a diagram, a code file and a test are discovered in the repo, not
written, so they have no id of their own. `vbench sync` gives each one in `00-id-registry.md`, which lists the id
beside its alias (the file path, test function, or use case and diagram kind). The registry is only ever appended to:
a row is never rewritten and a number never reused. Renaming a file or a test is a new alias and gets a new id; the
old row stays as a record. The kind codes: `SYS-CTX` context, `ARC-DOM` domain model, `ARC-CLS` class diagram,
`MOD-SEQ` sequence diagram, `MOD-STA` state diagram, `COD-SRC` code file, `TST-UNT` / `TST-INT` / `TST-SYS` /
`TST-ACC` the unit, integration, system and acceptance tests, `TST-UNP` a test that names no level.

## Documents

The number is the tier, the file name is the topic (the map is `README.md` in the docs folder).

| Tier | Meaning |
|---|---|
| `00-` | Foundational and cross-cutting: method, naming, requirements |
| `01`–`03` | Planning, decisions, practices |
| `04`–`98` | Yours: system design, one tactical design per bounded context |
| `99` | Retrospective |

Discovery briefs are `discovery/<slug>.md` (kebab-case, one per idea). Retrospective entries are `L-<nn>`, newest first.

## Rules

1. **Append, never renumber.** Retire an id; do not reuse it. This keeps cross-document links from rotting.
2. **Allocate with the CLI** so numbers cannot collide: `vbench new uc --area A --title "…"` for a use case, and `vbench id fr|nfr|request|ac|task [--area A] [--count n]` to print the next free id of any other kind.
3. **Use case files** are `docs/usecase-diagrams/UC-<area>-<nnn>-<slug>.md`. Their PlantUML companions share the stem: `UC-<area>-<nnn>-<slug>-sequence.puml`, `-class.puml`, `-state.puml` (`-sequence.2.puml` for a second flow). Shared includes are `_style.puml` and `_legend.puml` in the docs root (leading underscore, no `@startuml`).
   System-level diagrams live in the docs root: `08-usecase-diagrams.puml` (generated; `vbench sync`), `09-context-ddd.puml` (context map) and `NN-<context-slug>-ddd.puml` for each bounded context, NN = 10, 20, ... (`vbench new context`).
4. If you change the id shapes, change `uc_pattern`, `ac_pattern` and `task_pattern` in `.vbench/config.toml` to match.
