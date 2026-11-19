# 0006 A test pyramid, and an isolated stack for the top

- Status: accepted
- Date: 2026-11-19
- Decided by: together

## Context
Unit and use case tests use fakes. Real Keycloak behaviour (redirects, cookies, tokens) had only been checked by hand once.

## Decision
Levels: unit, use case with fakes, adapter (mock and against a real Keycloak), acceptance over HTTP with no browser. The upper levels run only with INTEGRATION=1, take their addresses from environment variables, make throwaway users, and fail when the stack is down. scripts/test-stack.sh starts a fresh isolated stack for CI.

## Consequences
The top levels are slower and need Docker. The default test run does not execute them, so a green default run says nothing about the thin layer (cookies, PKCE, nonce, state). CI must run the stack job.

## Links
docs/TESTING.md; scripts/test-stack.sh; apps/web/src/testing/stack.ts; apps/api/tests/integration.
