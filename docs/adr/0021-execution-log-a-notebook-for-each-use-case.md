# 0021 Execution log: an engineering notebook for each use case

- Status: proposed
- Date: 2026-11-24
- Decided by: together (the owner asked for it; the agent decided the shape)

## Context
After a slice is built, what is left is code, tests and commit messages. The order of work and the reason for each
choice live only in the session that built it. The person building is meant to understand what they own,
and a later change (a defect, a hardening) has no story to read. The use case file holds the plan (`Slices`) and the
design, but it mixes "how it is now" with "how it got here".

## Decision
Each use case may have a notebook in `docs/execution-logs/<UC-id>-<slug>/`: `README.md` (what it is, the table of
chapters), `current.md` (how the feature works today, rewritten when it changes), `chapters/NNN-<name>/` (one change
each, never rewritten to look perfect, a defect gets a new chapter) and `evidence/index.json` (the code, files and tests each
step matches and the review commit). A chapter has a `summary.md` (the overview: objective, context, ground rules, plan, risks, verification, approvals), a `plan.yaml` and one Markdown file for each task. The format is in
`docs/execution-logs/README.md`.

Three rules:
1. **The plan reflects the final code.** A chapter is a reviewed, step by step plan (logic, reasoning, stages, what to
   expect at each) that someone could follow to build the feature. Its last stage is the code that exists, copied from
   its file. For a feature already built, the plan is written by working backwards from the code.
2. **History is kept.** A later change is a new chapter that links the old one. `current.md` is the only page that
   describes today.
3. **Approval names a revision.** A step is reviewed at a commit; if the code it cites changes in a way that changes
   behaviour, the approval is stale until the step is reviewed again.

This first cut is the format and one real chapter (UC-P1, slice TSK-P1.5). No skill, agent or check reads it yet.

## Alternatives considered
- Put it in the use case file: it is already long (UC-P1 is over 330 lines) and history would bury the current design.
- Let an agent write it automatically now: prove the format by hand first.
- Generate it from git alone: it cannot hold the reasons or the order of work.

## Files that change
`docs/execution-logs/` (README, one notebook), this ADR and its row in `docs/adr/README.md`. Later, if accepted:
`vbench-tdd` (write the plan before building), `vbench-vcycle` (a row), `test_scope.py` and the ledger (an owner).

## Consequences
A way to read how a feature was built, and why. The cost is writing; the first chapter shows how much. Nothing checks the
notebook yet, so it can go stale: the check (links resolve, every cited commit exists, `current.md` names the same files
as the code) is the next step, to be added with the owner's yes.

## Links
ADR 0017 (one owner for each job), ADR 0018 (checked term cards); `docs/usecases/UC-P1-create-a-project.md`.
