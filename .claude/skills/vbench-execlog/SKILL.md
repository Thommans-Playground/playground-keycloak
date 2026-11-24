---
name: vbench-execlog
description: Write the execution log of a use case the standard way, a code-along for each slice. Turns one TSK slice into steps that each have one failing test and the code that passes it, puts the what and why in the chapter summary, and checks the task file with a script. Use whenever the user says "write the execution log", "document this task", "write up TSK-P1.x", "code along", "add a chapter", "convert the task files", or has just built a slice and wants the notebook written, even if they never say "vbench".
---

# Write an execution log

**Why this step:** a slice that is built but not explained is code nobody owns. The log is how someone follows the work at the
keyboard and understands why it is that way (ADR 0021, ADR 0022). Words are fixed:

- A **task** is one slice that can be built and tested on its own: a `TSK-` line of the use case's Slices.
- A **step** is one behaviour inside a task, with one failing test and the code that makes it pass. No test, no step.
- A test has a **level**: `Unit` (a rule, a use case or an adapter run in process, no HTTP), `API` (the real app through
  `TestClient`), `Integration` (needs a running stack or PostgreSQL), `Architecture` (the boundary tests).

## Steps

1. **Take one slice.** Read its line in the use case's Slices and its criteria. Work in
   `docs/execution-logs/<UC>/chapters/NNN-name/`. If the chapter does not exist, copy the shape of the UC-P1 one.
2. **List its behaviours.** One behaviour, one step. A bit of code with no test of its own (a one line call, wiring) is folded into
   the step whose test covers it. If a behaviour has no test, stop: write the test first with `vbench-tdd`.
3. **Write the what and why in `summary.md`**, under "What and why, task by task", as a `#### P1.n: <title>` entry: what the
   task does, criterion by criterion why, the logic decision by decision, where it lives (and a small Mermaid diagram if it
   helps, see `vbench-mermaid`), decisions, learnings, open questions, and where the real build differs from this plan.
4. **Write the task file** `TSK-P1.n-<slug>.md` with `execlog_tool.py shape` as the template: the header, the link to its
   summary entry, the run command, then each step as **Test** (with its level), **Code** and **Logic.** Code blocks are copied
   from the real files, with the first line `# path/to/file`. A block that is an earlier shape of a file says `, stage N shape`
   after the path. Never type code by hand: copy it, so it cannot differ.
5. **Run the check.** `python3 .claude/skills/vbench-execlog/scripts/execlog_tool.py check`. Fix what it names.
6. **Say what was not run.** Counts and run evidence do not go in the task file (they go stale). If a test was not run, say so in
   the summary entry. Never invent a number.
7. **A person reads it against the code**, then approves a named commit in the summary's approvals. This skill does not approve.

## What this skill does not do

- It does not write the code or the test (`vbench-tdd`), and it does not approve its own work.
- It does not judge whether a test is good or the logic well explained: the check only proves the shape and that every code
  block is a copy of its file.
- It does not commit.
