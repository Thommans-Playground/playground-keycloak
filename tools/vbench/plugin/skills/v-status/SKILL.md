---
name: v-status
description: Show V-model progress derived from the repo itself (UCs, which ACs and rungs are closed, the gates, the current branch) and recommend the next /vbench command. Read-only.
disable-model-invocation: true
argument-hint: [UC-id | area letter]
---

# /vbench:v-status: where are we on the V?

**Why this step:** knowing exactly where you are makes the next step obvious.

Read-only and stateless: everything is derived from specs, tags and the gates, so it cannot go stale.
Input: `$ARGUMENTS` (optional UC id or area letter).

1. Run `python3 scripts/snapshot.py $ARGUMENTS` (path relative to this skill's directory). One call prints
   `vbench status` (each UC with its AC count, AC coverage, tasks closed / declared, whether code and a
   verifying test exist, and the gate results), the branch and working tree, the commits ahead of the base, and
   the commit-convention result.
2. For detail, run `vbench check rungs --matrix` and `vbench check acs --matrix`.
3. Report concisely: the branch and the UC(s) it touches; UCs with no verifying test or uncovered ACs; specs
   with no code; code tags with no spec; uncommitted work.
4. Recommend exactly one next command, with the UC id, taken from `vbench next` (it respects the use cases'
   build order). Offer `/vbench:next` to do it.

## Connections
- The router: it reads the state of the use case and points to the skill that produces the missing artifact.
