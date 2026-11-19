---
name: v-5-ship
description: V-model step 5 (closure). Final gates before merge: full verification, independent review, and a PR draft with a traceability table. Asks before pushing or opening a PR.
disable-model-invocation: true
argument-hint: [base branch, default main]
---

# /vbench:v-5-ship: close the V

**Why this step:** every use case is proved and reviewed together before it is merged.

If nobody reviews behind you (a solo or small team), be more conservative about "done", not less.

Paths to `scripts/` and `references/` are relative to this skill's directory.

1. **Run `/vbench:v-4-verify all`** over the branch's UCs (`python3 ../v-4-verify/scripts/branch_ucs.py` lists them). Any Blocking item stops the ship: report and halt.
2. **Independent review in a clean context.** Hand a reviewer subagent only the diff against the base branch, the
   specs and the project's standards (constitution docs, ADRs, naming conventions), pushed into its prompt; the author's
   session is the wrong place to judge its own work. Use `/code-review` if available. Resolve what it raises, or list it
   explicitly.
3. **Docs and decisions.**
   - `vbench check` passes.
   - Nothing in the diff contradicts an accepted ADR or weakens a documented security practice; a
     contradiction has a superseding ADR.
   - The rigor tier chosen in `/vbench:v-2-design` is honoured (the diagrams and rungs it requires exist).
   - A decision that meets the ADR rule has its ADR, with the next free id.
   - A schema change has its migration note.
4. **Commit hygiene.** Run `vbench check commits --base <base>`: every subject is
   `<type>(UC-<id>[/<TSK-id>])[!]: …`, every cited spec and task exists, the branch is `<type>/<slug>`. Then read
   `git log --oneline <base>..HEAD` for unrelated files. Reword with the user's approval; never rewrite
   pushed history on your own.
5. **Draft the PR description** from `references/pr-description.md`. `python3 scripts/pr_draft.py` prints the
   traceability table (UC, tasks, ACs, realising files, verifying tests and rungs); add the Maturity column by hand:
   - Summary of the behaviour change.
   - Title in the commit style (`feat(UC-<id>): …`).
   - Traceability table: UC · tasks · ACs · test files · rungs closed · maturity change.
   - Design notes: aggregates, ports and adapters, patterns chosen and why.
   - Verification: the checks run and their results, stated as they came out.
   - Schema or migration note, ADR link, and known gaps deferred.
6. **Confirm before publishing.** Show the description and the exact `git push` / `gh pr create` commands.
   Push or open a PR only after the user says yes. Never edit CI workflows as part of shipping.

## Connections
- Calls: `/vbench:v-4-verify`, `vbench-trace-checker`.
- Back-edges: any Blocking item returns to `/vbench:v-3-code`, `/vbench:v-2-design` or `/vbench:v-1-requirements`
  depending on where the defect lives.
