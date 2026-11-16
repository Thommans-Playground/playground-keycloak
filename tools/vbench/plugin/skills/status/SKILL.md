---
name: status
description: Short form of /vbench:v-status, which does exactly the same. Show V-model progress derived from the repo itself (UCs, which ACs and rungs are closed, the gates, the current branch) and recommend the next /vbench command. Read-only.
disable-model-invocation: true
argument-hint: [UC-id | area letter]
---

# /vbench:status: short for /vbench:v-status

**Why this step:** a short name for a step you run often; it is the same step, with nothing added or left out.

Read `../v-status/SKILL.md` and follow it exactly, with `$ARGUMENTS` as its input. Its `scripts/` and `references/`
paths are relative to that skill's directory, not this one's. Keep any edit to the workflow in that file, never here,
so the two names cannot drift.
