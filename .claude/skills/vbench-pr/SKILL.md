---
name: vbench-pr
description: Prepare and open a pull request for the current branch in this repo, following the vbench PR format (title like "UC-P1: Create a project", a description from the commits, a checked checklist). Use this whenever the user says "open a PR", "create a pull request", "write the PR description", "is this ready for review", or has just pushed a branch, even if they never say "vbench". Also use it to check or improve an existing PR title or description.
---

# vbench-pr

Turn a finished branch into a pull request that a reviewer can understand quickly: a clear title, an honest description built from the commits, and a checklist that is only ticked where something was really checked.

The rules are in `_vbench/standards/conventions.md` (sections "Pull requests" and "How the skills ask"). That file is the single source, and the shape of the description is `.github/pull_request_template.md`. This skill applies them and does not restate them in full. If a rule changes, change `_vbench/standards/conventions.md`, the template or `scripts/check_pr.py`, not this file.

It explains its plan and asks the user what to do before it pushes or creates anything. It never merges, approves or closes a pull request on its own.

## Steps

1. **Look at the branch.**
   - `git branch --show-current` and `git status --short`. Uncommitted changes will not be in the PR, so say so. If they matter, suggest `vbench-commit` first.
   - `git log <base>..HEAD --oneline` and `git diff <base>...HEAD --stat` (`<base>` is `base_branch` in `vbench.json`, else the remote default branch, else `main` or `master`; `check_pr.py` prints which it used) show what the PR holds.
   - `git rev-parse --abbrev-ref @{u}` says whether the branch is pushed. `gh pr list --head <branch>` says whether a PR already exists. If one does, offer to update its description instead of creating another.
   - On `<base>`, stop. A PR needs its own branch.

2. **Check the branch.** Run `python3 .claude/skills/vbench-pr/scripts/check_pr.py`. It checks the branch name and every commit message since `<base>`. If something is not valid, explain it in plain words and offer to fix it before going on. Fixing a pushed commit message means rewriting history, so do not do it. Tell the user and let them decide.

3. **Write the title.**
   - A use case branch gives `UC-P1: Create a project`, from the id in the branch name.
   - Work with no use case gives `docs: add contributing rules and skills` (lowercase, a commit type first).
   - Under 72 characters, no full stop, no em or en dashes. Check it with `check_pr.py --title "<title>"`.

4. **Write the description** with the headings of `.github/pull_request_template.md`:
   - **What changed:** a few plain bullets that say what the PR does for the use case, built from the commits. Do not list files.
   - **Use case:** the id and a link to its spec if one exists, otherwise "none".
   - **How it was checked:** only what was really run and what happened. If no tests exist yet, or you did not run them, write "not run". Never claim a check that did not happen.
   - **Please check:** where the reviewer should look closely, and anything you are unsure about.
   - **Not in this PR:** what is left for later.
   - **Checklist:** tick an item only when you verified it (for example, the commit messages, because the checker ran). Leave the rest unticked and add a short note on why.

5. **Explain and ask.** Follow "How the skills ask" in `_vbench/standards/conventions.md`. Show the title, the description, the base and head branches, and the exact steps you would take (a push if the branch is not pushed, then creating the PR). Say in plain words what each step does and what it changes on GitHub. Then ask with the AskUserQuestion tool (or a plain question in chat if it is not available), with these answers:
   - **Accept:** do exactly this.
   - **Change it:** the user says what to change, then show the plan again.
   - **Reject:** do nothing.
   - **I'll do it myself:** print the title, the description and the commands, and run nothing.
   A draft PR is also an option if the user wants early feedback.

6. **Create the PR.** Only after Accept.
   - If the branch is not pushed: `git push -u origin HEAD`. Never force push.
   - If `gh` is installed and logged in (`gh auth status`): write the description to a temporary file and run `gh pr create --base <base> --head <branch> --title "<title>" --body-file <file>`.
   - If `gh` is missing or not logged in: do not fail. Print the title and description for the user to paste, with the link `https://github.com/<owner>/<repo>/pull/new/<branch>` (read the owner and repo from `git remote get-url origin`).

7. **Explain what happened.** Say in plain words what was done and what the result is: what was pushed, the PR link and number, and what is still waiting for a person (a review, checks). Say how to undo it: close the PR with `gh pr close <number>` or in the browser, which leaves the branch and commits untouched. Then offer what comes next, such as reviewing it or merging after approval. Do not do those yourself.

## Examples

Branch `feat/UC-P1-create-project`, three commits (a test, the feature, the screen).
Title: `UC-P1: Create a project`
What changed: a project can be created with a name and description; creating one with an empty name is refused; the new project shows on the projects list.
How it was checked: "Unit and acceptance tests passed locally" only if they were run, otherwise "not run".

Branch `docs/contributing-and-setup`, four commits.
Title: `docs: add contributing rules, branching strategy and skills`
Use case: none.

Branch is the base branch.
Stop and say: "You are on the base branch. Start a branch first with vbench-branch."

## When the PR already exists

If the user asks you to improve an existing PR, read it with `gh pr view <number>`, show the improved title and description, and follow the same explain and ask step before running `gh pr edit`.
