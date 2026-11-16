# Conventions: branches, commits, pull requests

The single source for the rules that `vbench-branch`, `vbench-commit` and `vbench-pr` apply. The checkers
(`check_branch.py`, `check_message.py`, `check_pr.py`) enforce the same rules. The id prefix (`UC`), the
base branch and the limits come from `vbench.json` (see `../README.md`). The examples use the defaults.

If a repo already has a `CONTRIBUTING.md` with its own rules, those win. Change the checkers' settings in
`vbench.json` to match them, or tell the skills.

## The loop

1. Pick a card. Its use case and acceptance test are already written.
2. Branch from an up to date base branch (the default branch, found from `origin/HEAD`, or `base_branch` in `vbench.json`):

   ```bash
   git switch <base> && git pull
   git switch -c feat/UC-P1-create-project
   ```

3. Write the failing test first, then the code that makes it pass. Repeat in small steps.
4. Open a pull request into the base branch within 1 to 2 days. If the card cannot be finished in that time, split it.
5. Get a review, make the checks pass, merge, and delete the branch.

## Branch names

| Type | Format | Example |
| ---- | ------ | ------- |
| Use case | `feat/UC-<area><n>-<slug>` | `feat/UC-P1-create-project` |
| Production fix | `hotfix/<slug>` | `hotfix/token-expiry` |
| Spike, may not merge | `experiment/<slug>` | `experiment/new-renderer` |
| Tooling, no use case | `chore/<slug>` | `chore/ci-lint` |
| Documentation only | `docs/<slug>` | `docs/branching-strategy` |

The use case id, `UC-<area><n>`, is a letter for the area and a number that runs within that area. Ids are
append only, never renumbered or reused. The branch, the card, the use case spec and the pull request all
carry it. The id keeps its capitals. The slug is lowercase words joined by hyphens, at most 60 characters in all.

Repos that do not use use case ids can set `"use_case_ids": "optional"` in `vbench.json`, which also allows
`feat/<slug>`.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <summary in lowercase, imperative>

Optional body: why, not what.
```

| Type | Use for |
| ---- | ------- |
| `feat` | New behaviour for a use case |
| `fix` | A bug fix |
| `test` | Adding or changing tests only |
| `refactor` | Restructuring with no behaviour change |
| `docs` | Documentation only |
| `style` | Formatting only |
| `chore` | Tooling, dependencies, configuration |

The summary line rules:

- Lowercase, and in the imperative: "archive a project", not "archived" or "archives".
- Say what the change does for the use case, not which files moved.
- No full stop at the end, and 72 characters or fewer for the whole line.
- No em dashes or en dashes. Use a comma, a colon or brackets.
- Add a body only when the reason is not obvious from the summary. Wrap it at about 72 characters.

The scope is the use case id. Keep commits small, so a test and the code that satisfies it can be separate commits:

```
test(UC-P1): a project cannot be archived twice
feat(UC-P1): archive a project with a reason
```

Work with no use case (tooling, docs) uses a plain scope, such as `chore(ci): add lint step`.

## Pull requests

- The title starts with the use case id: `UC-P1: Create a project`. Work with no use case uses a commit type and a lowercase summary: `docs: add contributing rules`. Under 72 characters, no full stop.
- If the repo has `.github/pull_request_template.md`, the description follows it. Otherwise: what changed, why, the use case it serves, how it was checked. Tick a checklist item only when it was really checked, and write "not run" instead of claiming a check that did not happen.
- Keep it small enough to review in one sitting.

## Before you open a pull request

- [ ] The branch is based on a recent base branch
- [ ] The use case has a spec, and its acceptance criteria are listed
- [ ] Tests were written first and cover the use case's acceptance test
- [ ] The repo's tests, lint and type checks pass
- [ ] Commit messages follow the format above
- [ ] Any finished work that is not ready for users is behind a feature flag, or the card is cut smaller

## How the skills ask

Every vbench skill works the same way, so you always know what it will do and can stay in control:

1. **Explain first.** Before it changes anything, the skill says in plain words what it found, what it plans to do and why, and what each step changes.
2. **Ask with four answers.**
   - **Accept:** do exactly what was shown.
   - **Change it:** you say what to change, and it shows the plan again.
   - **Reject:** do nothing.
   - **I'll do it myself:** it prints the commands or text and runs nothing.

   The question box shows its question in bold, so keep the question to one short line, like "Make these 3 commits?". Write the plan (messages, files, title, description) as normal text in the chat before asking, and put any extra detail in the answers' descriptions.
3. **Explain after.** When it has acted, it says in plain words what it did, what the result is, and how to undo it.

An answer covers only the plan that was shown. If the plan changes, the skill asks again. The skills stage files by name. They never merge, amend, rebase, reset or force push, and only `vbench-pr` pushes, and only after you accept.
