# The python-fastapi stack: layout and conventions

For a project scaffolded with `vbench init` (config key `stack = "python-fastapi"`). The choices are recorded as
accepted decision records and in `04-technology-stack.md`; a design is checked against them in the constitution check.
To depart from one, write an ADR that supersedes it. If the project has no stack, use `ddd-hexagonal.md` alone.

## Layout (one package per bounded context)

```
src/<package>/
  main.py                       the FastAPI app: the composition root, where routers and adapters are wired
  config.py                     pydantic-settings; every environment-specific value comes from here
  infrastructure/               technical plumbing shared by contexts (database sessions, clients); no business rules
  shared_kernel/                the tiny vocabulary every context shares (ids, money, time)
  <context>/                    created by `vbench new context --name "<Context>"`
    domain/                     aggregates, value objects, domain events, domain errors. Imports no framework
    application/
      ports/                    the interfaces the use cases need (repositories, gateways), as Protocols
      use_cases/                one module per behaviour the context offers
    adapters/
      inbound/                  FastAPI routers (and consumers) that call the use cases
      outbound/                 SQLAlchemy repositories and httpx clients that implement the ports
    public.py                   the only module another context may import (create it when one is needed)
```

`vbench new context` also writes the architecture contract (`.importlinter`). Run it with `uv run lint-imports`, the
`boundaries` gate. It fails on: a framework import in `domain` or `application`, `adapters` imported by
`application` or `domain`, `application` imported by `domain`, and one context importing another except through `public`.

## Conventions

- **FastAPI is a driving adapter.** A router parses the request into a Pydantic model, calls one use case, and maps the
  result back. No rules in routers. Dependencies (repositories, sessions) are injected with `Depends` and wired in `main.py`.
- **Two kinds of model.** Pydantic models describe the API and live in `adapters/inbound`. Domain objects are plain
  classes or dataclasses in `domain`. Map between them by hand; that is the point of the boundary.
- **Persistence.** SQLAlchemy 2.0 models live in `adapters/outbound` and are never imported by the domain. A repository
  port in `application/ports` has a SQLAlchemy adapter and, for fast tests, an in-memory one. A use case owns its
  transaction. Each schema change is an Alembic migration, noted in the use-case spec.
- **Errors.** The domain raises its own errors; the inbound adapter maps them to status codes at the boundary.
- **Configuration and secrets.** `Settings` reads `APP_*` variables. Never commit `.env`.
- **Outbound HTTP** (httpx) sits behind a port in an anti-corruption adapter, so a vendor's shapes never reach the domain.
- **Optional modules** (Celery and Redis, the auth kit, the agent kit, observability) each need their own ADR.

## Tests, mapped to the rungs

| Rung | What | How |
|---|---|---|
| unit | an aggregate, a value object, a use case with in-memory ports | plain pytest, no I/O |
| integration | a repository against PostgreSQL, an outbound client | the compose `db` service locally, a service container in CI |
| system | several contexts or the whole pipeline | through the public modules |
| acceptance | a criterion, through the public interface | `fastapi.testclient.TestClient` against `create_app()` |

Tag them as `references/tdd-and-tagging.md` says (`@pytest.mark.ac("AC-…")`, `Verifies UC-… · unit rung.`).

## Commands

`uv sync` (commit `uv.lock`), `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`,
`uv run lint-imports`, `docker compose up --build`. Ruff both lints and formats; there is no separate formatter.
The `[commands]` in `.vbench/config.toml` already hold these, so `scripts/run_gates.py` runs them as the task gate.
