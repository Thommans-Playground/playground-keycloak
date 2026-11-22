# 0019 Adopt the harness by strangling, not rewriting

- Status: accepted
- Date: 2026-11-22
- Decided by: agent (technical)

## Context
The harness was built inside one project and some of it is tied to that project (its Keycloak, its folder layout, its
design rules). To be useful elsewhere it has to enter projects that already have code, tests and habits, which nobody
will rewrite to fit a process.

## Decision
Adoption is incremental, one area at a time, like a strangler: observe, mark the seams, hold the line, make new work
follow the V, tighten an area when it is ready, retire the old way last. `vbench-adopt` owns it. Its tool `discover` only
reads: it writes no file, and proposes a `vbench.json` for a person to accept. The harness adapts through that config and
never changes the project's own files. The adoption states (`legacy`, `adopting`, `adopted`) and a baseline that lets
only new gaps fail are the next slice and are not built; the skill says so.

## Consequences
A project can start at step 0 in minutes and without risk, and gets value from each step alone. Until the trace reads the
adoption states, a gap in a legacy area is still shown as a gap. Packaging the generic skills as an installable plugin,
apart from the project-specific ones, is a separate step.

## Links
ADR 0017; `docs/standards/skills-and-agents.md`; the skill `vbench-adopt`.
