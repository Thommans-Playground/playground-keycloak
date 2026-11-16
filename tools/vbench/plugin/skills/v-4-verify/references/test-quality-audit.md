# Test-quality audit

`vbench check` proves a link exists. This audit asks whether the test deserves trust. Flag each finding with
`file:line` and a severity.

| Finding | Why it matters | Severity |
|---|---|---|
| No assertion, a swallowed exception, or `assert True` | passes while proving nothing | Blocking |
| An AC marker on a test that does not check that AC's behaviour | closes the gate falsely | Blocking |
| Mocks of the project's own services or repositories | the test dies in any internal refactor and hides integration bugs | Should fix |
| Assertions on private state or call order, not behaviour | same | Should fix |
| Network, clock or credential dependence without a seam | flaky, not reproducible in CI | Should fix |
| Docstring rung does not match what runs (a "unit" test that hits the database) | the ascent order stops meaning anything | Should fix |
| Only the happy path where the spec lists an exception flow | the failure behaviour is unverified | Should fix |
| `skip` / `xfail` left behind (except an explicit scaffold skip) | silently shrinks coverage | Should fix |
| Production code tagged `Realises UC-<id>` with no test that would fail if it were removed | dead or unverified code | Should fix |

## Mutation thought experiment
For each AC test ask: if I deleted or inverted the line it covers, would this test fail? If not, it is not
verifying that line.
