---
name: vbench-vcycle
description: Trace the V cycle of a use case and say, as facts, what is proved, what is not and what a person still has to do. One table with a row for each level (requirements, criteria and their tests, flow and analysis, rules and their tests, design and diagrams, slices, review stamps), ok, warn or FAIL for each, and an exit code. Use whenever the user says "vbench-vcycle", "trace the V cycle", "is UC-A1 verified", "is this use case ready", "what is missing for UC-A4", "does every criterion have a test", "can I merge", or has just finished a slice and wants to know where the use case stands, even if they never say "vbench".
---

# vbench-vcycle

A use case is **verifiable** when every level of its specification has something that proves it, the links are
recorded, and a person has reviewed them. This skill joins the checks the other tools already make into one answer for
one use case.

It reads files and runs nothing. It says a tagged test EXISTS, not that it passes or that it is any good. The test runs
(`/vbench-test-stack`) and the owner's review are separate, and this skill never replaces them. It never edits a file.

## The command

`python3 .claude/skills/vbench-vcycle/scripts/vcycle.py` from the repo root:

```
vcycle.py UC-A1               one use case, one row for each level of the V
vcycle.py --all               every use case, and a summary (a use case whose header cannot be read is a FAIL, and
                              checking none is a failure, not a pass)
vcycle.py UC-A1 --strict      warnings fail too (the gate to use before a release)
vcycle.py --all --json        the same as data, with the commit it was run on: keep it as the record of a run
vcycle.py --results junit.xml count a criterion as tested only when its test PASSED in this JUnit file
                              (or set `results` in vbench.json); without it the trace checks existence only, and says so
vcycle.py --all --baseline write   record today's failing rows (an owner's act); later runs show them as known gaps,
                              and only a new or changed failure fails. `--no-baseline` ignores the file
```

Exit code 1 when anything FAILS (with `--strict`, when anything warns too).

## The rows

| Row | Left of the V (specification) | Right of the V (proof) | FAIL when | warn when |
|---|---|---|---|---|
| Requirements | the requirements it serves | a listed criterion for each | | a requirement has no listed criterion |
| Criteria | the criteria it lists | a tagged test for each | a criterion has no test; a listed one is retired or missing; a test review hash is stale; with results, the test failed | stack run only; the test has no assertion; one tag names several criteria; a deferral to R2 cites no decision; with results, no result for the test |
| Analysis | analysis revisions, design, change log | every element traced | an analysis element has no log entry | not frozen, or no analysis yet (a `tier: small` use case needs neither) |
| Rules | the ontology rules it lists | a tagged test for each | a rule has no test | stack run only, or no ontology file |
| Design | the Design section | the linked diagrams exist | | a diagram is missing, or there is no Design section |
| Slices | the slices | each names its criteria and rules | a slice is malformed | a note from the use case tool |
| Security | criteria whose Notes start with `security` or name a `SEC-` check | a tagged test for each | a security criterion has no test | stack run only, a retired security criterion, or none marked yet ("not probed": run `/vbench-security-test`) |
| Review | the stamps on every link | fresh review hashes | a stamp is stale (the row changed since review) | not stamped |

A tag counts only on a test that really runs: a Python marker is read with `ast` (not in a string, on a helper, under a
skip in any order, in a skipped module, or on a test that skips itself), and a JS tag is not on `xit`, `.todo`,
`.fixme`, `skipIf` or `runIf`. A test whose body asserts nothing is a warning, never a proof.

## How far an area is adopted (strangler, ADR 0019)

`vbench.json` `adoption` says, for each area letter (UC-**A**1), `legacy`, `adopting` or `adopted` (default `adopted`).
**legacy**: rows that would warn or fail show as `legacy` and the use case is observed only. **adopting**: a FAIL
shows as a warning. **adopted**: as above. `packs` turns whole groups of rows off (a project without the `ddd` pack has no
Analysis, Rules or Design rows; without `security`, no Security row). Neither hides anything quietly: the JSON says which.

## Steps

1. **Run it** for the use case, then `--all` if the question is about the whole product.
2. **Report the table as it is**, with the numbers, and the exit code. Do not soften a FAIL and do not call a use case
   verified because it has no FAIL: an unstamped use case is not reviewed.
3. **Turn each FAIL and warn into one next step**, and say who does it:
   - criterion with no test: `/vbench-at`, then `/vbench-tdd` (an agent can do it);
   - rule with no test: tag the unit test that proves it, or write one;
   - security not probed, or a security criterion with no test: `/vbench-security-test <UC>` proposes the abuse-case criteria for a person to approve, then `/vbench-tdd` writes the failing test;
   - stack-run-only: it needs `/vbench-test-stack` to be run, say so;
   - analysis not frozen, not stamped, stale: **the owner reads it and runs `uc_tool.py freeze` and `stamp`**. Offer ONE
     review summary (every unstamped or stale link with what changed since it was reviewed), so the owner reads once and
     stamps together after a single yes. Never stamp without that reading. Never
     do that from here, and never in bulk to clear a warning.
4. **Say what the table does not prove**: that the tests pass (run `/vbench-test-stack`), that a test checks what the
   criterion says (the tag is a claim), and that a person has read it.

## Not the same as

- `uc_tool.py validate` checks one use case file for form and links. `vcycle` adds the tests and the review.
- `at_tool.py report` lists criteria and rules with no test across the product. `vcycle` asks it use case by use case.
