---
name: vbench-branch
description: Name and start a git branch for a piece of work in this repo, following the vbench branch format (for example "feat/UC-P1-create-project"). Use this whenever the user is about to start a card or use case, says "start UC-P1", "new branch for ...", "create a branch", "what should I call this branch", or wants a branch name checked, even if they never say "vbench". Also use it to check or fix an existing branch name.
---

# vbench-branch

Give the work a branch name that carries its use case id, so the branch, its card, its commits and its pull request all point at the same use case.

The rules are in `_vbench/standards/conventions.md` (sections "The loop" and "Branch names"). That file is the single source. This skill applies those rules and does not restate them in full. If the rules change, change `_vbench/standards/conventions.md` and `scripts/check_branch.py`, not this file.

It shows its plan and asks the user to confirm before it creates anything. It never pushes.

Why the name matters: the commit skill reads the use case id from the branch. A wrong branch name makes every commit after it wrong too.

## Steps

1. **Find out what the work is.** Get the use case id (for example `UC-P1`; the prefix is `id_prefix` in `vbench.json`) and a short description. If the user gave only an idea, ask which use case it is. Never invent an id, because ids are append only and the numbers are owned by the use case specs. If it truly has no use case, ask whether it is a `chore`, `docs` or `experiment` branch.

2. **Pick the type.**
   - A use case: `feat/UC-<area><n>-<slug>`
   - A fix for something in production: `hotfix/<slug>`
   - A spike that may not merge: `experiment/<slug>`
   - Tooling with no use case: `chore/<slug>`
   - Documentation only: `docs/<slug>`

3. **Make the slug.** A few lowercase words joined by hyphens that say what the change does, such as `create-project`. Drop filler words. Keep it short enough to read in a branch list. The id keeps its capitals.

4. **Check it.** Run `python3 .claude/skills/vbench-branch/scripts/check_branch.py "<branch name>"`. If it fails, fix the name and run it again.

5. **Check the starting point.** The branch should start from an up to date base branch (`base_branch` in `vbench.json`, else the remote default, else `main` or `master`). Find it with `python3 -c "import sys; sys.path.insert(0,'.claude/skills/_vbench'); import config; print(config.base_branch(config.load()))"`. The rest of this skill calls it `<base>`.
   - `git branch --show-current` and `git status --short` show where you are and whether there are uncommitted changes. If there are, say so before suggesting a switch.
   - `git fetch origin` is safe to run. Then `git rev-list --count <base>..origin/<base>` says how many commits `<base>` is behind. If it is more than zero, the commands below pull first.

6. **Explain and ask.** Follow "How the skills ask" in `_vbench/standards/conventions.md`. Explain in plain words why you chose this name. Show the plan: the branch name, what it starts from, and the commands. Mention anything that affects it, such as uncommitted changes that will come along, or `main` being behind. Then ask with the AskUserQuestion tool (or a plain question in chat if it is not available), with four answers: **Accept** (create this branch), **Change it** (the user says what to change, then show the plan again), **Reject** (do nothing), **I'll do it myself** (print the commands and run nothing). Check the intent too: if the work does not look like it matches the use case named, ask.

   Why ask: the name is used by every commit and the pull request after it, so a wrong name is annoying to fix once pushed. A confirmation covers exactly the plan shown. If it changes, ask again.

7. **Create the branch.** Only after a yes, run the commands one at a time and stop on the first error:

   ```bash
   git switch <base> && git pull
   git switch -c feat/UC-P1-create-project
   ```

   Skip `git pull` when `<base>` is not behind. If there are uncommitted changes, do not stash or discard them without asking. Never use `git switch -C` or `--discard-changes`, never push, and never delete or rename a branch. If the user picks "I'll do it myself", show the commands and run nothing. If they pick "Reject", do nothing. Finish with `git branch --show-current`, then explain in plain words what you did and how to undo it: `git switch <base>` then `git branch -d <name>` removes an empty new branch. Offer it, and do not run it unasked.

   Remind them of the loop: write the failing test first, and open the pull request within 1 to 2 days. If the card cannot be done in that time, it should be split before starting.

## Examples

"start UC-P1, create project" gives `feat/UC-P1-create-project`.

"I need to fix the token expiry bug in production" gives `hotfix/token-expiry`. A hotfix branches from the release tag running in production, so ask which tag if it is not `<base>`.

"add a lint step to CI" has no use case, so `chore/ci-lint`.

"let me try a new tiptap renderer" gives `experiment/new-tiptap-renderer`.

"new branch for the archive thing" has no id yet. Ask: "Which use case is that, for example UC-P1?"

## When the branch already exists

If the user asks you to check a branch name, run the checker, then explain what is wrong in plain words and give the fixed name. Renaming a branch that is already pushed affects other people, so give the commands and let the user decide.
