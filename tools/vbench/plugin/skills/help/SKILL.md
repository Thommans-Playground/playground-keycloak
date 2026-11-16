---
name: help
description: List the /vbench commands (long and short forms) and say which one is due now. Read-only.
disable-model-invocation: true
argument-hint:
---

# /vbench:help: what can I run?

**Why this step:** one place to see every command and the one that matters now, so nobody has to remember the names.

1. Run `vbench next --json` (or the `next_step` tool of the `vbench` MCP server) and note `command`, `uc` and `why`.
2. Print this table, then the due step on top of it, in plain words:

| Command | Short | What it does |
|---|---|---|
| `/vbench:next` | | Does the one next step and stops for your approval |
| `/vbench:discovery` | | Interviews you about a new idea before any requirement |
| `/vbench:v-1-requirements` | `/vbench:req` | Turns an idea or id into a use case |
| `/vbench:v-2-design` | `/vbench:design` | Designs an approved use case |
| `/vbench:v-3-code` | `/vbench:code` | Builds it task by task with TDD |
| `/vbench:commit` | | Commits one finished task with a convention-perfect message |
| `/vbench:v-4-verify` | `/vbench:verify` | Re-verifies it rung by rung |
| `/vbench:v-5-ship` | `/vbench:ship` | Final gates before merge |
| `/vbench:v-fix` | `/vbench:fix` | A traced bug fix or small change |
| `/vbench:v-status` | `/vbench:status` | Where each use case is on the V |

3. Mention the terminal commands once: `vbench status`, `vbench next`, `vbench check`, `vbench id <kind>`, `vbench commit`, `vbench doctor`
   (short forms `st`, `n`, `c`).
4. Change nothing and run nothing else; offer `/vbench:next` to do the due step.
