---
name: vbench-status
description: A short report card of where the use cases stand on the V, as a table, on demand. One row for each use case (requirements with their criteria, design, slices, and what sits beside the V), or one use case in full with a layer to a row. Read-only; it lays the rows of vbench-vcycle onto the V and adds nothing of its own. Use whenever the user says "vbench-status", "status card", "report card", "where do we stand", "show the V", "which use cases need attention", or wants a quick look instead of the full vcycle trace, even if they never say "vbench".
---

# vbench-status

A report card for the V cycle: quick to read, and honest about what it does not know. It runs `vbench-vcycle` and lays its
levels onto the two sides of the V. It checks nothing itself, so for the facts behind a row use `/vbench-vcycle UC-xx`.

## The command

`python3 .claude/skills/vbench-status/scripts/card.py` from the repo root:

```
card.py            every use case, one row each
card.py UC-A7      one use case in full: a layer to a row, the specification beside its proof, and what the script says
```

The shape of each dot says the state, so the card reads the same with colour off: ● finished, ◐ in progress,
○ not started, ✕ failing.

## Steps

1. Run `card.py`, or `card.py UC-xx` if the person named a use case. Show the table as it is.
2. Say the next step for each ◐ and ✕ in one line, and who does it (an agent can write a test; only the owner freezes
   analysis and stamps a review). Name the skill: `/vbench-at`, `/vbench-tdd`, `/vbench-uc`, `/vbench-vcycle`.
3. Say what the card does not show: integration is not tracked by the script (shown as ○ not tracked, not as a
   state); the pairing of levels onto the V is an interpretation; a dot is "a test exists", not "it passes"
   (`/vbench-test-stack` runs them).

## Not the same as

- `/vbench-vcycle` is the full trace and the exit code. This is the short card over it.
- `vbench status --card` (the vbench tool) does the same for a project set up with `vbench init`; this repo is not one.
