# Contributing

How a change gets from an idea to `main`. The rules below are checked, not just written: CI runs
`vbench check` (refs, rungs, acs) and, on pull requests, `vbench check commits`.

## Flow

Work in the V-cycle, one use case at a time (`docs/00-engineering-methodology.md`): requirement,
design, code, verify, ship. In Claude Code the steps are `/vbench:v-1-requirements` through
`/vbench:v-5-ship`; `/vbench:v-status` shows where a use case stands.

## Branching

Trunk-based development: `main` is always releasable, and everything reaches it through a short-lived branch and a
pull request.

```
<type>/<slug>        feat/uc-a-001-login      fix/uc-a-001-token-reuse      docs/uc-a-001-spec      chore/bump-ci
```

- `type` is a commit type (lower case). Put the use case id in the slug (`uc-a-001`), so the branch says what it is for.
- Cut the branch from the latest `main`. Keep it to a few days (`branch_max_days` in the config; `vbench doctor` notes a
  branch past it). If it grows, merge what is finished and split the rest.
- Rebase on `main` before opening the pull request (`vbench doctor` tells you when the branch is behind).
- One pull request is one use case, or one task when the use case is large.
- Cut `release/<x.y>` from `main` only to patch a shipped version while `main` moves on. A fix made there also goes to
  `main`.
- Hotfix: an ordinary `fix/` branch to `main`, then a patch tag.

### Repository settings (set these once; vbench cannot)

- Protect `main`: no direct pushes, require a pull request, require the `vbench` CI job to pass, require a linear history.
- Merge with **rebase and merge**. Squashing would fold the task commits into one and lose the history `vbench commit`
  built. If you must squash, make the pull request title a valid commit subject and keep the PR to a single task.
- Delete the branch after merging.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/) with the ids as the scope:

```
<type>(<UC-id>[/<TSK-id>])[!]: <description>

feat(UC-A-001/TSK-A-002): add login endpoint with lockout
fix(UC-A-001/TSK-A-003): reject reused refresh token
docs(UC-A-001): approve requirements and acceptance criteria
feat(UC-A-002)!: drop the v1 token format
chore: bump CI action versions
```

| Part | Rule |
|---|---|
| **type** | `feat` `fix` `docs` `refactor` `perf` `test` `build` `ci` `chore`, lower case |
| **UC-id** | the use case the commit belongs to; only `chore` may omit it, and the spec must exist |
| **Task** | optional; if given, the row `TSK-<area>-<nnn>` must already be in the spec's *Delivery tasks* table |
| **`!`** | a breaking change (a major version); `vbench commit --breaking` adds it and a `BREAKING CHANGE:` footer |
| **description** | imperative ("add", not "added"), lower case, no trailing period; the whole subject is at most 72 characters |

The body explains **why**, wrapped at 72 columns. Footers: `Closes: AC-…` (written for you on `feat` and `fix`),
`Tested: …` (written by `vbench commit`, says whether vbench ran the tests), `Closes #NN` for issues.

- **One commit is one finished task**: the red, green and refactor steps are done, the task's criteria have tests, the
  tests pass. Never commit WIP or a red state to a branch you will open a pull request from.
- Do not hand-write the subject: stage a finished task and run `vbench commit -m "add login" --dry-run`. It builds a
  subject that passes the check, refuses a task whose criteria have no test yet, and commits only what is staged (it runs
  the `[commands] test` command from `.vbench/config.toml` and refuses on red; `--green` is only for a project with
  none). In Claude Code, `/vbench:commit` does the same.
- Merge, revert, `fixup!` and `squash!` commits are skipped by the check.

## Pull requests

1. Rebase on the latest `main`.
2. Title in the commit style. Fill in the template; the traceability table comes from `/vbench:v-5-ship`.
3. Make sure `vbench check` and `vbench check commits --base origin/main` pass locally, and `vbench doctor` is quiet.
4. A human reviews and merges (rebase and merge). Keep the PR to one use case where you can.
5. A defect found in review or QA is not fixed silently: it becomes a task row, a new use case, or a `99-problems` entry.

## Releases

Semantic versioning, from the commit types: `fix` is a PATCH, `feat` a MINOR, a `!` or `BREAKING CHANGE` a MAJOR. A release
is an annotated tag on `main` (`git tag -a v1.2.3 -m "Release v1.2.3"`), made when `main` is green. Group the notes by
type; because the commits are Conventional Commits, tools such as `release-please` and `git-cliff` read them as they are.
