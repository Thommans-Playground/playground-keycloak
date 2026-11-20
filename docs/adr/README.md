# Architecture decision records

One short file for each **technical** decision: how the system is built. The owner's decisions (scope, people, who may do
what, accepted risk) stay in [docs/domain/decisions.md](../domain/decisions.md).

- File name: `NNNN-short-title.md`, numbered from 0001, never renumbered.
- Fields: status (proposed, accepted, superseded by NNNN), date, context, decision, consequences, links.
- A decision is never edited to change its meaning. A new record supersedes it, and the old one says so.
- Keep each to one page. If you need more, it is a design, and it belongs in the use case or a class diagram.

| ADR | Decision |
|---|---|
| [0001](0001-hexagonal-architecture.md) | Domain driven design with ports and adapters, on both sides |
| [0002](0002-caller-value-object.md) | Projects receive a Caller, and never look a role up |
| [0003](0003-audit-as-its-own-context.md) | The audit trail is its own bounded context |
| [0004](0004-alembic-migrations.md) | Database migrations with Alembic |
| [0005](0005-tests-tagged-with-markers.md) | Tests name the criterion or rule they prove |
| [0006](0006-test-pyramid-and-isolated-stack.md) | A test pyramid, and an isolated stack for the top |
| [0007](0007-ci-on-github-actions.md) | CI on GitHub Actions, with a fresh stack job |
| [0008](0008-vcycle-report.md) | One deterministic V cycle report, no model |
| [0009](0009-commit-before-keycloak-and-lock-administrators.md) | Commit a deactivation before calling Keycloak, and lock the administrators (accepted; the audit outcome part is superseded by 0011) |
| [0010](0010-context-folder-layout.md) | One folder layout for every bounded context in the API |
| [0011](0011-audit-context-append-only.md) | The Audit context, append only, enforced by the database |
| [0012](0012-migrations-outside-the-app.md) | Migrations live in `apps/api/migrations/`, outside the app, and run as the owner role |
