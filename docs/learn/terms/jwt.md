---
term: JWT
say: A JWT is a signed token: three parts, readable by anyone, impossible to change without breaking the signature.
aliases: [JWT, JSON Web Token, bearer token]
code:
  - apps/api/app/access/adapters/outbound/token_verifier.py :: RS256
guide: 1.9 Tokens
check: Which five things does the API check before it believes a token?
---

## In one line

A JSON Web Token has a header, a set of claims (who, for whom, until when) and a signature. Anyone can read it. Only the holder of Keycloak's private key can sign it.

## Why we need it

The API trusts a token only if the signature is valid and the claims make sense. It checks the signature, that it has not expired, that Keycloak issued it (`iss`), that it was made for this API (`aud`), and that it uses an allowed algorithm. Anything else is refused with 401 and nothing is created (AC-33). The token says who the person is. What they may do is looked up in our own database on every request.

## In our code

`JwtTokenVerifier` in `token_verifier.py` decodes with `algorithms=["RS256"]` and the issuer and audience it was built with. A token that says `alg: none` is refused.

## Look for yourself

Study guide experiment 3: get a real token, decode it, then watch the API reject a tampered copy.
