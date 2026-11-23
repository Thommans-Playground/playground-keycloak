---
name: vbench-next
description: The front door to the harness. Reads the V cycle trace and says, in plain words, where each use case is and the one next step, in three moments (say what, say the shape, build). Use whenever the user says "what next", "what is next", "where am I", "where do I start", "what is the next step", "status of the V", "start here", "I am lost", or does not know which skill to run, even if they never say "vbench".
---

# vbench-next

Always know where you are. Everything lands on the V; one glance tells you where you are, what your change touches and
what is next. Simple on the surface, rigorous underneath: you see three moments, say what, say the shape, build.

**Why this step:** about thirteen skills and eight agents are too many to choose from, so this one chooses for you. It
reads the trace of `vbench-vcycle`, takes the first failing row (else the first warning), and names one next step.

## The command

`python3 .claude/skills/vbench-next/scripts/next_tool.py` from the repo root, add `--json` for data:

```
next_tool.py next [UC-A1]   the one next step (no id: the use case that most needs attention)
next_tool.py all            every use case, its moment and next step, worst first
```

The three moments: SAY WHAT (`/vbench-req`, `/vbench-at`), SAY THE SHAPE (`/vbench-uc`, then the three reviewers),
BUILD (`/vbench-tdd`, then prove it with `/vbench-test-stack`, try to break it with `/vbench-security-test`, then the
owner reviews and stamps).

## Steps

1. Run `next_tool.py next` (or `next UC-xx`, or `all` for the whole picture). Show the output as it is.
2. Say where they are in a line: the moment, the use case, the reason quoted from the trace.
3. Offer the one next step and its exact command. Run it only after a yes. Ask once per moment, not once per
   sub-step: one yes covers the skill and the steps it names (for example `/vbench-at` then `/vbench-tdd`).
4. Say how many warnings remain. No failure is not done; "Nothing is open" appears only when every row is ok.
5. When a step is the owner's (the review row), say so, and stop. Do not do it for them.
6. After the step, run the tool again so they see the next one.

## Boundaries

- Reads only. It writes nothing and edits no requirement, criterion, use case or test file.
- Never runs a stamp or a freeze, and never offers to: reading the diffs and stamping are the owner's.
- Does not judge: unknown statuses and unknown levels in the trace are skipped, and a `tier` header (small or full)
  is shown but changes nothing.
- It routes to other skills; the facts live in `/vbench-vcycle`, the table of all use cases in `/vbench-status`.
