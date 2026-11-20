import os
import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.access.adapters.outbound.token_verifier import JwtTokenVerifier
from app.infrastructure.config import Settings
from tests.fakes import FakeIdp
from tests.migrations_support import drop_everything, owner_engine, upgrade
from tests.safety import check_test_database
from app.main import create_app

# The integration tests need the running stack: collected only with INTEGRATION=1.
collect_ignore_glob = [] if os.environ.get("INTEGRATION") == "1" else ["integration/*"]

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


def make_empty_engine():
    """The API's engine on an empty database: SQLite in memory by default, so a test run needs nothing and stays fast.
    Set TEST_DATABASE_URL to run the same tests on PostgreSQL, the engine of Amazon RDS."""
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        engine = create_engine(check_test_database(url))  # refuses a database that is not named *_test
        owner = owner_engine()
        drop_everything(owner)  # a clean slate for each test, as the owner
        owner.dispose()
        return engine
    return create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)


def make_engine():
    """An engine on a database that Alembic has brought to head, as the owner (ADR 0012). The app creates no tables."""
    engine = make_empty_engine()
    if os.environ.get("TEST_DATABASE_URL"):
        owner = owner_engine()
        upgrade(owner)
        owner.dispose()
    else:
        upgrade(engine)
    return engine


@pytest.fixture
def client(idp):
    settings = Settings(keycloak_url="http://kc.test", bootstrap_admin_emails="ada@x.test")
    engine = make_engine()
    verifier = JwtTokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key())
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


def pytest_collection_modifyitems(items):
    """Every ac("AC-6") and rule("RULE-A3") marker also becomes a mark named AC_6 or RULE_A3,
    so `pytest -m AC_6` runs the tests that prove that criterion."""
    for item in items:
        for kind in ("ac", "rule"):
            for marker in item.iter_markers(kind):
                if marker.args:
                    item.add_marker(getattr(pytest.mark, str(marker.args[0]).replace("-", "_")))
