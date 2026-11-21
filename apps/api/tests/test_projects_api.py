"""POST /projects through the HTTP client: UC-P1 acceptance level for slice TSK-P1.3 (AC-9, AC-10), and the wiring."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
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
    assert (body["name"], body["created_by"]) == ("Alpha", me_id(api, admin))
    assert body["members"] == [{"id": maya_id, "name": "maya"}]  # the name as Access has it now (ADR 0016)
    assert {k: body[k] for k in PLACEHOLDERS} == PLACEHOLDERS
    assert set(body) == {"id", "name", "created_by", "members", *PLACEHOLDERS}
    project = stored(engine, body["id"])  # a later read through the repository
    assert (project.name, project.members) == ("Alpha", {maya_id})


@pytest.mark.ac("AC-10")
def test_an_administrator_naming_themselves_is_a_member(api, admin, engine):
    ada_id = me_id(api, admin)
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [ada_id]})
    assert (r.status_code, r.json()["members"]) == (201, [{"id": ada_id, "name": "Ada"}])
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


def project_count(engine):
    with Session(engine) as s:
        return s.execute(text("SELECT count(*) FROM projects")).scalar_one()


def active_user(api, admin, sub, email):
    headers, account_id = register(api, sub, email)
    assert api.post(f"/accounts/{account_id}/approve", headers=admin).status_code == 200
    return headers, account_id


@pytest.mark.ac("AC-11")
@pytest.mark.ac("AC-32")
def test_an_ordinary_user_cannot_create_a_project(api, admin, engine):
    maya_h, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    r = api.post("/projects", headers=maya_h, json={"name": "Alpha", "members": [maya_id]})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 0


@pytest.mark.ac("AC-11")
@pytest.mark.ac("AC-32")
def test_a_member_of_other_projects_is_still_not_an_administrator(api, admin, engine):
    maya_h, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    assert api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]}).status_code == 201
    r = api.post("/projects", headers=maya_h, json={"name": "Beta", "members": [maya_id]})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 1


@pytest.mark.ac("AC-11")
def test_the_role_is_checked_before_the_input(api, admin, engine):
    maya_h, _ = active_user(api, admin, "sub-maya", "maya@x.test")
    r = api.post("/projects", headers=maya_h, json={"name": "", "members": ["not-an-account"]})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 0


@pytest.mark.ac("AC-32")
def test_a_demoted_administrator_is_refused_at_once(api, admin, engine):
    """The role is read on every request, not taken from the token (AC-32: the server decides, not the screen)."""
    bo_h, bo_id = active_user(api, admin, "sub-bo", "bo@x.test")
    assert api.post(f"/accounts/{bo_id}/promote", headers=admin, json={"reason": "Covers"}).status_code == 200
    assert api.post("/projects", headers=bo_h, json={"name": "Alpha", "members": []}).status_code == 201
    assert api.post(f"/accounts/{bo_id}/demote", headers=admin, json={"reason": "Back"}).status_code == 200
    r = api.post("/projects", headers=bo_h, json={"name": "Beta", "members": []})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 1


@pytest.mark.ac("AC-94")
def test_every_projects_route_passes_the_guard_chain(api, admin):
    """Walks the route table, so a route a later slice adds under /projects is covered with no edit here."""
    pending, _ = register(api, "sub-new", "new@x.test")
    gone, gone_id = active_user(api, admin, "sub-gone", "gone@x.test")
    assert api.post(f"/accounts/{gone_id}/deactivate", headers=admin, json={"reason": "Left"}).status_code == 200
    bad = {"Authorization": "Bearer not-a-token"}
    routes = [r for r in _api_routes(api.app) if r.path == "/projects" or r.path.startswith("/projects/")]
    assert len(routes) >= 1, "the table must really cover the routes"
    for route in routes:
        path = route.path.replace("{project_id}", str(uuid.uuid4()))
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            body = {"json": {"name": "Alpha", "members": [], "reason": "a reason"}} if method != "GET" else {}
            expected = {
                "no token": ({}, 401, None),
                "bad token": (bad, 401, None),
                "pending": (pending, 403, "account_pending"),
                "deactivated": (gone, 403, "account_deactivated"),
            }
            for who, (headers, status, code) in expected.items():
                r = api.request(method, path, headers=headers, **body)
                assert r.status_code == status, f"{who}: {method} {route.path}"
                if code:
                    assert r.json()["detail"]["code"] == code, f"{who}: {method} {route.path}"


def refused(r, code):
    assert (r.status_code, r.json()["detail"]["code"]) == (422, code)
    assert set(r.json()["detail"]) == {"code", "message"}


@pytest.mark.ac("AC-12")
@pytest.mark.parametrize("bad", ["", "   ", "x" * 101])
def test_a_bad_name_is_refused_with_422_and_nothing_is_created(api, admin, engine, bad):
    refused(api.post("/projects", headers=admin, json={"name": bad, "members": []}), "invalid_project_name")
    assert project_count(engine) == 0


@pytest.mark.ac("AC-12")
def test_a_name_of_100_emoji_is_accepted_and_a_padded_name_is_stored_trimmed(api, admin, engine):
    r = api.post("/projects", headers=admin, json={"name": "\U0001f600" * 100, "members": []})
    assert (r.status_code, r.json()["name"]) == (201, "\U0001f600" * 100)
    r = api.post("/projects", headers=admin, json={"name": "  Alpha  ", "members": []})
    assert (r.status_code, r.json()["name"], stored(engine, r.json()["id"]).name) == (201, "Alpha", "Alpha")


@pytest.mark.ac("AC-12")
def test_a_name_that_is_not_text_is_refused_with_422(api, admin, engine):
    refused(api.post("/projects", headers=admin, json={"name": 12, "members": []}), "invalid_request")
    refused(api.post("/projects", headers=admin, json={"members": []}), "invalid_request")
    assert project_count(engine) == 0


@pytest.mark.ac("AC-91")
@pytest.mark.parametrize("bad", ["Al\npha", "Al\tpha", "Al\u202epha", "Al\u2066pha"])
def test_a_name_with_a_control_or_override_character_is_refused_and_not_echoed(api, admin, engine, bad):
    r = api.post("/projects", headers=admin, json={"name": bad, "members": []})
    refused(r, "invalid_project_name")
    assert "pha" not in r.text and "Al" not in r.text
    assert project_count(engine) == 0


@pytest.mark.ac("AC-92")
def test_51_first_members_are_refused_and_50_are_accepted(api, admin, engine):
    ids = [active_user(api, admin, f"sub-{i}", f"u{i}@x.test")[1] for i in range(51)]
    refused(api.post("/projects", headers=admin, json={"name": "Alpha", "members": ids}), "invalid_request")
    assert project_count(engine) == 0
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": ids[:50]})
    assert (r.status_code, len(r.json()["members"])) == (201, 50)


@pytest.mark.ac("AC-93")
@pytest.mark.parametrize(
    "field,value",
    [("id", "p-1"), ("created_by", "acc-x"), ("added_by", "acc-x"), ("created_at", "2020-01-01"), ("files", ["f"])],
)
def test_an_unknown_field_is_refused_not_ignored_and_not_echoed(api, admin, engine, field, value):
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [], field: value})
    refused(r, "invalid_request")
    assert str(value) not in r.text and "Alpha" not in r.text
    assert project_count(engine) == 0


@pytest.mark.ac("AC-93")
def test_the_known_fields_still_work(api, admin):
    assert api.post("/projects", headers=admin, json={"name": "Alpha", "members": []}).status_code == 201
    assert api.post("/projects", headers=admin, json={"name": "Beta"}).status_code == 201


@pytest.mark.ac("AC-11")
def test_the_role_is_checked_before_unknown_fields_and_before_a_bad_name(api, admin, engine):
    maya_h, _ = active_user(api, admin, "sub-maya", "maya@x.test")
    r = api.post("/projects", headers=maya_h, json={"name": "", "members": [], "id": "p-1"})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert project_count(engine) == 0


def ineligible(r):
    assert r.status_code == 422
    assert r.json() == {"detail": {"code": "member_not_eligible", "message": "A first member cannot be added."}}


@pytest.mark.ac("AC-13")
def test_a_pending_a_deactivated_and_an_unknown_account_get_the_identical_refusal_and_nothing_is_written(
    api, admin, engine
):
    _, pending_id = register(api, "sub-pen", "pen@x.test")
    _, gone_id = active_user(api, admin, "sub-gone", "gone@x.test")
    assert api.post(f"/accounts/{gone_id}/deactivate", headers=admin, json={"reason": "left"}).status_code == 200
    answers = []
    for member in (pending_id, gone_id, str(uuid.uuid4())):
        r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [member]})
        ineligible(r)
        assert member not in r.text
        answers.append((r.status_code, r.json()))
    assert answers[0] == answers[1] == answers[2]
    assert project_count(engine) == 0


@pytest.mark.ac("AC-13")
def test_one_active_and_one_inactive_member_refuses_all_and_writes_nothing(api, admin, engine):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    _, pending_id = register(api, "sub-pen", "pen@x.test")
    ineligible(api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id, pending_id]}))
    assert project_count(engine) == 0
    with Session(engine) as s:
        assert s.execute(text("SELECT count(*) FROM memberships")).scalar_one() == 0


@pytest.mark.ac("AC-89")
def test_naming_the_same_active_person_twice_makes_one_membership(api, admin, engine):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    r = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id, maya_id]})
    assert (r.status_code, r.json()["members"]) == (201, [{"id": maya_id, "name": "maya"}])
    with Session(engine) as s:
        assert s.execute(text("SELECT count(*) FROM memberships")).scalar_one() == 1
