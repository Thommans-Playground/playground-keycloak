---
term: PKCE
say: PKCE (say "pixie") is a one-time secret that proves the party redeeming the code is the one that started the sign in.
aliases: [PKCE, code verifier, code challenge, code_verifier, code_challenge]
code:
  - apps/web/src/adapters/keycloak-identity-provider.ts :: randomPKCECodeVerifier
  - apps/web/src/adapters/keycloak-identity-provider.ts :: calculatePKCECodeChallenge
prereq: [openid-connect]
guide: 1.7 PKCE
check: A thief copies the code from the redirect address. Which two things do they still lack when they try to redeem it?
---

## In one line

PKCE protects the short-lived `code` that comes back in the address after a sign in. Without it, anyone who could read that address could try to swap the code for tokens. With it, a stolen code alone is not enough. PKCE is a second lock, defence in depth: our client is confidential, so the swap also needs the client secret, which only our server holds.

## Why we need it

Before we leave for Keycloak we make up a random secret, the verifier. We send Keycloak only its fingerprint, the challenge. When we swap the code for tokens we show the secret itself, and Keycloak checks it matches the fingerprint it was given. A thief has the code but not the verifier and not the client secret, so Keycloak refuses.

## In our code

`randomPKCECodeVerifier` makes the secret and `calculatePKCECodeChallenge` makes its fingerprint, both in the Keycloak adapter. The verifier is kept on our server in the login attempt, never in the browser.

## Look for yourself

Study guide experiment 1: find `code_challenge` in the address you are sent to, and notice there is no verifier in it.
