# Architecture Decision Records

Append-only. To reverse a decision, add a new ADR that supersedes it; never edit or delete an old one.
Write an ADR when a decision is expensive to reverse (a new context, a port/adapter, a schema change, a
security posture, an optional module from the [technology stack](04-technology-stack.md)).

## Template

### ADR-DEC-NNN: Title
- **Status:** proposed | accepted | superseded by ADR-DEC-NNN
- **Context:** the forces at play.
- **Decision:** what we chose, in one or two sentences.
- **Consequences:** what becomes easier, what becomes harder.
- **Realised by:** the use cases (UC-…) that depend on it.

## The stack decisions

These record the default stack. They are accepted from the start so that designs are checked against them.

### ADR-DEC-001: Python 3.13 and uv
- **Status:** accepted
- **Context:** the team is Python-native; builds must be reproducible on every machine and in CI.
- **Decision:** Python 3.13, managed with uv. `uv.lock` is committed, and every command runs through `uv run`.
- **Consequences:** one fast, pinned toolchain. Contributors need uv. A dependency change is a lockfile change.

### ADR-DEC-002: FastAPI as the driving adapter
- **Status:** accepted
- **Context:** the API needs validation, generated documentation and async support without owning business rules.
- **Decision:** FastAPI with Pydantic at the boundary and uvicorn to serve it. Routers translate HTTP into use-case
  calls and hold no rules. Pydantic models describe the API; domain objects are not Pydantic models.
- **Consequences:** the API contract is explicit and documented. Mapping between API models and domain objects is
  written by hand, on purpose, so the domain stays independent of the framework.

### ADR-DEC-003: PostgreSQL with SQLAlchemy 2, psycopg 3 and Alembic
- **Status:** accepted
- **Context:** the product needs a transactional store, and persistence must stay replaceable behind a port.
- **Decision:** PostgreSQL, accessed through SQLAlchemy 2.0 with the psycopg 3 driver. Schema changes are Alembic
  migrations. Repositories are ports in the application layer; the SQLAlchemy ones live in the outbound adapters.
- **Consequences:** ACID guarantees and JSON columns. Tests can use in-memory adapters for speed and PostgreSQL for
  integration. A schema change always comes with a migration and a note in the use-case spec.

### ADR-DEC-004: Ports and adapters with DDD bounded contexts
- **Status:** accepted
- **Context:** the domain must outlive frameworks, and teams must be able to reason about one context at a time.
- **Decision:** one package per bounded context, with `domain`, `application` (use cases and ports) and `adapters`
  (`inbound`, `outbound`). The domain and application layers import no framework. Contexts depend on each other only
  through a `public` module. `import-linter` enforces this as the `boundaries` gate.
- **Consequences:** a violation fails CI instead of surviving review. Adding a context adds a package, a contract and
  a domain-model diagram (`vbench new context`).

### ADR-DEC-005: Ruff, mypy and pytest
- **Status:** accepted
- **Context:** style and correctness should be settled by tools, not discussion.
- **Decision:** Ruff for both linting and formatting (no separate formatter), mypy in strict mode for types, pytest
  with coverage for tests. All of them are enforced gates.
- **Consequences:** one fast tool covers lint and format. Strict typing costs effort up front and pays back in refactors.

### ADR-DEC-006: Docker, Compose and GitHub Actions
- **Status:** accepted
- **Context:** development, CI and deployment should run the same artefacts.
- **Decision:** Docker and Compose for local development (the API and PostgreSQL), GitHub Actions for CI with a
  PostgreSQL service. Bandit is enforced; pip-audit is informational. Trivy runs nightly on built images.
- **Consequences:** a new contributor is one `docker compose up` from a running system.

### ADR-DEC-007: Optional modules are adopted one decision at a time
- **Status:** accepted
- **Context:** background work, an auth kit, an agent kit and an observability stack are real needs for some
  products and dead weight for others.
- **Decision:** none is part of the default. Adopting one (Celery with Redis, bcrypt with PyJWT and Fernet,
  LangGraph, Prometheus with Grafana and Loki, a container registry) needs its own ADR naming the use case that forces it.
- **Consequences:** the default stays small. Each addition is visible and justified.

### ADR-DEC-008: Next.js, TypeScript, Tailwind and shadcn for a frontend
- **Status:** accepted
- **Context:** a product UI needs accessible components, server rendering and a safe place for backend-for-frontend routes.
- **Decision:** Next.js (App Router) with TypeScript, React, shadcn/ui on Radix, Tailwind CSS, TanStack Table, ECharts
  where charts are needed, Vitest for tests, ESLint and Prettier for style.
- **Consequences:** a typed, accessible UI that talks to the API through route handlers. The frontend is a separate
  deployable from the API.
