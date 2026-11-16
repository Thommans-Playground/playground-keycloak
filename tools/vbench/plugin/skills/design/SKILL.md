---
name: design
description: Short form of /vbench:v-2-design, which does exactly the same. V-model step 2 (left arm, system / architecture / module). Design an approved UC using DDD and hexagonal architecture, with GoF patterns only where a force demands them, sized by a rigor tier, and commit each level to the test that will verify it. Writes no code.
disable-model-invocation: true
argument-hint: <UC-id> [system|arch|module] [light|standard|full]
---

# /vbench:design: short for /vbench:v-2-design

**Why this step:** a short name for a step you run often; it is the same step, with nothing added or left out.

Read `../v-2-design/SKILL.md` and follow it exactly, with `$ARGUMENTS` as its input. Its `scripts/` and `references/`
paths are relative to that skill's directory, not this one's. Keep any edit to the workflow in that file, never here,
so the two names cannot drift.
