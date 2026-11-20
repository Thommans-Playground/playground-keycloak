"""POST /projects through the HTTP client: UC-P1 acceptance level for slice TSK-P1.3 (AC-9, AC-10), and the wiring."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.access.adapters.outbound.token_verifier import JwtTokenVerifier
from app.infrastructure.config import Settings
from app.main import create_app
from app.projects.adapters.outbound.sql import SqlProjects
from tests.conftest import AUDIENCE, ISSUER, KEY, auth, make_engine, me_id, register
from tests.fakes import FakeIdp, FakeSecurityLog
from tests.migrations_support import drop_everything, owner_engine
from tests.test_api import _api_routes

PLACEHOLDERS = {"files": [], "endpoints": [], "evaluations": []}


@pytest.fixture
def engine():
    engine = make_engine()
    yield engine
    engine.dispose()
    if os.environ.get("TEST_DATABASE_URL"):
        owner = owner_engine()
        drop_everything(owner)
        owner.dispose()


@pytest.fixture
def api(engine):
    settings = Settings(keycloak_url="http://kc.test", bootstrap_admin_emails="ada@x.test")
    verifier = JwtTokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key())
    return TestClient(create_app(settings, verifier, FakeIdp(), engine, FakeSecurityLog()))


@pytest.fixture
def admin(api):
    h = auth("sub-ada", "ada@x.test", name="Ada")
    assert api.get("/me", headers=h).json()["role"] == "administrator"
    return h


def stored(engine, project_id):
    with Session(engine) as s:
        return SqlProjects(s).by_id(project_id)


@pytest.mark.ac("AC-9")
def test_an_administrator_creates_a_project_naming_an_active_account(api, admin, engine):
    maya_h, maya_id = register(api, "sub-maya", "maya@x.test")
    api.post(f"/accounts/{maya_id}/approve", headers=admin)

    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]})

    assert r.status_code == 201
    body = r.json()
    assert str(uuid.UUID(body["id"])) == body["id"]
    assert (body["name"], body["created_by"], body["members"]) == ("Alpha", me_id(api, admin), [maya_id])
    assert {k: body[k] for k in PLACEHOLDERS} == PLACEHOLDERS
    assert set(body) == {"id", "name", "created_by", "members", *PLACEHOLDERS}
    project = stored(engine, body["id"])  # a later read through the repository
    assert (project.name, project.members) == ("Alpha", {maya_id})


@pytest.mark.ac("AC-10")
def test_an_administrator_naming_themselves_is_a_member(api, admin, engine):
    ada_id = me_id(api, admin)
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [ada_id]})
    assert (r.status_code, r.json()["members"]) == (201, [ada_id])
    assert stored(engine, r.json()["id"]).members == {ada_id}


@pytest.mark.ac("AC-10")
def test_an_administrator_naming_nobody_makes_a_project_with_no_member(api, admin, engine):
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": []})
    assert (r.status_code, r.json()["members"]) == (201, [])
    assert stored(engine, r.json()["id"]).members == frozenset()


def test_two_projects_have_two_different_ids(api, admin):
    ids = {api.post("/projects", headers=admin, json={"name": "Alpha", "members": []}).json()["id"] for _ in range(2)}
    assert len(ids) == 2


def test_the_route_is_behind_the_access_guard_chain(api):
    assert api.post("/projects", json={"name": "Alpha", "members": []}).status_code == 401
    h, _ = register(api, "sub-new", "new@x.test")  # pending
    r = api.post("/projects", headers=h, json={"name": "Alpha", "members": []})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "account_pending")


def test_the_project_route_is_served_by_the_projects_context(api):
    modules = {r.endpoint.__module__ for r in _api_routes(api.app) if r.path == "/projects"}
    assert modules == {"app.projects.adapters.inbound.http"}
