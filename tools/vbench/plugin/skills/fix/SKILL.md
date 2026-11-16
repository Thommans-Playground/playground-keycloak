---
name: fix
description: Short form of /vbench:v-fix, which does exactly the same. Fix a confirmed bug or make a small unplanned change while keeping it traced to a UC: failing test first, smallest change, spec updated if behaviour changed.
disable-model-invocation: true
argument-hint: <bug description | UC-id>
---

# /vbench:fix: short for /vbench:v-fix

**Why this step:** a short name for a step you run often; it is the same step, with nothing added or left out.

Read `../v-fix/SKILL.md` and follow it exactly, with `$ARGUMENTS` as its input. Its `scripts/` and `references/`
paths are relative to that skill's directory, not this one's. Keep any edit to the workflow in that file, never here,
so the two names cannot drift.
