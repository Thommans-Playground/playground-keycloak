---
name: ship
description: Short form of /vbench:v-5-ship, which does exactly the same. V-model step 5 (closure). Final gates before merge: full verification, independent review, and a PR draft with a traceability table. Asks before pushing or opening a PR.
disable-model-invocation: true
argument-hint: [base branch, default main]
---

# /vbench:ship: short for /vbench:v-5-ship

**Why this step:** a short name for a step you run often; it is the same step, with nothing added or left out.

Read `../v-5-ship/SKILL.md` and follow it exactly, with `$ARGUMENTS` as its input. Its `scripts/` and `references/`
paths are relative to that skill's directory, not this one's. Keep any edit to the workflow in that file, never here,
so the two names cannot drift.
