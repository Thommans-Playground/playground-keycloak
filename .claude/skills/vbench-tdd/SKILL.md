---
name: vbench-tdd
description: Build a slice of a use case test first, with red, green and refactor run by three subagents (vbench-tdd-red, vbench-tdd-green, vbench-tdd-refactor), and a pause for the person's review after each step. Use whenever the user says "tdd", "red green refactor", "build UC-P1 test first", "write the failing test for AC-12", "next slice", "start the first task", or wants to implement a use case, even if they never say "vbench".
---

# vbench-tdd

Drive one slice of a use case through **red, green, refactor**, one behaviour at a time, with the person reviewing
after every step. The rules (red for the right reason, the minimum code, refactor only on green) are in the three
agents in `.claude/agents/`: `vbench-tdd-red`, `vbench-tdd-green`, `vbench-tdd-refactor`. The rules for branches, commits and asking are
in `_vbench/standards/conventions.md`. The method is the vbench V-cycle: the failing test comes first, so a pass means something.

**Why subagents, and where the pause is.** A subagent runs to the end and returns: it cannot wait for you. So each
step is its own agent with a clean context and narrow job, and **the pause happens here, in this conversation,
between agents**. You decide after each one.

## Steps

1. **Scope.** Say in one line what is being built: one slice (a `TSK-` line in the use case's Slices section) or one
   criterion. Run `python3 .claude/skills/vbench-uc/scripts/uc_tool.py impact <UC>` and `python3 .claude/skills/vbench-at/scripts/at_tool.py show AC-<n>`
   and say which criteria the slice proves. If the use case or its criteria are missing or vague, stop and send the user to
   vbench-uc or vbench-req. Do not build from a guess. Then run `python3 .claude/skills/vbench-explain/scripts/terms_tool.py find <UC> --unseen`
   and offer at most two cards for terms this slice uses (`vbench-explain`), before the first RED, never in the middle of a step.

2. **Preconditions. Stop and say why if one fails.**
   - You are on a feature branch (`feat/UC-<area><n>-<slug>`), not the base branch. If not, offer vbench-branch.
   - The baseline is green. Read `vbench.json`: the `stacks` entry for the app (`api` or `web`) gives the commands.
     Run its `tests`. If it is red, stop and report. Never start on red.
   - The design is settled. The use case has its design sequence diagram, and the reviewers were run on it with
     their findings resolved or accepted by a person (CLAUDE.md, "Reviews"; `vbench-vcycle` shows the stamps).
     If not, say so and ask whether to run the reviewers first. Building comes after the design is settled, not during it.

3. **Plan the behaviours.** Break the slice into small behaviours, one test each, in order, simplest first (a tracer
   bullet through the whole path, then the refusals and edges). Show the list as normal text, then ask with the four
   answers from conventions.md ("How the skills ask"): **Accept**, **Change it**, **Reject**, **I'll do it myself**.

   Before the first RED, also write down which files you expect the slice to change. When the slice is done, compare
   that with `git diff --stat` and say what surprised you. A surprise means the design was unclear or the build wandered.

4. **For each behaviour, run the loop. Pause after every step.**
   - **RED.** Start the `vbench-tdd-red` agent (Agent tool, `subagent_type: "vbench-tdd-red"`). Brief it in full, because it starts
     cold: the behaviour in one sentence, the app, the ids (`AC-n`, `UC-..`), where the test goes, and the commands from
     `vbench.json`. Show its report as it is, the test and the failing run. **Pause:** is this the right failing test?
     Ask: **Accept** (go to GREEN), **Change it** (say what, then run `vbench-tdd-red` again), **Reject**, **I'll do it myself**.
     Also offer **Run to the end of the slice** (drops the pauses, and still shows every red and green run in the summary).
   - **GREEN.** Start `vbench-tdd-green` with the test, the app and the use case id. Show the diff and the passing run.
     **Pause:** is this the right behaviour, and is it the minimum? Same four answers.
   - **REFACTOR.** Offer it only if the code earns it. Start `vbench-tdd-refactor` with the files that changed. Show the diff and
     the green run. **Pause** again. "Nothing worth refactoring" is a fine answer: say it and move on.
   - Then the next behaviour. Do not write the next test until the previous one is green.

5. **Close the slice.** Run `scripts/check.sh` (format, lint, typecheck and tests, the fast gate of ADR 0014), then the app's
   `build` from `vbench.json` if it has one.
   Run `python3 .claude/skills/vbench-at/scripts/at_tool.py report` and say which criteria now have a test. Update the slice
   in the use case only if the person agrees: code is the source of truth. If a test showed a missing or wrong criterion,
   stop and hand it to vbench-req.

6. **Offer the commits. Never commit unasked.** The rhythm is a `test` commit, then a `feat` commit
   (`test(UC-P1): ...`, then `feat(UC-P1): ...`). Use vbench-commit, which shows its plan and asks.

## Rules

- **Never skip the failing run.** A green you did not see go red first proves nothing.
- **A pause is for a decision**, so show what is needed to decide: the test and its failure, the code and its pass,
  the diff. Do the mechanical parts without asking (running the suite, the report).
- **If an agent returns something off-brief** (a test that passes at once, a change to the test in GREEN, production
  code in RED), do not pass it on as done: say so, and run the step again with a corrected brief.
- **The agents do not commit, edit `docs/requirements/`, or run the API tests against the app's own database.**
- **If the agents are not available** (they load when a session starts), read the agent's file in `.claude/agents/`
  and give its body to a general purpose agent as the brief, or do the step yourself in this conversation. The pauses stay.
- No em or en dashes in anything you write.
