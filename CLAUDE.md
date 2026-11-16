# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Phase 1 is built: a working Keycloak auth module, from the source specs ([docs/specs/keycloak-auth-module.md](docs/specs/keycloak-auth-module.md)).

- `keycloak-config/`: Docker compose and the `playground` realm import (the part that becomes the `keycloak-config` repo in phase 2).
- `apps/api/`: FastAPI, Python 3.12+, managed with `uv`. `app/domain` is pure rules, `app/ports.py` the ports, `app/adapters` Keycloak admin and SQLAlchemy.
- `apps/web/`: Next.js 16 (App Router, `proxy.ts` not `middleware.ts`), TypeScript, shadcn (Base UI, so `render` not `asChild`), `openid-client`. Read `node_modules/next/dist/docs/` before changing Next code.

Commands: `docker compose up -d --build` at the root runs everything (Keycloak, API, web; the guide is docs/GETTING-STARTED.md); or `docker compose up -d` in `keycloak-config/` for Keycloak alone; `uv run uvicorn app.main:create_app --factory` and `uv run pytest` in `apps/api/`; `npm run dev`, `npm run build`, `npm test`, `npm run lint` in `apps/web/`. Full steps in README.md.

Rules that matter: the token says who, our database says what they may do (roles and status are read on every request); the browser never sees a token; account changes need a reason and are audited. The specs live under `docs/`: `requirements/` (markdown tables), `domain/` (`contexts/`, `ontology/`, `decisions.md`, `diagrams/`) and `usecases/`. `docs/specs/keycloak-auth-module.md` is the build spec distilled from them.

## Project intent

This is a playground for learning Keycloak (per README.md), with two intended phases of work:

1. **Local Keycloak hands-on setup** — running Keycloak (via Docker), configuring realms/clients/users, and wiring a sample app to it over OIDC (Authorization Code + PKCE), then exploring realm export/import, custom themes, and SPIs.
2. **Multi-repo distribution** — packaging the resulting realm config/theme/SPI artifacts into a dedicated `keycloak-config` repo, distributed to other company project repos via Google's `repo` multi-repository tool (a manifest repo referencing `keycloak-config` alongside each product repo, with per-project revision pinning).

When adding code, prefer structuring it around these two phases rather than a generic app layout.
