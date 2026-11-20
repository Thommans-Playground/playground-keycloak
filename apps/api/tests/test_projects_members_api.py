"""POST /projects/{id}/members and DELETE /projects/{id}/members/{account_id} through the whole HTTP path: UC-P2
(AC-17, AC-18, AC-20, AC-84, AC-30, AC-32, AC-60, AC-48, AC-87, AC-88, AC-93), RULE-P4."""

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


@pytest.fixture
def world(api, admin):
    """Maya is a member of Alpha. Bob and Eve are active and in no project. Pat is pending. Alpha is Ada's."""
    maya_h, maya = active_user(api, admin, "sub-maya", "maya@x.test")
    bob_h, bob = active_user(api, admin, "sub-bob", "bob@x.test")
    eve_h, eve = active_user(api, admin, "sub-eve", "eve@x.test")
    pat_h, pat = register(api, "sub-pat", "pat@x.test")
    alpha = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya]}).json()
    return {
        "maya": (maya_h, maya),
        "bob": (bob_h, bob),
        "eve": (eve_h, eve),
        "pat": (pat_h, pat),
        "alpha": alpha,
    }


def members(api, admin, project_id):
    return sorted(m["id"] for m in api.get(f"/projects/{project_id}", headers=admin).json()["members"])


def add(api, headers, project_id, account_id):
    return api.post(f"/projects/{project_id}/members", headers=headers, json={"account_id": account_id})


def remove(api, headers, project_id, account_id):
    return api.delete(f"/projects/{project_id}/members/{account_id}", headers=headers)


def counts(engine):
    with Session(engine) as s:
        return (
            s.execute(text("SELECT count(*) FROM memberships")).scalar_one(),
            s.execute(text("SELECT count(*) FROM audit_entries WHERE kind = 'project'")).scalar_one(),
        )


@pytest.mark.ac("AC-17")
def test_an_administrator_adds_an_active_person_and_the_answer_is_the_project(api, admin, world):
    alpha, (_, maya), (_, bob) = world["alpha"], world["maya"], world["bob"]
    r = add(api, admin, alpha["id"], bob)
    assert r.status_code == 200
    assert (r.json()["id"], sorted(m["id"] for m in r.json()["members"])) == (alpha["id"], sorted([maya, bob]))
    assert {m["id"]: m["name"] for m in r.json()["members"]} == {maya: "maya", bob: "bob"}  # ADR 0016
    assert r.json() == api.get(f"/projects/{alpha['id']}", headers=admin).json()
    assert api.get(f"/projects/{alpha['id']}", headers=world["bob"][0]).status_code == 200  # in at their next request


@pytest.mark.ac("AC-18")
@pytest.mark.parametrize("who", ["pending", "deactivated", "unknown"])
def test_a_pending_deactivated_or_unknown_person_is_refused_with_one_answer(api, admin, world, engine, who):
    alpha = world["alpha"]
    gone_h, gone = active_user(api, admin, "sub-gone", "gone@x.test")
    assert api.post(f"/accounts/{gone}/deactivate", headers=admin, json={"reason": "Left"}).status_code == 200
    target = {"pending": world["pat"][1], "deactivated": gone, "unknown": str(uuid.uuid4())}[who]
    before = counts(engine)
    r = add(api, admin, alpha["id"], target)
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "member_not_eligible")
    assert target not in r.text and "pending" not in r.text and "deactivated" not in r.text
    assert counts(engine) == before


@pytest.mark.ac("AC-18")
def test_the_three_refusals_have_the_same_body(api, admin, world):
    gone_h, gone = active_user(api, admin, "sub-gone", "gone@x.test")
    api.post(f"/accounts/{gone}/deactivate", headers=admin, json={"reason": "Left"})
    bodies = {add(api, admin, world["alpha"]["id"], t).text for t in (world["pat"][1], gone, str(uuid.uuid4()))}
    assert len(bodies) == 1


@pytest.mark.ac("AC-20")
def test_an_administrator_removes_a_member_who_then_gets_the_missing_project_answer(api, admin, world):
    alpha, (maya_h, maya) = world["alpha"], world["maya"]
    assert api.get(f"/projects/{alpha['id']}", headers=maya_h).status_code == 200
    r = remove(api, admin, alpha["id"], maya)
    assert (r.status_code, r.json()["members"]) == (200, [])
    gone = api.get(f"/projects/{alpha['id']}", headers=maya_h)
    missing = api.get(f"/projects/{uuid.uuid4()}", headers=maya_h)
    assert (gone.status_code, gone.json()) == (missing.status_code, missing.json()) == (404, gone.json())


@pytest.mark.ac("AC-20")
def test_an_administrator_may_remove_a_deactivated_member(api, admin, world):
    alpha, (_, bob) = world["alpha"], world["bob"]
    assert add(api, admin, alpha["id"], bob).status_code == 200
    assert api.post(f"/accounts/{bob}/deactivate", headers=admin, json={"reason": "Left"}).status_code == 200
    assert remove(api, admin, alpha["id"], bob).status_code == 200
    assert bob not in members(api, admin, alpha["id"])


@pytest.mark.ac("AC-88")
def test_adding_an_existing_member_changes_nothing_writes_no_entry_and_answers_success(api, admin, world, engine, log):
    alpha, (_, maya) = world["alpha"], world["maya"]
    before, lines = counts(engine), len(log.events)
    r = add(api, admin, alpha["id"], maya)
    assert (r.status_code, r.json()["members"]) == (200, [{"id": maya, "name": "maya"}])
    assert counts(engine) == before
    assert log.events[lines:] == []


@pytest.mark.ac("AC-87")
def test_removing_a_person_who_is_not_a_member_is_refused_and_writes_nothing(api, admin, world, engine, log):
    alpha, (_, bob) = world["alpha"], world["bob"]
    before, lines = counts(engine), len(log.events)
    r = remove(api, admin, alpha["id"], bob)
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "member_not_eligible")
    assert counts(engine) == before
    assert [e["reason"] for e in log.events[lines:]] == ["member_not_eligible"]


@pytest.mark.ac("AC-87")
def test_removing_an_account_that_does_not_exist_gets_the_same_refusal(api, admin, world):
    r = remove(api, admin, world["alpha"]["id"], str(uuid.uuid4()))
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "member_not_eligible")


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-84")
@pytest.mark.parametrize("change", ["add", "remove"])
def test_a_stranger_gets_one_404_for_a_hidden_a_missing_and_a_malformed_project(api, admin, world, engine, change):
    eve_h, _ = world["eve"]
    _, maya = world["maya"]
    _, bob = world["bob"]
    answers = []
    for pid in (world["alpha"]["id"], str(uuid.uuid4()), "not-a-uuid"):
        before = counts(engine)
        r = add(api, eve_h, pid, bob) if change == "add" else remove(api, eve_h, pid, maya)
        answers.append((r.status_code, r.text, r.json()["detail"]["code"]))
        assert counts(engine) == before
    assert len(set(answers)) == 1 and answers[0][0] == 404 and answers[0][2] == "project_not_found"
    assert world["alpha"]["id"] not in answers[0][1] and "Alpha" not in answers[0][1]


@pytest.mark.rule("RULE-P4")
@pytest.mark.ac("AC-84")
def test_a_stranger_is_told_not_found_even_with_a_bad_body(api, admin, world):
    """The project is looked at before the input is: a body with an unknown field changes nothing about the answer."""
    eve_h, _ = world["eve"]
    r = api.post(f"/projects/{world['alpha']['id']}/members", headers=eve_h, json={"account_id": "x", "id": "y"})
    assert (r.status_code, r.json()["detail"]["code"]) == (404, "project_not_found")


@pytest.mark.ac("AC-60")
@pytest.mark.ac("AC-32")
def test_a_member_who_is_not_an_administrator_is_refused_403_and_nothing_changes(api, admin, world, engine):
    alpha, (maya_h, maya), (_, bob) = world["alpha"], world["maya"], world["bob"]
    before = counts(engine)
    for r in (add(api, maya_h, alpha["id"], bob), remove(api, maya_h, alpha["id"], maya)):
        assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert counts(engine) == before and members(api, admin, alpha["id"]) == [maya]


@pytest.mark.ac("AC-32")
def test_a_demoted_administrator_is_refused_at_once(api, admin, world):
    bo_h, bo = active_user(api, admin, "sub-bo", "bo@x.test")
    alpha, (_, bob) = world["alpha"], world["bob"]
    assert api.post(f"/accounts/{bo}/promote", headers=admin, json={"reason": "Covers"}).status_code == 200
    assert add(api, bo_h, alpha["id"], bob).status_code == 200
    assert api.post(f"/accounts/{bo}/demote", headers=admin, json={"reason": "Back"}).status_code == 200
    assert add(api, bo_h, alpha["id"], world["eve"][1]).status_code == 404  # no longer an administrator, not a member


@pytest.mark.ac("AC-93")
@pytest.mark.parametrize(
    "body", [{"account_id": "x", "extra": 1}, {"account_id": "x", "added_by": "y"}, {"id": "x"}, {}, {"account_id": 7}]
)
def test_an_unknown_missing_or_mistyped_field_is_refused_422_and_nothing_changes(api, admin, world, engine, body):
    before = counts(engine)
    r = api.post(f"/projects/{world['alpha']['id']}/members", headers=admin, json=body)
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "invalid_request")
    assert "extra" not in r.text and "added_by" not in r.text
    assert counts(engine) == before


@pytest.mark.ac("AC-93")
def test_the_role_is_checked_before_the_body(api, admin, world):
    maya_h, _ = world["maya"]
    r = api.post(f"/projects/{world['alpha']['id']}/members", headers=maya_h, json={"nope": 1})
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")


@pytest.mark.ac("AC-30")
def test_an_addition_writes_one_entry_with_who_what_which_project_and_which_member(api, admin, world):
    alpha, (_, bob) = world["alpha"], world["bob"]
    add(api, admin, alpha["id"], bob)
    entries = [e for e in api.get("/audit", headers=admin).json() if e["action"] == "add_member"]
    (e,) = entries
    assert (e["kind"], e["reason"]) == ("project", None)
    assert (e["actor_id"], e["actor_name"], e["actor_email"]) == (me_id(api, admin), "Ada", "ada@x.test")
    assert (e["target_id"], e["target_name"], e["target_email"]) == (alpha["id"], "Alpha", None)
    assert e["details"] == [{"id": bob, "name": "bob", "email": "bob@x.test"}]


@pytest.mark.ac("AC-30")
def test_a_removal_writes_one_entry_and_a_rename_afterwards_does_not_change_it(api, admin, world):
    alpha, (_, maya) = world["alpha"], world["maya"]
    remove(api, admin, alpha["id"], maya)
    assert api.get("/me", headers=auth("sub-maya", "maya@x.test", name="Maya Lopez")).status_code == 200
    (e,) = [e for e in api.get("/audit", headers=admin).json() if e["action"] == "remove_member"]
    assert (e["target_id"], e["target_name"]) == (alpha["id"], "Alpha")
    assert e["details"] == [{"id": maya, "name": "maya", "email": "maya@x.test"}]


@pytest.mark.ac("AC-30")
def test_the_change_and_its_entry_commit_together_or_not_at_all(api, admin, world, engine, monkeypatch):
    from app.audit.adapters.outbound import sql as audit_sql

    def boom(self, entry):
        raise RuntimeError("audit store down")

    monkeypatch.setattr(audit_sql.SqlAuditEntries, "add", boom, raising=True)
    alpha, (_, bob) = world["alpha"], world["bob"]
    before = counts(engine)
    with pytest.raises(RuntimeError):
        add(api, admin, alpha["id"], bob)
    assert counts(engine) == before


@pytest.mark.ac("AC-48")
@pytest.mark.parametrize(
    "who,call,status,code",
    [
        ("maya", "add", 403, "forbidden"),
        ("maya", "remove", 403, "forbidden"),
        ("eve", "add", 404, "project_not_found"),
        ("eve", "remove", 404, "project_not_found"),
        ("admin", "add_pending", 422, "member_not_eligible"),
        ("admin", "remove_stranger", 422, "member_not_eligible"),
        ("admin", "bad_body", 422, "invalid_request"),
    ],
)
def test_each_refusal_writes_exactly_one_line_with_its_code_and_who(api, admin, world, log, who, call, status, code):
    alpha = world["alpha"]
    headers, who_id = (admin, me_id(api, admin)) if who == "admin" else world[who]
    since = len(log.events)
    r = {
        "add": lambda: add(api, headers, alpha["id"], world["bob"][1]),
        "remove": lambda: remove(api, headers, alpha["id"], world["maya"][1]),
        "add_pending": lambda: add(api, headers, alpha["id"], world["pat"][1]),
        "remove_stranger": lambda: remove(api, headers, alpha["id"], world["bob"][1]),
        "bad_body": lambda: api.post(f"/projects/{alpha['id']}/members", headers=headers, json={"x": 1}),
    }[call]()
    assert (r.status_code, r.json()["detail"]["code"]) == (status, code)
    (line,) = log.events[since:]
    assert (line["event"], line["result"], line["reason"], line["person_id"]) == (
        "request_refused",
        "refused",
        code,
        who_id,
    )
    assert alpha["id"] not in str(line)


@pytest.mark.ac("AC-48")
def test_a_successful_change_writes_no_refusal_line(api, admin, world, log):
    alpha = world["alpha"]
    since = len(log.events)
    assert add(api, admin, alpha["id"], world["bob"][1]).status_code == 200
    assert remove(api, admin, alpha["id"], world["bob"][1]).status_code == 200
    assert log.events[since:] == []


@pytest.mark.ac("AC-94")
def test_the_member_routes_are_behind_the_guard_chain_before_the_project_is_looked_at(api, admin, world):
    alpha, (_, bob) = world["alpha"], world["bob"]
    pat_h, _ = world["pat"]
    for method, path, body in (
        ("POST", f"/projects/{alpha['id']}/members", {"account_id": bob}),
        ("DELETE", f"/projects/{alpha['id']}/members/{bob}", None),
    ):
        assert api.request(method, path, json=body).status_code == 401
        r = api.request(method, path, headers=pat_h, json=body)
        assert (r.status_code, r.json()["detail"]["code"]) == (403, "account_pending")
        assert alpha["name"] not in r.text


def test_the_member_routes_are_served_by_the_projects_context(api):
    from tests.test_api import _api_routes

    got = {(r.path, tuple(sorted(r.methods))) for r in _api_routes(api.app) if r.path.startswith("/projects")}
    assert ("/projects/{project_id}/members", ("POST",)) in got
    assert ("/projects/{project_id}/members/{account_id}", ("DELETE",)) in got
