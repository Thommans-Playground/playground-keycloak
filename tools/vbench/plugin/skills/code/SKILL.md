---
name: code
description: Short form of /vbench:v-3-code, which does exactly the same. V-model step 3 (the vertex). Build an approved, designed UC task by task with strict double-loop TDD: a failing acceptance test first, then red-green-refactor at the unit rung, then integration and system tests as seams appear.
disable-model-invocation: true
argument-hint: <UC-id> [TSK-id]
---

# /vbench:code: short for /vbench:v-3-code

**Why this step:** a short name for a step you run often; it is the same step, with nothing added or left out.

Read `../v-3-code/SKILL.md` and follow it exactly, with `$ARGUMENTS` as its input. Its `scripts/` and `references/`
paths are relative to that skill's directory, not this one's. Keep any edit to the workflow in that file, never here,
so the two names cannot drift.
