---
name: verify
description: Short form of /vbench:v-4-verify, which does exactly the same. V-model step 4 (right arm). Independently re-verify a UC rung by rung in ascending order (unit, integration, system, acceptance) and audit the quality of its tests. Read-only.
disable-model-invocation: true
argument-hint: <UC-id | all> [unit|integration|system|acceptance|all]
---

# /vbench:verify: short for /vbench:v-4-verify

**Why this step:** a short name for a step you run often; it is the same step, with nothing added or left out.

Read `../v-4-verify/SKILL.md` and follow it exactly, with `$ARGUMENTS` as its input. Its `scripts/` and `references/`
paths are relative to that skill's directory, not this one's. Keep any edit to the workflow in that file, never here,
so the two names cannot drift.
