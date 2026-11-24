# 0022 Execution log: a task is a slice, a step is one tested behaviour, and a skill writes it

- Status: accepted
- Date: 2026-11-24
- Decided by: together (the owner asked for the shape and for it to be a rule; the agent decided the wording and the check)

## Context
ADR 0021 gave each use case a notebook with a chapter `summary.md` and one file for each task. The first task files held
everything (objective, reasoning, diagrams, red and green evidence, review) and ran to 500 lines or more, so nobody could
follow them while building. The reasons already live in the summary. A task file should be what you follow at the keyboard,
and writing one should be a procedure that gives the same shape every time.

## Decision
The words are fixed.

- **A task is one slice that can be built and tested on its own.** It is a `TSK-` line of the use case's Slices. Its
  criteria all have a passing test when it is done.
- **A step is one behaviour inside a task, with one failing test and the code that makes it pass.** A step with no test of its
  own is not a step: fold it into the step whose test covers it.
- **The test level is named on the step.** `Unit`: a rule, a use case or an adapter run in process, no HTTP. `API`: the real
  app through `TestClient`. `Integration`: needs a running stack or PostgreSQL. `Architecture`: the boundary tests. A step may
  carry more than one.

| It holds | It lives in |
|---|---|
| What the task does and why, the criteria with their reasons, the logic decision by decision, the diagram, decisions, open questions, where the build differs | `summary.md`, under "What and why, task by task" |
| The code to write, test first, and the few lines of logic that explain it | the task file |

A task file has a header (id, use case, criteria, the commit its code matches), a link to its entry in the summary, the command
that runs its tests, and the steps. A step is **Test** (with its level), **Code** and **Logic.** Code blocks are copies of the
real files at the commit in the header and are never typed by hand. Run counts are not kept in the task file: a run is a fact about
a commit and goes stale.

**Writing one is a procedure, owned by the skill `vbench-execlog`:** take one slice, list its behaviours, write the summary
entry, write the task file from the code, run the check, say what was not run, and have a person read it against the code. The
check is `execlog_tool.py check`. It fails when a header field is missing, the summary has no entry for the task, steps are not
numbered from 1, a step has no test level, no test block, no code block or no logic, a code block is not a copy of its file (unless
it says `stage N shape`), or the text has an em or en dash. It cannot tell whether a test is good or the logic well explained.
A person reads that.

## Alternatives considered
- Keep the ten section layout: complete, but too long to follow, and it repeated the summary.
- A short card with the detail folded under it: tried on TSK-P1.5 and rejected by the owner, who wants the reasons in the
  summary and the task about building and testing.
- A rule in the README only, with no skill: nothing would run it, and a new task would drift. The skill is small, and the
  check keeps it honest.

## Files that change
`.claude/skills/vbench-execlog/` (the skill, `execlog_tool.py` and its tests); `docs/standards/skills-and-agents.md` and its
ledger (one owner, ADR 0017); `docs/execution-logs/README.md` (the task file shape); the UC-P1 chapter (`summary.md` and the eight
task files, converted); `docs/adr/README.md`; `CLAUDE.md`.

## Consequences
A task is something you can follow in one sitting, and the why is read once, in the summary. The cost is two places per task:
the check fails when a task has no summary entry or a step has no test. A task that cannot be split into tested steps is a sign
it is too large, which is the point. The run counts and the red and green evidence of the earlier ten section files are in git
at `46987d0`; they are not carried into the new files, because a count at a commit is not a property of the file. A later
chapter that needs them records them in the summary's verification section.

## Links
ADR 0021 (the notebook), ADR 0017 (one owner for each job), ADR 0020 (honest green); `.claude/skills/vbench-execlog/SKILL.md`.
