---
name: commit
description: Commit one finished task with a message that follows the project's convention. Runs `vbench commit --dry-run`, shows the message and what blocks it, and commits only after the person agrees. Use after a red-green-refactor cycle is approved, never mid-cycle.
disable-model-invocation: true
argument-hint: [summary of the change]
---

# /vbench:commit: commit a finished task

**Why this step:** a commit that follows the convention and records only finished work keeps the history traceable and `vbench check commits` green.

One commit is one finished task: the red, green and refactor steps were each approved, the task's criteria all have
tests, and the project's tests pass. Never commit a red step or work in progress.

1. Make sure the task's files, and only those, are staged (`git status`). Anything else stays out of the commit.
2. Run the project's gates: `python3 ../v-3-code/scripts/run_gates.py` (paths relative to this skill's directory).
   If anything fails, stop and report; do not commit.
3. Run `vbench commit -m "$ARGUMENTS" --dry-run --json` (ask for a summary in the imperative if `$ARGUMENTS` is empty).
   No `vbench` on the PATH but its MCP server configured? Use the `commit_message` tool, which returns the same plan.
4. Read the result:
   - `blockers` not empty: tell the person exactly what they say (an unfinished task, a failing gate) and stop.
   - Exit code 2 (ambiguous): more than one task or use case is staged. List the candidates and ask which one,
     then rerun with `--task` or `--uc`, or unstage the rest.
   - `warnings`: pass them on (unstaged files, a past-tense summary).
5. Show the `message`, the type, the use case and task, and the files. Ask whether to commit. **Do not commit
   without a yes.**
6. On yes, run the same command without `--dry-run`. vbench runs the project's test command itself and refuses on a
   red run; only if `[commands] test` is empty does it need `--green` (then say that it was the person's word, not a run).
   Report the hash.

Keep any change to the commit rules in `vbench commit`, never in this file.

## Connections
- Before it: `/vbench:v-3-code` (the cycle) or `/vbench:v-fix`. After it: `/vbench:v-5-ship` checks the whole branch.
