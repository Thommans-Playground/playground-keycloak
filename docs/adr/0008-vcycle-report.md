# 0008 One deterministic V cycle report, no model

- Status: accepted
- Date: 2026-11-19
- Decided by: together

## Context
The traceability checks were spread over three tools (requirements, use cases, test tags), and none answered "is this use
case verified?" in one place. An agent that summarises them would add a model's mistakes to a question that has an exact
answer.

## Decision
`vbench-vcycle` is a script that reads the recorded links and the test tags and prints one row for each level of the V,
with ok, warn or FAIL and an exit code. It runs no tests and calls no model. A skill wraps it for the chat. CI runs it for
every use case, informationally until a person has stamped them, and keeps its JSON as the record of the run.

## Consequences
The answer is the same every time, and CI can gate on it later (`--strict`). It proves that a tagged test exists, not that
it passes or checks the right thing, so it must be read with the test runs and the owner's review. A criterion with no
test, a rule with no test and a stale stamp fail it. Unstamped, not frozen and stack-run-only only warn.

## Links
ADR 0005, 0006, 0007; docs/TESTING.md; the skill vbench-vcycle.
