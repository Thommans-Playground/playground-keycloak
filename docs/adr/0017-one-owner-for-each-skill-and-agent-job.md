# 0017 One owner for each skill and agent job

- Status: accepted
- Date: 2026-11-22
- Decided by: agent (technical); the scope of the V itself is unchanged

## Context
The skills and agents grew one at a time. Four read-only reviewers read all 18 skills and 7 agents against the
Automotive SPICE process groups (as a yardstick, not a conformance claim). They found jobs done in two places: the three
reviewers check the same diagrams and the same abuse cases; three skills write a failing test; four places report
status; `decisions.md` is written by three skills; two skills answer "is it already there?". They also found gaps
(test results, problem resolution, review findings, release) and broken references.

## Decision
Each job has one owner, written in `docs/standards/skills-and-agents.md` (eleven rules). No capability is removed: the
ledger `docs/standards/skills-and-agents-ledger.md` lists every script command and guard that must stay, and
`.claude/skills/_vbench/test_scope.py` fails when a skill or agent has no row in the map, a hand-off names something
that does not exist, or a ledger item has gone. A capability is removed on purpose only by deleting its ledger row in the
same commit. The skill and agent texts are changed to match in a separate step.

## Consequences
A new skill or agent needs a row in the map before it is added. Overlap is now a written rule instead of a surprise,
and the known gaps are listed, not hidden. The test checks that things exist and that nothing named is missing; it does
not judge whether a skill is good.

## Links
ADR 0005, 0008; CLAUDE.md ("Reviews", "Decisions"); `docs/standards/skills-and-agents.md`.
