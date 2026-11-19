"""The TokenVerifier, built as create_app builds it, against real tokens from the running Keycloak."""

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth import InvalidToken, TokenVerifier
from tests.integration import helpers
from tests.integration.helpers import login

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def verifier() -> TokenVerifier:
    s = helpers.settings()
    # Exactly the call in create_app (main.py)
    return TokenVerifier.from_jwks(s.issuer, s.api_audience, s.internal_realm_url)


@pytest.fixture
def token(throwaway_user):
    return login(throwaway_user)


def claims_of(token: str) -> dict:
    return jwt.decode(token, options={"verify_signature": False})


@pytest.mark.ac("AC-33")
@pytest.mark.ac("AC-1")
def test_a_real_token_is_accepted_with_the_right_identity(verifier, token, throwaway_user):
    claims = claims_of(token)
    assert claims["iss"] == helpers.settings().issuer
    assert "playground-api" in ([claims["aud"]] if isinstance(claims["aud"], str) else claims["aud"])
    principal = verifier.verify(token)
    assert principal.identity == throwaway_user.id == claims["sub"]
    assert principal.email == throwaway_user.email


@pytest.mark.ac("AC-33")
def test_a_token_with_a_tampered_signature_is_refused(verifier, token):
    head, payload, sig = token.split(".")
    flipped = ("A" if sig[10] != "A" else "B")
    tampered = ".".join([head, payload, sig[:10] + flipped + sig[11:]])
    with pytest.raises(InvalidToken):
        verifier.verify(tampered)


@pytest.mark.ac("AC-33")
def test_an_expired_token_is_refused(verifier, token, monkeypatch):
    """A real token lives minutes and cannot be re-signed, so the clock PyJWT reads moves past its exp."""
    import datetime as dt

    import jwt.api_jwt as api_jwt

    later = dt.datetime.fromtimestamp(claims_of(token)["exp"] + 3600, dt.timezone.utc)

    class Later(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return later

    monkeypatch.setattr(api_jwt, "datetime", Later)
    with pytest.raises(InvalidToken, match="(?i)expired"):
        verifier.verify(token)


@pytest.mark.ac("AC-33")
@pytest.mark.parametrize("change", [{"aud": "someone-else"}, {"iss": "http://evil.test/realms/playground"}])
def test_a_token_resigned_with_our_own_key_and_other_claims_is_refused(verifier, token, change):
    claims = {**claims_of(token), **change}
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    headers = {"kid": jwt.get_unverified_header(token)["kid"]}  # same kid as Keycloak's key, other key
    forged = jwt.encode(claims, key, algorithm="RS256", headers=headers)
    with pytest.raises(InvalidToken):
        verifier.verify(forged)
