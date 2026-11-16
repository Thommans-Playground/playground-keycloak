---
name: v-3-code
description: V-model step 3 (the vertex). Build an approved, designed UC task by task with strict double-loop TDD: a failing acceptance test first, then red-green-refactor at the unit rung, then integration and system tests as seams appear.
disable-model-invocation: true
argument-hint: <UC-id> [TSK-id]
---

# /vbench:v-3-code: the vertex, driven by tests

**Why this step:** writing the test first proves it can fail, so a pass means something.

Input: `$ARGUMENTS` (UC id, optional task id; default = the first task in the spec whose ACs are not all
covered, per `vbench status`). Paths to `scripts/` and `references/` are relative to this skill's directory.

Run the gates with `python3 scripts/run_gates.py` (it reads `[commands]` from `.vbench/config.toml`, runs `test`,
`lint`, `types`, `boundaries`, then `vbench check`, and prints one table; `--only test,lint` narrows it). The
loops, the red-for-the-right-reason rule and the exact tag forms are in `references/tdd-and-tagging.md`. On the
python-fastapi stack the commands are `uv run …` and the layout and test mapping are in
`../v-2-design/references/stack-python-fastapi.md`; code goes in the context's `domain`, `application` and `adapters`,
and `boundaries` (`uv run lint-imports`) must stay green.

## Preconditions: stop and say why if any fail
- The spec has concrete ACs (`/vbench:v-1-requirements`) and, for standard and full tiers, a Verification plan
  with a Delivery tasks table (`/vbench:v-2-design`).
- The user approved the design in this conversation, or it is committed as `docs(UC-<id>): …`.
- You are on a feature branch, not the default branch.
- The baseline is green: run `python3 scripts/run_gates.py --only test` first. If it is red, stop and report.

## The iron rule
**No production code without a failing test that demands it.** Show the failing run before writing the code.
Exceptions, stated aloud when used: refactoring under green; pure configuration or wiring covered by the next
rung's test; documentation.

A test is only RED if it fails **for the right reason**: an assertion on the missing behaviour. A collection
error, an import error, a fixture error or a `NameError` is not red; fix the test until it fails on the
assertion.

## Where you pause, and where you do not
The person's attention is for the decisions: is this the right failing test, is this the right behaviour, is the
shape clean. So **stop for review at each step of the diagram** and nowhere else in the loop:
- **After RED:** show the failing run and the test, then stop. Wait for a yes.
- **After GREEN:** show the passing run and the code, then stop. Wait for a yes.
- **After REFACTOR** (when you refactored): show the diff and the green run, then stop.
Then take the next step. Do the slow and mechanical parts without asking: running the gates, tagging, syncing the spec,
task rows and diagrams, `vbench trace`, drafting the commit message. Show `vbench trace <UC>` at each pause so the
person sees which steps are done. If they say "run to the end of the task" (or the use case), drop the pauses until
then, and still show every red and green run in the summary.

## Loop, per task
1. **Announce** the task (its row in the spec's Delivery tasks table), the ACs it closes, the sequence steps it builds
   and the planned test for each rung. Build the steps one at a time, in diagram order, and start each task in a fresh
   session when the context is long. If the work needs a task the table does not have, **add the row first** (id = next free
   `TSK-<area>-<nnn>` from `vbench id task --area <A>`, description, ACs): commits are checked against that table.
2. **OUTER RED (acceptance rung).** Write the task's AC test(s) first, through the public interface. Tag
   each with the AC marker from config (default `@pytest.mark.ac("AC-<area>-<nnn>")`) and the docstring
   `Verifies UC-<id> · STP-<area>-<nnn> · acceptance rung.` Run it and confirm it fails on the assertion.
3. **INNER LOOP (unit rung)**, one behaviour at a time, tracer bullet first:
   - RED: one unit test, docstring `· unit rung.`; run it and see it fail for the right reason.
   - GREEN: the minimum code to pass; tag it `Realises UC-<id> · STP-<area>-<nnn>` (the step it builds) in a comment or
     docstring, on the line that does the work. Run.
   - Do not write the next test until this one is green. Never anticipate future tests.
   - REFACTOR only on green; run the tests after each step.
4. **INTEGRATION rung, when a seam appears** (new port or adapter, a call across a context's public
   interface, persistence): write the failing integration test first, then wire it, then run the
   `boundaries` command if one is configured. Docstring `· integration rung.`
5. **SYSTEM rung, only if the design planned one**: failing test first.
6. **OUTER GREEN.** Run the acceptance test(s). The task is done when they pass, not before.
7. **Task gate.** Run `python3 scripts/run_gates.py`. Fix before moving on.
8. **Sync the spec and its diagrams** to what was built (code is the source of truth; redraw a diagram that no
   longer matches): the task's row (description and the ACs it really closed; never a
   status mark, closure is derived), Implementation overview, Known gaps. Flip Maturity only when the code
   earns it.
9. One commit per **finished** task, never per phase: the steps were reviewed as you went, so commit once, only if asked. Stage that task's files, run the project's gates (`run_gates.py`), and
   run `vbench commit -m "<summary>" --dry-run`: it builds the message the convention needs and says what still
   blocks it. Show it; if the person agrees, repeat without `--dry-run` (vbench runs `[commands] test` itself and
   refuses on red; `--green` only when none is set). Never commit a red step or WIP.

## When things go wrong
- The test reveals a missing or wrong AC: stop and go back to `/vbench:v-1-requirements` (the spec is the
  contract; do not quietly change the behaviour in code).
- The design does not fit: go back to `/vbench:v-2-design`.

## Connections
- Reads: the approved spec and design.
- Writes: production code tagged `Realises`, tests tagged `Verifies` and AC markers, spec sync (task rows).
- Back-edges: `/vbench:v-1-requirements` (AC gap), `/vbench:v-2-design` (design gap).
- Next: `/vbench:v-4-verify`.
