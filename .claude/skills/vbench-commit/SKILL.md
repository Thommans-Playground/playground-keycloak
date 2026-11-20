---
name: vbench-commit
description: Work out what the changes in this repo are, split them into sensible commits, write each message in the vbench commit format, and make the commits (Conventional Commits with the use case id as scope, for example "feat(UC-P1): archive a project with a reason"). Use this whenever the user asks for a commit message, says "commit this", "what should I write for this commit", "message for these changes", or has just finished a piece of work and is about to commit, even if they never say "vbench". Also use it to check or fix a commit message someone else wrote.
---

# vbench-commit

Reason about the changes, then commit them with clear messages that match this repo's format, so the history reads as a trail of use cases and anyone can follow it. It always shows its plan and asks the user to confirm before it commits anything. It never pushes.

The rules are in `_vbench/standards/conventions.md` (section "Commit messages"). That file is the single source. This skill applies those rules and does not restate them in full. If the rules change, change `_vbench/standards/conventions.md` and `scripts/check_message.py`, not this file.

The reasoning: the scope carries the use case id from the id scheme, so a commit, its branch, its card and its pull request all point at the same use case. Small commits keep the test-first rhythm visible: a `test` commit, then the `feat` commit that makes it pass.

## Steps

1. **Look at the work.** Run `git branch --show-current` and `git status --short`, then `git diff --staged` and `git diff`. New files do not show in a diff, so read them or list them. Work out what the changes are about before choosing anything.

2. **Find the scope.**
   - Branch `feat/UC-P1-create-project` gives scope `UC-P1`. The id keeps its capitals.
   - Branches `chore/…` or `docs/…` have no use case. Use a plain lowercase scope that names the part touched, such as `ci`, `docs` or `deps`.
   - On the base branch (`main`, `master` and so on), or when the branch holds no id, do not guess an id. Ask which use case this belongs to. Never invent a new id.

3. **Pick the type.** Choose the one that matches the diff:
   `feat` (new behaviour), `fix` (bug), `test` (tests only), `refactor` (no behaviour change), `docs`, `style` (formatting only), `chore` (tooling, dependencies, config).
   A diff of only test files is `test`. If it holds new behaviour plus its tests, `feat` is fine, but see step 5.

4. **Write the summary line.** Format: `<type>(<scope>): <summary>`. Follow the summary line rules in `_vbench/standards/conventions.md`: lowercase and imperative, says what the change does for the use case, no full stop, 72 characters or fewer, and no em or en dashes.

5. **Check the size.** One commit is one step. If the diff mixes unrelated things (two use cases, or a refactor plus a feature, or formatting plus logic), say so and suggest how to split it, with a message for each part. A test and the code that satisfies it may be one commit or two. Two is better when the work was done test first.

6. **Add a body only when it earns its place.** Add one when the reason is not obvious from the summary: why this approach, what was rejected, what to watch for. Skip it for small, clear changes.

6b. **Check the code first.** Run `scripts/check.sh` (ADR 0014). A commit with a failing format or lint check will fail in CI.
7. **Validate.** Run `python3 .claude/skills/vbench-commit/scripts/check_message.py "<the summary line>"`. If it fails, fix the line and run it again.

8. **Explain and ask.** Follow "How the skills ask" in `_vbench/standards/conventions.md`. Before changing anything, explain in plain words what the changes are and why you would split them this way. Show the plan: for each commit, its message and the files it will hold, plus any file you are leaving out and why. Then ask with the AskUserQuestion tool (or a plain question in chat if the tool is not available), with four answers: **Accept** (make these commits), **Change it** (the user says what to change, then show the plan again), **Reject** (do nothing), **I'll do it myself** (print the commands and run nothing). Also ask about anything unclear, for example whether a file belongs in this work at all.

   Why ask: a commit puts the user's name in the history, and once it is shared it is hard to undo cleanly. The user is also learning, so seeing the reasoning before it happens is part of the point. A confirmation covers exactly the plan shown. If the plan changes, ask again.

9. **Commit.** Only after a yes. For each commit, stage exactly its files by name, then commit:

   ```bash
   git add path/one path/two
   git commit -m "feat(UC-P1): archive a project with a reason"
   ```

   Rules that keep this safe:
   - Stage by name. Never use `git add -A` or `git add .`, because they pick up stray files such as `.DS_Store`, build output or secrets. Leave out anything that looks like a secret (`.env`, keys) and tell the user.
   - For a message with a body, use a second `-m`. If the session's instructions require a `Co-Authored-By` trailer, add it as the last line of the body.
   - Do not push, amend, rebase or reset. Those change shared or past history, and need their own request.
   - If a commit fails (for example a hook), report the error and stop. Do not retry with flags that skip checks.
   - If the user says "just the message" or "don't commit", or picks "I'll do it myself", show the messages and the commands, and run nothing. If they pick "Reject", do nothing.

   Finish by showing `git log --oneline` for the new commits and `git status --short` for what is left. Then explain in plain words what you did, and how to undo it: `git reset --soft HEAD~1` removes the last commit and keeps the changes staged. Offer it, and do not run it unasked.

## Examples

Branch `feat/UC-P1-create-project`, staged: a new failing test for archiving twice.
`test(UC-P1): a project cannot be archived twice`

Same branch, staged: the domain rule and use case that make that test pass.
`feat(UC-P1): archive a project with a reason`

Branch `chore/ci-lint`, staged: a lint step in the workflow file.
`chore(ci): add lint step`

Branch `docs/branching-strategy`, staged: edits to the branching strategy document.
`docs(branching): add status table of what is set up`

On the base branch, staged: changes with no use case id.
Do not write a message yet. Ask: "Which use case is this for, or should it be a chore?"

## When the message is someone else's

If the user pastes a message to check, run it through the checker, then explain in plain words what is wrong and give the fixed version.
