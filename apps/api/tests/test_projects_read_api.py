"""GET /projects and GET /projects/{project_id} through the HTTP client: UC-P3 (AC-55, AC-26, AC-27, AC-28, AC-86,
AC-48), and the wiring."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.access.adapters.outbound.token_verifier import JwtTokenVerifier
from app.infrastructure.config import Settings
from app.main import create_app
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
def log():
    return FakeSecurityLog()


@pytest.fixture
def api(engine, log):
    settings = Settings(keycloak_url="http://kc.test", bootstrap_admin_emails="ada@x.test")
    verifier = JwtTokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key())
    return TestClient(create_app(settings, verifier, FakeIdp(), engine, log))


@pytest.fixture
def admin(api):
    h = auth("sub-ada", "ada@x.test", name="Ada")
    assert api.get("/me", headers=h).json()["role"] == "administrator"
    return h


def active_user(api, admin, sub, email):
    headers, account_id = register(api, sub, email)
    assert api.post(f"/accounts/{account_id}/approve", headers=admin).status_code == 200
    return headers, account_id


def make_project(api, admin, name, members):
    r = api.post("/projects", headers=admin, json={"name": name, "members": members})
    assert r.status_code == 201
    return r.json()


@pytest.fixture
def world(api, admin):
    """Maya is in Alpha and Beta, Bob in Beta, Eve in none. Gamma has no member."""
    maya_h, maya = active_user(api, admin, "sub-maya", "maya@x.test")
    bob_h, bob = active_user(api, admin, "sub-bob", "bob@x.test")
    eve_h, eve = active_user(api, admin, "sub-eve", "eve@x.test")
    alpha = make_project(api, admin, "Alpha", [maya])
    beta = make_project(api, admin, "Beta", [maya, bob])
    gamma = make_project(api, admin, "Gamma", [])
    return {"maya": maya_h, "bob": bob_h, "eve": eve_h, "ids": (maya, bob, eve), "projects": (alpha, beta, gamma)}


@pytest.mark.ac("AC-55")
def test_a_user_lists_only_their_projects_and_an_administrator_lists_all(api, admin, world):
    alpha, beta, gamma = world["projects"]
    r = api.get("/projects", headers=world["bob"])
    assert r.status_code == 200
    assert [p["id"] for p in r.json()] == [beta["id"]]
    assert {p["id"] for p in api.get("/projects", headers=world["maya"]).json()} == {alpha["id"], beta["id"]}
    r = api.get("/projects", headers=admin)  # the administrator is a member of none
    assert {p["id"] for p in r.json()} == {alpha["id"], beta["id"], gamma["id"]}


@pytest.mark.ac("AC-55")
def test_a_listed_project_has_the_shape_of_the_open_answer(api, admin, world):
    alpha = world["projects"][0]
    listed = api.get("/projects", headers=world["maya"]).json()
    assert alpha in listed
    assert all(set(p) == {"id", "name", "created_by", "members", *PLACEHOLDERS} for p in listed)


@pytest.mark.ac("AC-86")
def test_a_user_in_no_project_gets_200_and_an_empty_list(api, world):
    r = api.get("/projects", headers=world["eve"])
    assert (r.status_code, r.json()) == (200, [])


@pytest.mark.ac("AC-86")
def test_nobody_has_a_project_yet_an_administrator_gets_an_empty_list(api, admin):
    r = api.get("/projects", headers=admin)
    assert (r.status_code, r.json()) == (200, [])


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-26")
@pytest.mark.ac("AC-28")
def test_a_member_and_an_administrator_open_a_project_and_see_its_members(api, admin, world):
    _, beta, _ = world["projects"]
    maya, bob, _ = world["ids"]
    for headers in (world["maya"], world["bob"], admin):
        r = api.get(f"/projects/{beta['id']}", headers=headers)
        assert r.status_code == 200
        body = r.json()
        assert (body["id"], body["name"], body["created_by"]) == (beta["id"], "Beta", me_id(api, admin))
        assert sorted(body["members"], key=lambda m: m["id"]) == sorted(
            [{"id": maya, "name": "maya"}, {"id": bob, "name": "bob"}], key=lambda m: m["id"]
        )
        assert {k: body[k] for k in PLACEHOLDERS} == PLACEHOLDERS
        assert set(body) == {"id", "name", "created_by", "members", *PLACEHOLDERS}


@pytest.mark.ac("AC-28")
def test_an_administrator_opens_a_project_with_no_member(api, admin, world):
    gamma = world["projects"][2]
    r = api.get(f"/projects/{gamma['id']}", headers=admin)
    assert (r.status_code, r.json()["members"]) == (200, [])


def hidden_answer(r):
    return r.status_code, r.json(), r.headers.get("content-type")


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-26")
@pytest.mark.ac("AC-27")
def test_a_person_who_may_not_see_a_project_gets_the_answer_for_a_missing_one(api, world):
    alpha, beta, gamma = world["projects"]
    r = api.get(f"/projects/{alpha['id']}", headers=world["bob"])  # Bob is in Beta only
    assert r.status_code == 404
    assert r.json() == {"detail": {"code": "project_not_found", "message": "Project not found."}}
    assert alpha["name"] not in r.text and alpha["id"] not in r.text


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-27")
def test_hidden_missing_and_malformed_ids_get_identical_status_body_and_code(api, world):
    alpha, _, gamma = world["projects"]
    ids = [alpha["id"], gamma["id"], str(uuid.uuid4()), "not-a-uuid", "1", "a" * 300, "%00", "%20", "%E2%80%AE"]
    answers = [hidden_answer(api.get(f"/projects/{i}", headers=world["eve"])) for i in ids]
    assert answers[0][0] == 404
    assert all(a == answers[0] for a in answers), answers


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-27")
def test_the_same_holds_for_a_member_of_other_projects(api, world):
    alpha, beta, _ = world["projects"]
    hidden = hidden_answer(api.get(f"/projects/{beta['id']}", headers=world["eve"]))
    missing = hidden_answer(api.get(f"/projects/{uuid.uuid4()}", headers=world["eve"]))
    bad = hidden_answer(api.get("/projects/xyz", headers=world["eve"]))
    assert hidden == missing == bad


@pytest.mark.ac("AC-48")
def test_every_refusal_writes_one_line_with_a_reason_that_does_not_tell_hidden_from_missing(api, world, log):
    alpha, _, _ = world["projects"]
    eve_id = world["ids"][2]
    for pid in (alpha["id"], str(uuid.uuid4()), "not-a-uuid"):
        log.events.clear()
        assert api.get(f"/projects/{pid}", headers=world["eve"]).status_code == 404
        assert log.events == [
            {
                "event": "request_refused",
                "result": "refused",
                "person_id": eve_id,
                "session_id": None,
                "reason": "project_not_found",
            }
        ]


@pytest.mark.ac("AC-48")
def test_a_successful_read_writes_no_log_line_and_no_audit_entry(api, admin, world, log, engine):
    alpha = world["projects"][0]
    with Session(engine) as s:
        before = s.execute(text("SELECT count(*) FROM audit_entries")).scalar_one()
    log.events.clear()
    assert api.get("/projects", headers=world["maya"]).status_code == 200
    assert api.get(f"/projects/{alpha['id']}", headers=world["maya"]).status_code == 200
    assert api.get(f"/projects/{alpha['id']}", headers=admin).status_code == 200
    assert log.events == []
    with Session(engine) as s:
        assert s.execute(text("SELECT count(*) FROM audit_entries")).scalar_one() == before


@pytest.mark.ac("AC-94")
def test_the_read_routes_are_behind_the_guard_chain_before_the_project_is_looked_at(api, admin, world):
    alpha = world["projects"][0]
    pending, _ = register(api, "sub-new", "new@x.test")
    for path in ("/projects", f"/projects/{alpha['id']}"):
        assert api.get(path).status_code == 401
        r = api.get(path, headers=pending)
        assert (r.status_code, r.json()["detail"]["code"]) == (403, "account_pending")
        assert alpha["name"] not in r.text


def test_the_read_routes_are_served_by_the_projects_context(api):
    got = {(r.path, tuple(sorted(r.methods))) for r in _api_routes(api.app) if r.path.startswith("/projects")}
    assert ("/projects", ("GET",)) in got and ("/projects/{project_id}", ("GET",)) in got
    modules = {r.endpoint.__module__ for r in _api_routes(api.app) if r.path.startswith("/projects")}
    assert modules == {"app.projects.adapters.inbound.http"}


# ADR 0016: every project answer shows its members as {id, name}


def member_pairs(project):
    return {m["id"]: m["name"] for m in project["members"]}


@pytest.mark.ac("AC-55")
@pytest.mark.ac("AC-28")
def test_the_list_shows_the_names_of_the_members_of_every_project(api, admin, world):
    maya, bob, _ = world["ids"]
    listed = {p["name"]: p for p in api.get("/projects", headers=admin).json()}
    assert member_pairs(listed["Alpha"]) == {maya: "maya"}
    assert member_pairs(listed["Beta"]) == {maya: "maya", bob: "bob"}
    assert listed["Gamma"]["members"] == []
    mine = {p["name"]: p for p in api.get("/projects", headers=world["maya"]).json()}
    assert member_pairs(mine["Beta"]) == {maya: "maya", bob: "bob"}


@pytest.mark.ac("AC-26")
def test_a_person_who_changed_their_name_shows_with_the_new_name_at_the_next_read(api, admin, world):
    maya, _, _ = world["ids"]
    renamed = auth("sub-maya", "maya@x.test", name="Maya Lopez")
    assert api.get("/me", headers=renamed).json()["name"] == "Maya Lopez"
    alpha = world["projects"][0]
    assert member_pairs(api.get(f"/projects/{alpha['id']}", headers=admin).json()) == {maya: "Maya Lopez"}


@pytest.mark.ac("AC-28")
def test_a_deactivated_member_keeps_showing_with_the_name(api, admin, world):
    maya, _, _ = world["ids"]
    assert api.post(f"/accounts/{maya}/deactivate", headers=admin, json={"reason": "Left"}).status_code == 200
    alpha = world["projects"][0]
    assert member_pairs(api.get(f"/projects/{alpha['id']}", headers=admin).json()) == {maya: "maya"}


@pytest.mark.ac("AC-28")
def test_a_member_id_that_access_does_not_know_keeps_its_id_and_has_a_null_name(api, admin, world, engine):
    alpha = world["projects"][0]
    ghost = str(uuid.uuid4())
    with Session(engine) as s:
        s.execute(
            text("INSERT INTO memberships (project_id, account_id, added_by) VALUES (:p, :a, :b)"),
            {"p": alpha["id"], "a": ghost, "b": me_id(api, admin)},
        )
        s.commit()
    maya, _, _ = world["ids"]
    opened = api.get(f"/projects/{alpha['id']}", headers=admin).json()
    assert member_pairs(opened) == {maya: "maya", ghost: None}
    listed = {p["name"]: p for p in api.get("/projects", headers=admin).json()}
    assert member_pairs(listed["Alpha"]) == {maya: "maya", ghost: None}
