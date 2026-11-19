# 0001 Domain driven design with ports and adapters, on both sides

- Status: accepted
- Date: 2026-11-17
- Decided by: together

## Context
The final application runs on AWS, and the prototype uses open source engines locally (PostgreSQL, Keycloak, an in memory session store). The move must be configuration, not a rewrite, and the rules must stay testable without the outside systems.

## Decision
The domain is pure rules and imports nothing outside itself. Everything that touches the outside (database, Keycloak, session store, the API, AWS services) is a port with an adapter, chosen in one place, the composition root. The API has one folder for each bounded context. The web server (BFF) follows the same shape and its pages stay thin. A failing test comes first, and an architecture test on each side fails when a boundary is crossed.

## Consequences
A port and an adapter for each outside system is more files, and a swap becomes one adapter. Rules can be tested in milliseconds with fakes. The in memory session store and its per process lock must be replaced before more than one web task runs.

## Links
decisions 4 and 5 in docs/domain/decisions.md; apps/api/tests/test_architecture.py; apps/web/src/architecture.test.ts; docs/domain/diagrams/access-design.puml and bff-design.puml.
