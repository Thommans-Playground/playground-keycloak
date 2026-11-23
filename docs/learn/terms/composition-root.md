---
term: Composition root
say: The composition root is the one place that knows every adapter and wires them into the use cases. Nothing else is allowed to.
aliases: [composition root, composition, wiring, dependency injection]
prereq: [ports-and-adapters]
code:
  - apps/api/app/composition/app.py :: create_app
  - apps/web/src/composition.ts :: build
check: You want to swap the in-memory session store for Redis. Which file do you edit, and why do the use cases not change?
---

## In one line

Domain and use cases ask for ports. One file picks the real adapters and hands them over.

## Why we need it

If a use case imported the database or Keycloak itself, we could not test it with fakes or swap the engine. Keeping every `new` and every import of an adapter in one place keeps the rest pure. Tests build the same wiring with fakes, and an architecture test fails if anything else imports an adapter.

## In our code

On the API, `create_app` in `composition/app.py` builds the engine, the token verifier, the Keycloak admin and the security log, and passes them in. On the web, `build` in `src/composition.ts` builds the identity provider, the stores, the backend client and the log, and returns the use cases the routes call.

## Look for yourself

Open both files and count the adapters they build. Then run `cd apps/api && uv run pytest tests/test_architecture.py`.
