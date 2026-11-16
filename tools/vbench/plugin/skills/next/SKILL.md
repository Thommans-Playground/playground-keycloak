---
name: next
description: Do the one next step of the V-cycle. Asks `vbench next` which command is due (it knows the build order of the use cases and what each has and lacks), then performs that step and stops at its approval gate. Use when you want to be carried through the cycle one turn at a time instead of choosing the step yourself.
disable-model-invocation: true
argument-hint: [UC-id | an idea, when there are no use cases yet]
---

# /vbench:next: one turn of the V-cycle

**Why this step:** one command that always knows the next step, so nobody has to memorise the sequence.

One invocation is one turn: find the due step, do it, stop at its gate. Nothing is stored; the answer is derived
from the specs, tags and tests, so running it again always lands in the right place.

## Steps
1. **Ask the CLI, do not guess.** Run `vbench next --json`. It returns `command`, `uc`, `why`, `purpose` and `blocked`
   (exit 1 with a null `command` means nothing can proceed).
   If `$ARGUMENTS` is a use case id, run `vbench status $ARGUMENTS --json` instead and take that use case's `next` field.
   No `vbench` on the PATH but a `vbench` MCP server configured (the Docker setup)? Use its `next_step` and `status`
   tools; they return the same facts.
   If `$ARGUMENTS` is a free-text idea and there are no use cases yet, the step is `discovery` with the idea as its
   input.
2. **Say it in three short lines.** The command, the use case (and task), and the reason, then the `purpose` field from
   `vbench next`, which says why this step exists. The reader may be new to the method, so keep it plain. They can
   stop here and run a different step by hand; that is their call.
3. **Do that step.** Read the matching skill file in the sibling directory (`../discovery/SKILL.md`, `../v-1-requirements/SKILL.md`,
   `../v-2-design/SKILL.md`, `../v-3-code/SKILL.md`, `../v-4-verify/SKILL.md`, `../v-5-ship/SKILL.md`) and follow it
   exactly for that use case and task: its preconditions, its rules, and its approval gate.
4. **Stop at the gate.** Do not start the following step in the same turn. After the step, run `vbench next` once
   and show what is due after this, so the user knows what the next invocation will do.

## When nothing can proceed
`vbench next` exits 1 with no command when every remaining use case is blocked. Run `vbench check links`, show the
dangling id or the cycle, and ask the user which `Depends on` row to fix. Do not pick for them.

## Rules
- One step per turn. Never chain two skills, and never skip a gate to "save a turn".
- If a step's precondition fails (an unapproved spec, a missing design), say so and follow that skill's own
  back-edge rather than working around it.
- This skill decides nothing about the product. It only routes; the approvals stay with the user.

## Connections
- Reads: `vbench next`, `vbench status`, the use-case specs.
- Calls (by reading their files): `discovery`, `v-1-requirements`, `v-2-design`, `v-3-code`, `v-4-verify`, `v-5-ship`.
- Not a replacement for `/vbench:v-status`, which reports without acting.
