# UC-X-nnn - <Title>

> **Use-case specification.** **Code is the source of truth.**

| Field | Value |
|-------|-------|
| **Use Case ID** | UC-X-nnn |
| **Bounded context** | (context) |
| **Primary actor** | (actor) |
| **Rigor** | <rigor> |
| **Maturity** | ⚪ specified only |
| **Realises** | (REQ-FR-/REQ-NFR- ids) |
| **Epic** | (EP- id) |
| **Depends on** | - |
| **Diagrams** | - |
| **Lifecycle** | (yes or none) |
| **ADRs** | - |

> **Diagrams** links this use case's PlantUML files, named after the spec: `UC-X-nnn-<slug>-sequence.puml`,
> `-class.puml` and `-state.puml` (`-sequence.2.puml` for a second flow). The rigor tier says which are required
> (standard: sequence; full: sequence and class); a state diagram is added at any tier when the Lifecycle row below is
> `yes`. `vbench check diagrams` enforces the names, the links and the required set. Number each message of the sequence
> diagram with a step id (`STP-X-nnn`, from `vbench id step --area X`); `vbench check steps` then wants every step cited by a
> task and, once there is code, tagged `Realises UC-X-nnn · STP-X-nnn` and driven by a test, and `vbench trace UC-X-nnn` reads it back.
>
> **Lifecycle** says whether something in this use case moves through states: `yes` means the state diagram
> (`-state.puml`) is required, at any tier; `none` means there is no lifecycle and says so. The full tier needs the
> decision made, so `vbench check diagrams` fails while it is still a placeholder.
>
> **Depends on** lists the use cases that must be built first (`UC-A-001, UC-A-002`, or `-`). It is the only place
> dependencies are written; `vbench check links` validates it, and `vbench status` / `vbench next` derive the
> build order, the waves and what each use case enables from it. A row marked `TBD` is not yet specified.

## Description
(One paragraph: what the actor achieves and why.)

## Preconditions
- (what must be true before)

## Main flow
1. (step)

## Alternative & exception flows
- (flow: what happens, and what the actor sees)

## Postconditions
- (what is true after)

## Acceptance criteria

Each criterion has a stable id and cites the requirement it satisfies. The AC -> test mapping is derived
from the markers on the tests, not hand-listed here (`vbench check acs --matrix`). Mark a criterion for a
not-yet-built flow with `(planned)` in its row.

| AC id | Given / when / then | Satisfies |
|---|---|---|
| **AC-X-nnn** | TBD: Given (state), when (action), then (observable outcome). | (REQ-FR-nnn) |

## Design decisions
(Standard and full tiers: D1…Dn with the force behind each choice.)

## Verification plan
(Standard and full tiers: each AC -> planned test file and rung.)

## Delivery tasks

One row per commit-sized task, each ending in a passing test. Commits cite them (`feat(UC-X-nnn/TSK-X-nnn): …`),
so add the row before the commit that uses it. **Steps** names the sequence-diagram steps the task builds (`STP-X-nnn`); a task is one step or a few adjacent ones, built with TDD. A task is closed when every AC it names has a marked test
(`vbench status` shows it), so there is no status column to keep in step.

| Task id | Description | Closes ACs | Steps |
|---|---|---|---|
| **TSK-X-nnn** | (what this task delivers) | (AC ids) | (STP ids) |

## Known gaps
- (what is not built, or not verified)
