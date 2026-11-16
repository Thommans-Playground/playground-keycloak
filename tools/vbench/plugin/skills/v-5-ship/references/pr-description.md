# Pull request description

Title in the commit style: `feat(UC-A-001): add login with lockout`.

```markdown
## Summary
<The behaviour that changes and why, in a short paragraph. Not a list of files.>

## Traceability
<Paste the table from scripts/pr_draft.py; fill the "Maturity" column by hand.>

## Design notes
<Aggregates, ports and adapters, patterns chosen and the force for each. Link the ADR if one was added.>

## Verification
<The checks run and their results, as they came out. Paste failures, do not paraphrase them.>

## Schema / migration
<New or changed columns and how an existing database is migrated, or "none".>

## Known gaps
<What is deferred and where it is recorded in the spec.>
```

Rules: state results as they came out (a skipped step is "skipped", not "passed"); do not claim a rung is
closed that the matrix shows open; never edit CI workflows as part of shipping.
