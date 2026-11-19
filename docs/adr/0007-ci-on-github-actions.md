# 0007 CI on GitHub Actions, with a fresh stack job

- Status: accepted
- Date: 2026-11-19
- Decided by: the agent

## Context
Nothing ran the tests except the agent and the owner. The process review found that the integration tests had only run
against the dev stack, and that a green default run says nothing about the thin layer (cookies, PKCE, nonce, state).

## Decision
`.github/workflows/ci.yml` runs on every pull request and on pushes to main, in four jobs: the API tests on SQLite and on
a PostgreSQL service, the web tests with lint, typecheck and build, the traceability tools and tag report, and a fresh
stack job that calls `scripts/test-stack.sh run` (its own compose project, wiped at the end). The use case check is
informational until a person has stamped the use cases. Dependabot opens weekly updates for npm, uv, Docker and Actions.

## Consequences
A pull request cannot show green without the stack tests. The stack job is slow (image builds) and needs Docker on the
runner. Branch protection with a required human review and these checks is a setting in GitHub, not a file, so it is a
manual step. Secret scanning, a dependency audit and a container scan are not in the workflow yet.

## Links
ADR 0006; docs/TESTING.md; scripts/test-stack.sh; the skill vbench-test-stack.
