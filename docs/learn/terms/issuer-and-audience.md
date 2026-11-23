---
term: Issuer and audience
say: The issuer (`iss`) says who made a token. The audience (`aud`) says which service it was made for. The API checks both.
aliases: [issuer, audience, iss, aud, iss claim, aud claim]
prereq: [jwt]
code:
  - apps/api/app/access/adapters/outbound/token_verifier.py :: issuer
  - apps/api/app/access/adapters/outbound/token_verifier.py :: audience
guide: 1.9 Tokens
check: A valid Keycloak token was made for another API in the same realm. Why must our API still refuse it?
---

## In one line

Two claims inside a token. `iss` names the server that signed it. `aud` names the service allowed to accept it.

## Why we need it

A good signature only proves Keycloak signed the token. It does not prove the token was meant for us. Without the `iss` check we might trust a token from some other server. Without the `aud` check, a token made for another service could be replayed against ours.

## In our code

`JwtTokenVerifier.verify` passes `audience=self.audience` and `issuer=self.issuer` to `jwt.decode`, and requires `iss` and `aud` to be present at all. `from_jwks` fetches keys from an address we can reach, while the issuer checked is the public one.

## Look for yourself

Decode a real access token (study guide experiment 3) and find `iss` and `aud`. Change one letter of either in a test and watch the verifier refuse it.
