# Writing acceptance criteria

Each criterion is one row in the spec's AC table: `| **AC-<area>-<nnn>** | Given … when … then … | FR-/NFR- ids |`.

## Rules
- **One behaviour per row.** If the "then" has an "and" joining two outcomes, split the row.
- **Observable through a public interface**: an API response, persisted state, an emitted event, a rendered
  message. Never "the function is called" or "the cache is warm".
- **Testable as written.** Someone who has not seen the code could turn the row into a failing test.
- **Cites what it satisfies** (FR/NFR). A row that satisfies nothing is either missing a requirement or
  not needed.
- **Slug** is kebab-case, names the behaviour, and is never reused (`AC-A-001`, not `AC-A-002`).
- **Cover** the main flow, each alternative and exception flow, and each postcondition.
- Mark a criterion for a flow that is specified but not yet built with `(planned)` in its row; it is then
  not enforced by `vbench check acs`.

## Rewrites

| Vague | Testable |
|---|---|
| Login works correctly | Given a registered user with the right password, when they sign in, then the response is 200 and a session token is returned |
| Handles bad input | Given an email without "@", when the form is submitted, then the response is 422 and names the `email` field |
| Fast search | Given 10 000 records, when a search runs, then the first page returns in under 300 ms (REQ-NFR-003) |
| Admin can approve | Given a pending account, when an admin approves it, then its status is `active` and an audit row records the admin and the time |

## Smells
`TBD` in a row, "etc.", "appropriate", "as needed", a "then" that restates the "when", two actors in one row.
