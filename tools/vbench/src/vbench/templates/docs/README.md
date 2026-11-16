# Documentation Map

The engineering documentation for this product. **Code is the source of truth**: these docs are reconciled
against it, and `vbench check refs` fails CI when a link or a cited path stops resolving.

New here? Start with [getting started](00-getting-started.md), a 15-minute walkthrough, and keep the
[glossary](00-glossary.md) open. Then read in this order, which walks the left arm of the V from the top:
[methodology](00-engineering-methodology.md) → [requirements](00-requirements-engineering.md) →
[backlog and build order](01-backlog-epics-stories.md) → the [use-case specs](usecase-diagrams/_TEMPLATE.md).

## How the set is organised

Self-describing numbered files: **the number is the tier, the file name is the topic**. The id scheme itself is
in [naming conventions](00-naming-conventions.md).

| Tier | Meaning |
|---|---|
| `00-` | Foundational and cross-cutting: method, naming, requirements |
| `01`–`03` | Planning, decisions, practices |
| `04` | The technology stack, when the project uses the stack standard |
| `05`–`98` | Yours: system design (a use-case map, a context map, one tactical design per bounded context) |
| `99` | Retrospective |

## Catalogue

| Document | What it answers | Owner step |
|---|---|---|
| [Getting started](00-getting-started.md) | How do I begin, and what do I need to know first? | everyone |
| [Glossary](00-glossary.md) | What does this word mean? | everyone |
| [Engineering methodology](00-engineering-methodology.md) | How this product is built: the V, DDD, TDD, rigor tiers | all |
| [Naming conventions](00-naming-conventions.md) | What an id looks like and who allocates it | all |
| [Id registry](00-id-registry.md) | Which id does this code file, test, diagram or context have? (generated) | `vbench sync` |
| [Requirements engineering](00-requirements-engineering.md) | Who wants what: stakeholders, vocabulary, FRs, NFRs, priorities | `/vbench:v-1-requirements` |
| [Backlog, epics and use cases](01-backlog-epics-stories.md) | How the work is cut, what depends on what, in what order to build | `/vbench:v-1-requirements` |
| [Architecture decisions](02-architecture-decision-record.md) | Why the load-bearing choices were made (append-only) | `/vbench:v-2-design` |
| [Security practices](03-security-practices.md) | The defences in place and what is still pending | `/vbench:v-2-design` |
{{STACK_DOC_ROW}}
| [Problems and learnings](99-problems-encountered-and-learnings.md) | What went wrong and what we changed | anyone |

Folders:
- `discovery/`: one analysis brief per idea, written before any requirement and approved by you ([template](discovery/_TEMPLATE.md); `vbench new discovery` creates one).
- `usecase-diagrams/`: one spec per use case, plus its PlantUML sequence, class and state diagrams (named after the spec; the rigor tier says which are required). `_style.puml` and `_legend.puml` in the docs root are the shared includes.
- System diagrams, also in the docs root and named like MK3's: `08-usecase-diagrams.puml` (generated from the specs by
  `vbench sync`; do not edit), `09-context-ddd.puml` (the context map) and one `NN-<context>-ddd.puml` per bounded
  context (its domain model), created by `vbench new context`.
- `design-patterns/`: the patterns this codebase actually uses ([guide](design-patterns/README.md)).
- Add `diagrams/`, `integration/` or `tutorial/` when you need them; list them in the catalogue when you do.
