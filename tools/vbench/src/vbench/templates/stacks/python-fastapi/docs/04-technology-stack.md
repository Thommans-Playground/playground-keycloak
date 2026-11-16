# 04 - Technology stack

> **What this is.** The stack this project is built on, as decisions rather than preferences. It is the default that
> `vbench init` scaffolds. Each choice is recorded in the [decision records](02-architecture-decision-record.md);
> to depart from one, add a decision record that supersedes it. `/vbench:v-2-design` checks every design against them.

The backend is FastAPI on Python with PostgreSQL, organised as ports and adapters around DDD bounded contexts. Docker
gives the same environment in development and CI. A frontend, when the product needs one, is Next.js with TypeScript
and Tailwind CSS.

## Backend

| Layer | Technology | Why |
|---|---|---|
| Language | Python 3.13 | Mature ecosystem; strong type hints, checked by mypy |
| Dependency manager | uv | Fast, with a lockfile that pins every version (`uv.lock` is committed) |
| Web framework | FastAPI | Async-native, OpenAPI generated, Pydantic integrated. A **driving adapter only** |
| ASGI server | uvicorn | Production-grade server for FastAPI |
| Validation | Pydantic | Schemas and validation at the API boundary |
| Configuration | pydantic-settings | Every environment-specific value is read from the environment, not code |
| ORM | SQLAlchemy 2.0 | Battle-tested; typed; sync and async engines |
| Database driver | psycopg 3 (`psycopg[binary]`) | One driver for the API and any worker |
| Migrations | Alembic | Versioned schema changes; a migration is part of the change that needs it |
| HTTP client | httpx | Outbound calls, kept inside anti-corruption-layer adapters |

## Architecture

| Choice | Rule | Enforced by |
|---|---|---|
| **Ports and adapters** | The domain depends on nothing. Ports are defined by the application layer; adapters implement them | `lint-imports`, the `boundaries` gate |
| **DDD** | One package per bounded context: `domain`, `application` (use cases and ports), `adapters` (`inbound`, `outbound`) | The same contract, plus design review |
| **No framework in the core** | `domain` and `application` import no FastAPI, SQLAlchemy, psycopg or httpx | `lint-imports` |
| **Contexts are independent** | A context reaches another only through that context's `public` module | `lint-imports` |

## Frontend (when the product has a UI)

| Layer | Technology | Why |
|---|---|---|
| Framework | Next.js (App Router) | Server components and route handlers (a backend-for-frontend) |
| Language | TypeScript | Type safety |
| UI | React, shadcn/ui (Radix), Tailwind CSS | Accessible primitives, fully customisable, utility-first styling |
| Data table | TanStack Table | Headless, composable |
| Charts | ECharts | Rich charts for dashboards |
| Tests | Vitest | Fast unit tests |
| Lint and format | ESLint, Prettier | Style consistency on the TypeScript side |

## Development tools

| Tool | Purpose | Gate |
|---|---|---|
| **Ruff** | Linting **and** formatting (one tool; there is no separate formatter) | `ruff check`, `ruff format --check`, both enforced |
| mypy | Static type checking | enforced |
| pytest, pytest-cov | Test runner and coverage | enforced |
| import-linter | The architecture rules above | enforced |
| PlantUML, Mermaid | Diagram source, versioned with the code | `vbench check diagrams` |

## Infrastructure and security

| Layer | Technology | Why |
|---|---|---|
| Database | PostgreSQL | ACID; JSON columns absorb heterogeneous payloads |
| Containers | Docker and Docker Compose | Reproducible development, a CI build target and a path to production |
| CI/CD | GitHub Actions (GitLab CI is scaffolded too) | Native, parallel jobs |
| Static analysis | Bandit (and Ruff's `S` rules) | Python security checks, enforced |
| Dependencies | pip-audit, npm audit | Known-vulnerability scan, informational |
| Images | Trivy | CRITICAL and HIGH CVEs on built images, run nightly |
| Web scan | OWASP ZAP | Baseline scan, informational |

## Optional modules

Not part of the default. Adopt one by its own decision record, so the choice and its reason are written down.

| Module | Technology | Adopt it when |
|---|---|---|
| Background work | Celery with Redis | Long-running or concurrent tasks must not block a request |
| Auth kit | bcrypt, PyJWT, cryptography (Fernet) | The product owns user credentials, sessions or encrypted secrets |
| Agent kit | LangGraph, LangChain, OpenAI SDK | The product has an assistant behind a port |
| Observability | Prometheus, Grafana, Loki, Promtail, prometheus-fastapi-instrumentator | You need metrics and logs beyond the platform's own |
| Registry | Amazon ECR (or your platform's) | Images are deployed to AWS |

## Commands

```bash
uv sync                      # install, and write uv.lock the first time (commit it)
uv run uvicorn {{PACKAGE}}.main:app --reload    # the API on http://127.0.0.1:8000/docs
uv run ruff check . && uv run ruff format --check .
uv run mypy .
uv run lint-imports          # the architecture rules
uv run pytest
docker compose up --build    # the API and PostgreSQL
```
