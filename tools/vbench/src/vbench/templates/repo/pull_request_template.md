## What and why

<!-- One paragraph: the behaviour that changes and the reason. -->

## Use cases

| UC | Tasks | ACs closed | Rungs verified |
|---|---|---|---|
| UC-… | Task-… | AC-… | unit / integration / system / acceptance |

## Checklist

- [ ] Branch is `<type>/<slug>`, short-lived, and rebased on `main`
- [ ] One use case (or one task) in this PR; each commit is one finished task
- [ ] Merge with **rebase and merge**, so the task commits survive
- [ ] `vbench check` passes (refs, rungs, acs)
- [ ] `vbench check commits --base origin/main` passes and `vbench doctor` is quiet
- [ ] Spec updated to what was built (tasks, Known gaps); ADR added if a decision was made
- [ ] Reviewed by a human
