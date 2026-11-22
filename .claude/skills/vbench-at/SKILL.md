---
name: vbench-at
description: Turn acceptance criteria into acceptance tests and check that the two stay linked. Reports, as facts, which acceptance criteria have no test, which tests name a criterion that does not exist, which tests are stale because the criterion changed, and which use cases list a criterion with no test. Drafts a failing test skeleton from a criterion (Given, When, Then as comments, no invented assertions) and asks before writing it. Use this whenever the user says "vbench-at", "acceptance test", "write the test for AC-12", "which criteria have no test", "are my acceptance tests up to date", "Verifies AC", "outer loop", "test first for this use case", or has just finished writing acceptance criteria or a use case and wants the tests, even if they never say "vbench".
---

# vbench-at

An acceptance test runs **one acceptance criterion through the front door** (the API) and checks what the
person gets, not how the code is built. It is the outer loop of test-first: written first, failing, and green
last. Unit tests (rules) and integration tests (adapters) are other levels and are not written here.

This skill ties the criteria in `docs/requirements/acceptance-criteria.md` to the tests that run them, and
reports where the tie is missing or broken. It drafts a skeleton and stops there: the checks in a test depend
on the API, and an assertion written without knowing the API is a guess.

The tag convention is in `_vbench/standards/naming-conventions.md` section 6. The levels and what "acceptance" means are in
`_vbench/standards/usecases.md` ("How a use case is verified").

## The stack, and where the repo stands

The project's default stack is **Next.js, React, TypeScript and Tailwind** for the frontend and **Python, FastAPI
and Postgres** for the backend (decision 22). So the default acceptance test is a **pytest** test that calls the
FastAPI API. Playwright is for the few browser journeys, and Vitest is for frontend unit tests, not acceptance.

Look before you claim anything: run `ls` and check for `tests/`, a backend and a test config. When this skill
was written there was **no backend, no API and no `tests/acceptance` folder** in the repo yet. The only tests
were Vitest unit tests in `packages/ui`, and Playwright was installed from earlier Storybook work. So the
details (how the API starts in a test, the Postgres test database, how a test signs in) were not settled. Use the
default, and ask those details (`references/questions.md`, sections 1 and 2).

## The helper

`python3 .claude/skills/vbench-at/scripts/at_tool.py <command>` (from the repo root). It looks for tests in
`tests/acceptance` (change it with `--tests-dir`), and it never edits the two requirements files.

- `report [--release R1]`: criteria with no test, tests naming an unknown criterion, stale tests, tests with no
  review hash, and use cases that list a criterion with no test. Exit code 1 means a problem (an unknown tag
  or a stale test). A criterion with no test is a gap, not an error.
- `show AC-ID`: the criterion, the requirements it proves, the use cases that run it, and its tests.
- `skeleton AC-ID [--stack pytest|playwright|vitest] [--write]`: a failing placeholder (default `pytest`). Printing writes nothing.
  It refuses a criterion that is not acceptance level, a criterion that already has a test, and a file that
  exists.
- `stamp AC-ID`: record that a person has checked the tests of this criterion against its current text.

## The tag

A test says which criterion it runs, in a comment or its name:

```
Verifies AC-12 [reviewed 7a2439b]
```

In pytest, use a marker for each criterion, which also lets `pytest -m AC_12` run them:

```
@pytest.mark.ac("AC-12", reviewed="7a2439b")
```

Only test files count, and a tag counts only in a test's title or in a comment directly above a test (in pytest,
only the marker). A skipped test does not count. Use one tag for each criterion: a list such as `Verifies AC-5, AC-63`
cannot carry a review hash and `stamp` refuses it. `stamp AC-5` never touches `AC-57`. The report also shows
criteria deferred to R2 (notes start with `R2`), criteria covered only by the stack run, and rule tags
(`@pytest.mark.rule("RULE-A3")`, `(Verifies RULE-A3)`) that name no rule, and rules with no test.

The hash is a short fingerprint of the criterion (given, when, then, level), the same one `vbench-uc` keeps.
If the criterion changes, the test is **stale** until a person checks it and runs `stamp`. A change to the
criterion's `notes` does not count. Stamping is the act of review, so never stamp to make a warning go away.

## Steps

1. **Scope.** Say what you are examining: one criterion, one use case, or the whole list. Take one criterion at
   a time when writing.
2. **Facts first.** Run `report` (with `--release R1` when the work is Release 1) or `show AC-ID`. Report the
   result in plain words. Say plainly when the tests folder does not exist yet.
3. **Is the criterion testable as written?** Read it against `references/questions.md` section 5. If it is
   vague, holds two outcomes, names a screen and not a result, or belongs at another level, **do not patch it
   here**: hand it to vbench-req with what is wrong, and stop for that criterion.
4. **Details.** If there are no acceptance tests yet, confirm the default (pytest against the FastAPI API) and ask
   the API and database questions (sections 1 and 2). Skip a question the repo already answers.
5. **Draft.** Run `skeleton AC-ID --stack ...` without `--write` and show it. Ask before writing. On Accept,
   run it with `--write`, then run the new test and say that it fails, which is the point. The skeleton stops here:
   the real failing test, with its assertions, is written by `vbench-tdd-red` (through `vbench-tdd`).
6. **The person writes the checks.** Offer to help only when asked. The checks must use things a person can
   observe through the API: a status, a body, a visible side effect. If the API does not exist yet, say that
   the test waits for the use case's first slice.
7. **Review and stamp.** After the person confirms the test matches the criterion, run `stamp AC-ID`.
8. **Commit.** A new failing test is its own `test(UC-...)` commit (vbench-commit), then the code that makes it
   pass. Do not commit unasked.

## Hand-offs

- **Back to vbench-req** when a criterion is wrong, missing, vague or at the wrong level. Say which criterion
  and why. vbench-req changes the row after the owner accepts. This skill never does.
- **To vbench-ontology** when a test needs a rule or an object that has no ontology file.
- **From vbench-uc** when a use case lists criteria with no test: that is where this skill starts.

## Rules that matter

- One test runs one criterion. If a test needs two criteria, it is two tests or the criteria are wrong.
- Never write an assertion the criterion does not state. Never copy an expected value from nowhere.
- A skeleton fails on purpose. A green placeholder would count as proof of nothing.
- Use the project's own words (its vocabulary and ontology). No em dashes or en dashes anywhere.
- Ask before writing any file. Do not commit or push unasked.

## Example

User: `/vbench-at which release 1 criteria have no test`

You: run `report --release R1`. Say: "41 acceptance criteria, and `tests/acceptance` does not exist yet, so none
has a test. There is no use case file yet either." Confirm the default (pytest against the FastAPI API), ask the API and database questions, then offer the skeleton for
AC-1 ("a pending account; an administrator approves it; the account is active and the person can sign in").
