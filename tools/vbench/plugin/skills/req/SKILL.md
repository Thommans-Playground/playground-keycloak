---
name: req
description: Short form of /vbench:v-1-requirements, which does exactly the same. V-model step 1 (left arm, top). Turn an idea, a `STK-REQ`/`REQ-FR` id, or an existing UC into an approved requirement-level spec with testable acceptance criteria, relevant NFRs, and a decision to create or update a use case. Writes no code.
disable-model-invocation: true
argument-hint: <idea | STK-REQ-/REQ-FR-/UC- id>
---

# /vbench:req: short for /vbench:v-1-requirements

**Why this step:** a short name for a step you run often; it is the same step, with nothing added or left out.

Read `../v-1-requirements/SKILL.md` and follow it exactly, with `$ARGUMENTS` as its input. Its `scripts/` and `references/`
paths are relative to that skill's directory, not this one's. Keep any edit to the workflow in that file, never here,
so the two names cannot drift.
