---
name: v-fix
description: Fix a confirmed bug or make a small unplanned change while keeping it traced to a UC: failing test first, smallest change, spec updated if behaviour changed.
disable-model-invocation: true
argument-hint: <bug description | UC-id>
---

# /vbench:v-fix: a small change without skipping the trace

**Why this step:** a failing test first shows the bug is real, and keeps it fixed and traced to its use case.

Input: `$ARGUMENTS`

1. **Triage size.** Does it add behaviour (a new flow, endpoint or AC)? Stop and send the user to
   `/vbench:v-1-requirements`. This is for defects and small corrections only.
2. **Find the owner.** Identify the UC whose spec covers the behaviour (search for `Realises UC-`). No owning
   UC: say so and ask whether it warrants one.
3. **Reproduce first.** Write a failing test tagged `Verifies UC-<id> · <rung> rung.` and, if it pins an
   acceptance criterion, the AC marker. Run it and show it failing on the assertion, not on a collection or
   import error.
4. **Smallest fix** to green. No unrelated refactors.
5. **Spec sync.** If the spec described the buggy behaviour, or the fix reveals a missing flow or AC, update
   the spec in the same change.
6. **Gates.** `python3 ../v-3-code/scripts/run_gates.py --only test,lint` (add `check` if docs or tags changed).
   Not the whole matrix for a one-line fix.
7. Commit only if asked, with `vbench commit -m "<summary>" -t fix --dry-run` first (then `--green`). If the fix is
   its own commit-sized unit of the UC, add a task row to the spec first and name it with `--task`.

## Connections
- Back-edge: new behaviour discovered → `/vbench:v-1-requirements`.
