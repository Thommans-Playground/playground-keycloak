"""Creating a project through the whole HTTP path: its audit entry (AC-29, AC-85, AC-89) and its log lines (AC-48)."""

import json
import os
from io import StringIO

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.access.adapters.outbound.token_verifier import JwtTokenVerifier
from app.infrastructure.config import Settings
from app.infrastructure.security_log import JsonStdoutSecurityLog
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


def project_entries(api, admin):
    return [e for e in api.get("/audit", headers=admin).json() if e["kind"] == "project"]


@pytest.mark.ac("AC-29")
def test_a_created_project_writes_one_entry_with_the_actor_the_project_and_the_first_members(api, admin):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    _, bob_id = active_user(api, admin, "sub-bob", "bob@x.test")
    ada_id = me_id(api, admin)

    project = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id, bob_id]}).json()

    (e,) = project_entries(api, admin)
    assert (e["kind"], e["action"], e["reason"]) == ("project", "create_project", None)
    assert (e["actor_id"], e["actor_name"], e["actor_email"]) == (ada_id, "Ada", "ada@x.test")
    assert (e["target_id"], e["target_name"], e["target_email"]) == (project["id"], "Alpha", None)
    assert e["details"] == [
        {"id": maya_id, "name": "maya", "email": "maya@x.test"},
        {"id": bob_id, "name": "bob", "email": "bob@x.test"},
    ]


@pytest.mark.ac("AC-29")
def test_a_rename_afterwards_does_not_change_the_entry(api, admin):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]})
    renamed = auth("sub-maya", "maya@x.test", name="Maya Lopez")
    assert api.get("/me", headers=renamed).json()["name"] == "Maya Lopez"
    assert api.get("/me", headers=auth("sub-ada", "ada@x.test", name="Ada Byron")).json()["name"] == "Ada Byron"

    (e,) = project_entries(api, admin)
    assert (e["actor_name"], e["details"][0]["name"]) == ("Ada", "maya")


@pytest.mark.ac("AC-29")
def test_a_project_with_no_first_member_still_writes_one_entry(api, admin):
    api.post("/projects", headers=admin, json={"name": "Alpha", "members": []})
    (e,) = project_entries(api, admin)
    assert e["details"] == []


@pytest.mark.ac("AC-29")
def test_a_refused_creation_writes_no_entry(api, admin, engine):
    _, maya_id = register(api, "sub-maya", "maya@x.test")  # pending: not eligible
    user_h, _ = active_user(api, admin, "sub-bob", "bob@x.test")
    before = api.get("/audit", headers=admin).json()
    bad = [
        (user_h, {"name": "Alpha", "members": []}),
        (admin, {"name": "", "members": []}),
        (admin, {"name": "Alpha", "members": [], "id": "x"}),
        (admin, {"name": "Alpha", "members": [maya_id]}),
    ]
    for headers, body in bad:
        assert api.post("/projects", headers=headers, json=body).status_code in (403, 422)
    assert api.get("/audit", headers=admin).json() == before
    with Session(engine) as s:
        assert s.execute(text("SELECT count(*) FROM projects")).scalar_one() == 0


@pytest.mark.ac("AC-89")
def test_naming_a_person_twice_names_them_once_in_the_entry(api, admin):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id, maya_id]})
    (e,) = project_entries(api, admin)
    assert [d["id"] for d in e["details"]] == [maya_id]


@pytest.mark.ac("AC-85")
def test_an_administrator_sees_each_project_creation_in_the_trail_newest_first(api, admin):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    first = api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]}).json()
    second = api.post("/projects", headers=admin, json={"name": "Beta", "members": []}).json()

    entries = api.get("/audit", headers=admin).json()
    assert [(e["kind"], e["target_name"]) for e in entries[:2]] == [("project", "Beta"), ("project", "Alpha")]
    assert (entries[0]["target_id"], entries[1]["target_id"]) == (second["id"], first["id"])
    assert entries[1]["details"][0]["name"] == "maya"
    assert entries[2]["kind"] == "account"  # the account entries are still there, below


# AC-48: every refusal Projects answers writes one line; a success writes none; a guard's refusal is not doubled


def refusal_lines(log, since):
    return log.events[since:]


@pytest.mark.ac("AC-48")
@pytest.mark.parametrize(
    "who,body,status,code",
    [
        ("user", {"name": "Alpha", "members": []}, 403, "forbidden"),
        ("admin", {"name": "  ", "members": []}, 422, "invalid_project_name"),
        ("admin", {"name": "Alpha", "members": [], "id": "x"}, 422, "invalid_request"),
        ("admin", {"name": "Alpha", "members": ["no-such-account"]}, 422, "member_not_eligible"),
        ("admin", ["not", "an", "object"], 422, "invalid_request"),
    ],
)
def test_each_projects_refusal_writes_exactly_one_line_with_its_code_and_who(api, admin, log, who, body, status, code):
    user_h, user_id = active_user(api, admin, "sub-bob", "bob@x.test")
    headers, account_id = (user_h, user_id) if who == "user" else (admin, me_id(api, admin))
    since = len(log.events)

    r = api.post("/projects", headers=headers, json=body)

    assert r.status_code == status
    (line,) = refusal_lines(log, since)
    assert (line["event"], line["result"], line["reason"], line["person_id"]) == (
        "request_refused",
        "refused",
        code,
        account_id,
    )


@pytest.mark.ac("AC-48")
def test_a_created_project_writes_no_line(api, admin, log):
    _, maya_id = active_user(api, admin, "sub-maya", "maya@x.test")
    since = len(log.events)
    assert api.post("/projects", headers=admin, json={"name": "Alpha", "members": [maya_id]}).status_code == 201
    assert refusal_lines(log, since) == []


@pytest.mark.ac("AC-48")
def test_a_guards_refusal_is_logged_once_by_the_guard_and_not_again_by_projects(api, admin, log):
    pending, pending_id = register(api, "sub-new", "new@x.test")
    gone, gone_id = active_user(api, admin, "sub-gone", "gone@x.test")
    api.post(f"/accounts/{gone_id}/deactivate", headers=admin, json={"reason": "Left"})
    body = {"name": "Alpha", "members": []}
    for headers, code in [
        ({}, "missing_token"),
        ({"Authorization": "Bearer nope"}, "invalid_token"),
        (pending, "account_pending"),
        (gone, "account_deactivated"),
    ]:
        since = len(log.events)
        assert api.post("/projects", headers=headers, json=body).status_code in (401, 403)
        assert [e["reason"] for e in refusal_lines(log, since)] == [code]


@pytest.mark.ac("AC-48")
def test_the_json_line_holds_no_project_name_and_no_account_id_but_the_callers(engine):
    stream = StringIO()
    settings = Settings(keycloak_url="http://kc.test", bootstrap_admin_emails="ada@x.test")
    verifier = JwtTokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key())
    api = TestClient(create_app(settings, verifier, FakeIdp(), engine, JsonStdoutSecurityLog(stream)))
    admin = auth("sub-ada", "ada@x.test", name="Ada")
    ada_id = me_id(api, admin)
    stream.truncate(0)
    stream.seek(0)

    r = api.post("/projects", headers=admin, json={"name": "Secret Alpha", "members": ["acc-someone-else"]})

    assert r.status_code == 422
    (raw,) = stream.getvalue().splitlines()
    line = json.loads(raw)
    assert (line["event"], line["result"], line["reason"], line["person_id"]) == (
        "request_refused",
        "refused",
        "member_not_eligible",
        ada_id,
    )
    assert "Secret" not in raw and "acc-someone-else" not in raw
