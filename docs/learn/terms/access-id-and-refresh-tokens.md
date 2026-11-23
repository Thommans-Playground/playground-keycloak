---
term: Access, ID and refresh tokens
say: Three tokens, three jobs: the access token is for the API, the ID token says who signed in, the refresh token gets a new access token.
aliases: [access token, id token, refresh token, id_token_hint]
code:
  - apps/web/src/domain/session.ts :: REFRESH_SKEW_MS
  - apps/web/src/adapters/keycloak-identity-provider.ts :: endSessionUrl
prereq: [openid-connect]
guide: 1.9 Tokens
check: A refresh token leaks from the server session store. What can the thief do with it that a leaked ID token would not allow?
---

## In one line

Keycloak gives us three tokens after a sign in. They look alike and do different jobs.

## Why we need it

The access token is short-lived and is what the API checks. The refresh token lives longer and is only used to get a fresh access token, so the person is not asked to sign in again. The ID token says who signed in; we keep it to tell Keycloak which session to end at sign out (`id_token_hint`). All three stay on our server. The browser never holds one (AC-41).

## In our code

`REFRESH_SKEW_MS` in `domain/session.ts` is the thirty seconds before expiry when we refresh (RULE-A10). `endSessionUrl` builds the sign out address that carries the ID token as a hint.

## Look for yourself

Study guide experiment 6: read a real person's access token in the admin console.
