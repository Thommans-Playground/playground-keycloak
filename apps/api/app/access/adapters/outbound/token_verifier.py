"""Check the Keycloak access token: signature, expiry, issuer, audience (NFR-1, NFR-1)."""

from typing import Callable

import jwt
from jwt import PyJWKClient

from app.access.application.ports import InvalidToken, Principal


class JwtTokenVerifier:
    def __init__(self, issuer: str, audience: str, signing_key: Callable[[str], object]):
        self.issuer, self.audience, self._signing_key = issuer, audience, signing_key

    @classmethod
    def from_jwks(cls, issuer: str, audience: str, realm_url: str | None = None) -> "JwtTokenVerifier":
        # Keys are fetched from where we can reach Keycloak. The issuer checked is the public one.
        client = PyJWKClient(f"{realm_url or issuer}/protocol/openid-connect/certs", cache_keys=True)
        return cls(issuer, audience, lambda token: client.get_signing_key_from_jwt(token).key)

    def verify(self, token: str) -> Principal:
        try:
            claims = jwt.decode(
                token,
                self._signing_key(token),
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except Exception as exc:  # bad signature, expired, wrong issuer, JWKS unreachable
            raise InvalidToken(str(exc)) from exc
        email = claims.get("email")
        if not email:
            raise InvalidToken("token has no email claim")
        return Principal(
            identity=claims["sub"],
            name=claims.get("name") or claims.get("preferred_username") or email,
            email=email,
            email_verified=bool(claims.get("email_verified")),
        )
