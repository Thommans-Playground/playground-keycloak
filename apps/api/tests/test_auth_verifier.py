"""TokenVerifier with a real JWKS served over HTTP by a local server, built as create_app builds it."""

import base64
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import jwt
import pytest
from cryptography.hazmat.primitives import serialization

from app.auth import InvalidToken, TokenVerifier
from tests.conftest import AUDIENCE, ISSUER, KEY, OTHER_KEY, make_token

KID = "key-1"


def _b64(n: int) -> str:
    return base64.urlsafe_b64encode(n.to_bytes((n.bit_length() + 7) // 8, "big")).rstrip(b"=").decode()


def jwk(key, kid):
    nums = key.public_key().public_numbers()
    return {"kty": "RSA", "use": "sig", "alg": "RS256", "kid": kid, "n": _b64(nums.n), "e": _b64(nums.e)}


class JwksServer:
    def __init__(self, keys: dict):
        doc = json.dumps({"keys": [jwk(k, kid) for kid, k in keys.items()]}).encode()

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(doc)

            def log_message(self, *a):
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), H)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def realm_url(self) -> str:
        return f"http://127.0.0.1:{self.port}/realms/playground"

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def jwks():
    s = JwksServer({KID: KEY})
    yield s
    s.stop()


@pytest.fixture
def verifier(jwks):
    # As create_app builds it: the issuer is the public one, the keys come from realm_url.
    return TokenVerifier.from_jwks(ISSUER, AUDIENCE, jwks.realm_url)


def signed(claims_over=None, key=KEY, kid=KID, alg="RS256", drop=()):
    claims = {"sub": "sub-1", "email": "bo@x.test", "name": "Bo", "email_verified": True, "iss": ISSUER,
              "aud": AUDIENCE, "exp": int(time.time()) + 300}
    claims.update(claims_over or {})
    for k in drop:
        claims.pop(k)
    return jwt.encode(claims, key, algorithm=alg, headers={"kid": kid} if kid else None)


def test_a_good_rs256_token_is_accepted_through_the_jwks_fetch(verifier):
    p = verifier.verify(signed())
    assert (p.identity, p.email, p.name, p.email_verified) == ("sub-1", "bo@x.test", "Bo", True)


def test_the_keys_are_fetched_from_the_certs_path_of_the_realm_url():
    seen = []

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.path)
            body = json.dumps({"keys": [jwk(KEY, KID)]}).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    httpd = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        v = TokenVerifier.from_jwks(ISSUER, AUDIENCE, f"http://127.0.0.1:{httpd.server_address[1]}/realms/playground")
        v.verify(signed())
    finally:
        httpd.shutdown()
        httpd.server_close()
    assert seen == ["/realms/playground/protocol/openid-connect/certs"]


# Verifies AC-33
@pytest.mark.parametrize("name,token", [
    ("expired", lambda: signed({"exp": int(time.time()) - 10})),
    ("wrong issuer", lambda: signed({"iss": "http://evil.test/realms/playground"})),
    ("wrong audience", lambda: signed({"aud": "someone-else"})),
    ("missing sub", lambda: signed(drop=("sub",))),
    ("missing exp", lambda: signed(drop=("exp",))),
    ("missing email", lambda: signed(drop=("email",))),
    ("signed by another key, same kid", lambda: signed(key=OTHER_KEY)),
    ("unknown kid", lambda: signed(kid="unknown-kid")),
    ("no kid", lambda: signed(kid=None)),
    ("alg none", lambda: jwt.encode({"sub": "s", "email": "a@x.test", "iss": ISSUER, "aud": AUDIENCE,
                                     "exp": int(time.time()) + 300}, None, algorithm="none",
                                    headers={"kid": KID})),
    ("garbage", lambda: "not.a.jwt"),
])
def test_bad_tokens_are_refused(verifier, name, token):
    with pytest.raises(InvalidToken):
        verifier.verify(token())


# Verifies AC-33 (signed with an algorithm we do not allow)
def test_hs256_token_signed_with_the_public_key_is_refused(verifier):
    pem = KEY.public_key().public_bytes(serialization.Encoding.PEM,
                                        serialization.PublicFormat.SubjectPublicKeyInfo)
    claims = {"sub": "s", "email": "a@x.test", "iss": ISSUER, "aud": AUDIENCE, "exp": int(time.time()) + 300}
    # PyJWT refuses to build this with a PEM key, so build it by hand, as an attacker would.
    def part(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=")
    import hashlib, hmac
    signing = part({"alg": "HS256", "typ": "JWT", "kid": KID}) + b"." + part(claims)
    sig = base64.urlsafe_b64encode(hmac.new(pem, signing, hashlib.sha256).digest()).rstrip(b"=")
    with pytest.raises(InvalidToken):
        verifier.verify((signing + b"." + sig).decode())


def test_a_jwks_server_that_is_down_gives_invalid_token():
    s = JwksServer({KID: KEY})
    url = s.realm_url
    s.stop()  # the port now refuses connections
    v = TokenVerifier.from_jwks(ISSUER, AUDIENCE, url)
    with pytest.raises(InvalidToken):
        v.verify(signed())


def test_a_down_jwks_server_is_a_401_through_the_api():
    """main.py catches InvalidToken only, and verify() wraps every error in it, so a JWKS outage is a 401."""
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from app.config import Settings
    from app.main import create_app
    from tests.fakes import FakeIdp

    s = JwksServer({KID: KEY})
    url = s.realm_url
    s.stop()
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    app = create_app(Settings(keycloak_url="http://kc.test"), TokenVerifier.from_jwks(ISSUER, AUDIENCE, url),
                     FakeIdp(), engine)
    r = TestClient(app).get("/me", headers={"Authorization": f"Bearer {signed()}"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == "invalid_token"
