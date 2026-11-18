import os
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.access.adapters.sql import Base
from app.auth import TokenVerifier
from app.config import Settings
from tests.fakes import FakeIdp
from tests.safety import check_test_database
from app.main import create_app

ISSUER = "http://kc.test/realms/playground"
AUDIENCE = "playground-api"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def make_token(sub: str, email: str, name: str = "Test Person", *, verified: bool = True, key=KEY,
               issuer: str = ISSUER, audience: str = AUDIENCE, expires_in: int = 300) -> str:
    claims = {"sub": sub, "email": email, "name": name, "email_verified": verified, "iss": issuer,
              "aud": audience, "exp": int(time.time()) + expires_in}
    return jwt.encode(claims, key, algorithm="RS256")


@pytest.fixture
def idp():
    return FakeIdp()


def make_engine():
    """SQLite in memory by default, so a test run needs nothing and stays fast.
    Set TEST_DATABASE_URL to run the same tests on PostgreSQL, the engine of Amazon RDS."""
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        engine = create_engine(check_test_database(url))  # refuses a database that is not named *_test
        Base.metadata.drop_all(engine)  # a clean slate for each test: create_app makes the tables
        return engine
    return create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


@pytest.fixture
def client(idp):
    settings = Settings(keycloak_url="http://kc.test", bootstrap_admin_emails="ada@x.test")
    engine = make_engine()
    verifier = TokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key())
    return TestClient(create_app(settings, verifier, idp, engine))


def auth(sub: str, email: str, **kw) -> dict:
    return {"Authorization": f"Bearer {make_token(sub, email, **kw)}"}


@pytest.fixture
def admin(client):
    """Ada, the bootstrap administrator, already has her account."""
    h = auth("sub-ada", "ada@x.test", name="Ada")
    assert client.get("/me", headers=h).json()["role"] == "administrator"
    return h


def register(client, sub: str, email: str) -> tuple[dict, str]:
    h = auth(sub, email, name=email.split("@")[0])
    return h, client.get("/me", headers=h).json()["id"]


def me_id(client, headers) -> str:
    return client.get("/me", headers=headers).json()["id"]
