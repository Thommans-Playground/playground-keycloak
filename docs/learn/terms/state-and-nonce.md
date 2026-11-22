---
term: State and nonce
say: State and nonce are two random values that tie one sign in to the one browser attempt that started it.
aliases: [nonce, state parameter, state and nonce, login_expired]
code:
  - apps/web/src/adapters/keycloak-identity-provider.ts :: randomState
  - apps/web/src/adapters/keycloak-identity-provider.ts :: randomNonce
  - apps/web/src/domain/login-attempt.ts :: LOGIN_ATTEMPT_TTL_MS
guide: 1.8 `state` and `nonce`
check: What does a sign in do if the person comes back with a state it never made?
---

## In one line

Both are random values we invent for one sign in attempt. `state` comes back in the address, and we check it matches the attempt we saved. `nonce` comes back inside the signed id token, and we check it too.

## Why we need it

`state` stops a sign in we never started from being finished in someone's browser: if the value does not match, we refuse. `nonce` stops an old id token from being replayed into a new attempt. An attempt lives for ten minutes and can be used once, so a stale or repeated return gives `login_expired` and no session is made (AC-38, AC-42).

## In our code

`randomState` and `randomNonce` make the values in the Keycloak adapter. `LOGIN_ATTEMPT_TTL_MS` in `domain/login-attempt.ts` is the ten minutes. The values are checked as `expectedState` and `expectedNonce` when the code is swapped.

## Look for yourself

Study guide experiment 1 shows the `state` in the address. Then try to finish a sign in twice with the same return address and read the answer.
