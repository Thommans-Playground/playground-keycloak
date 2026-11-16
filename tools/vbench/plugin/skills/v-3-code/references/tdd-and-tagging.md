# Double-loop TDD, and the tags the checks read

## The loops
- **Outer loop (acceptance rung):** write the task's AC test first, through the public interface. It fails on
  the assertion. It stays red while the inner loop runs, and green means the task is done.
- **Inner loop (unit rung):** one behaviour at a time. RED (a unit test fails on its assertion) → GREEN (the
  least code that passes) → REFACTOR on green only. Do not write the next test before this one is green.
  Start with a tracer bullet: the thinnest path through every layer.
- **Integration rung:** when a seam appears (new port or adapter, a cross-context call, persistence).
- **System rung:** only if the design planned one.

## Red for the right reason
A test is red only if it fails on the **assertion about the missing behaviour**. A collection error, import
error, fixture error or `NameError` is not red. Fix the test until the failure message names the behaviour.

## Tags
Plain text, greppable, read by `vbench check`. Exact forms:

```python
# production code
"""Realises UC-A-001 · Spec: docs/usecase-diagrams/UC-A-001-log-in.md"""


def check_password(user, password):  # Realises UC-A-001 · STP-A-002 (the step the line builds)
    ...


# a test
@pytest.mark.ac("AC-A-001")  # the marker named in config (ac_marker)
def test_wrong_password_is_rejected():
    """Verifies UC-A-001 · STP-A-002, STP-A-003 · acceptance rung."""
```

Rung words: `unit`, `integration`, `system`, `acceptance`. One marker may list several ACs. A `STP-…` id is a step of
the use case's sequence diagram: tag the line that builds it and the test that drives it, and `vbench check steps` and
`vbench trace UC-A-001` read the chain back. A step is owed code and a real test once the use case has code; one marked
`(planned)` in the diagram is not. The `Spec:` path
must exist. Tags prove a link exists; they do not make a test good.

## Commits
One per task when asked: `feat(UC-A-001/TSK-A-002): add login endpoint` (`test`, `refactor` as they fit). The task
row must already be in the spec's Delivery tasks table.
