---
term: JWKS
say: JWKS is the list of Keycloak's public keys, so the API can check signatures without ever holding a secret.
aliases: [JWKS, JSON Web Key Set, signing keys]
code:
  - apps/api/app/access/adapters/outbound/token_verifier.py :: PyJWKClient
prereq: [jwt]
guide: Match the token's `kid`
check: Keycloak rotates its signing key while a token signed with the old key is still within its lifetime. Is that token accepted, and what has to be true for that?
---

## In one line

Keycloak signs tokens with a private key and publishes the matching public keys at a well-known address. That list is the JSON Web Key Set.

## Why we need it

Each token names the key that signed it in its header (`kid`). The API fetches the list, picks the key with that `kid`, and checks the signature. Because only public keys are involved, the API can verify tokens and cannot make them. Keys are cached, and a new key is fetched when an unknown `kid` appears. When Keycloak rotates, it keeps the old public key published for a while, so tokens signed before the rotation still verify until they expire.

## In our code

`PyJWKClient` in `token_verifier.py` is pointed at the realm's `/protocol/openid-connect/certs` address, which the code writes out by hand. It does not read `jwks_uri` from the discovery document. The client does the fetching and caching.

## Look for yourself

Study guide experiment 4: match a token's `kid` to a key in Keycloak's list.
