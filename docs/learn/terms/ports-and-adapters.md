---
term: Ports and adapters
say: A port is an interface our code owns for something outside it. An adapter is the piece that plugs a real thing into it.
aliases: [hexagonal, hexagon, ports and adapters, port and adapter, adapter]
code:
  - apps/web/src/application/ports.ts :: IdentityProvider
  - apps/api/app/access/application/ports.py :: TokenVerifier
  - docs/adr/0001-hexagonal-architecture.md
check: What would you change to move the database to Amazon RDS, and what stays the same?
---

## In one line

The rules of the product live in a pure domain that imports nothing from outside. Everything outside (the database, Keycloak, the session store) sits behind a port, and an adapter implements it.

## Why we need it

It keeps the rules testable with fakes, and it makes swaps cheap: to move from PostgreSQL to RDS, or to change how tokens are checked, we change an adapter and the domain does not move. Tests fail if a boundary is crossed.

## In our code

`IdentityProvider` in the web `application/ports.ts` and `TokenVerifier` in the API `ports.py` are ports. ADR 0001 records the decision.

## Look for yourself

Run `cd apps/api && uv run pytest tests/test_architecture.py`, then try adding a forbidden import and see it fail.
