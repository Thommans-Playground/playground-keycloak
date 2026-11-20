"""GET /audit through the HTTP client: UC-L1 acceptance level (AC-56, AC-68, AC-69), and the composition that wires it."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.access.adapters.outbound.sql import AccountRow
from app.access.adapters.outbound.token_verifier import JwtTokenVerifier
from app.infrastructure.config import Settings
from app.main import create_app
from tests.conftest import AUDIENCE, ISSUER, KEY, auth, make_engine, make_token, me_id, register
from tests.fakes import FakeIdp
from tests.test_api import _api_routes

ENTRY_FIELDS = {
    "id", "at", "kind", "actor_id", "actor_name", "actor_email", "action",
    "target_id", "target_name", "target_email", "details", "reason",
}


@pytest.mark.ac("AC-56")
def test_an_account_change_shows_with_who_what_whom_and_the_reason(client, admin):
    _, maya_id = register(client, "sub-maya", "maya@x.test")
    client.post(f"/accounts/{maya_id}/approve", headers=admin)
    client.post(f"/accounts/{maya_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    ada_id = me_id(client, admin)

    r = client.get("/audit", headers=admin)
    assert r.status_code == 200
    entries = r.json()
    assert all(set(e) == ENTRY_FIELDS for e in entries)
    deactivate, approve, register_entry = entries[0], entries[1], entries[2]

    assert (deactivate["kind"], deactivate["action"], deactivate["reason"]) == ("account", "deactivate", "Left the team")
    assert (deactivate["actor_id"], deactivate["actor_name"], deactivate["actor_email"]) == (ada_id, "Ada", "ada@x.test")
    assert (deactivate["target_id"], deactivate["target_name"], deactivate["target_email"]) == (maya_id, "maya", "maya@x.test")
    assert deactivate["details"] == [] and deactivate["at"]
    assert (approve["action"], approve["reason"]) == ("approve", None)
    # a person's first request: no actor, the new account as target
    assert (register_entry["action"], register_entry["actor_id"], register_entry["actor_name"]) == ("register", None, None)
    assert (register_entry["target_id"], register_entry["target_name"]) == (maya_id, "maya")


@pytest.mark.ac("AC-56")
def test_the_bootstrap_administrator_entry_names_the_new_account(client, admin):
    ada_id = me_id(client, admin)
    last = client.get("/audit", headers=admin).json()[-1]
    assert (last["action"], last["actor_id"], last["target_id"], last["target_name"]) == ("create_bootstrap_admin", None, ada_id, "Ada")


@pytest.mark.ac("AC-68")
def test_each_person_who_is_not_an_active_administrator_is_refused_and_sees_no_entry(client, admin):
    _, user_id = register(client, "sub-user", "user@x.test")
    client.post(f"/accounts/{user_id}/approve", headers=admin)
    _, gone_id = register(client, "sub-gone", "gone@x.test")
    client.post(f"/accounts/{gone_id}/approve", headers=admin)
    client.post(f"/accounts/{gone_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    register(client, "sub-new", "new@x.test")

    cases = {
        "ordinary user": ("sub-user", "user@x.test", "forbidden"),
        "pending account": ("sub-new", "new@x.test", "account_pending"),
        "deactivated account": ("sub-gone", "gone@x.test", "account_deactivated"),
    }
    for who, (sub, email, code) in cases.items():
        r = client.get("/audit", headers=auth(sub, email))
        assert (r.status_code, r.json()["detail"]["code"]) == (403, code), who
        assert "action" not in r.text and not isinstance(r.json(), list), who


@pytest.mark.ac("AC-68")
def test_no_token_and_a_bad_token_are_401(client):
    r = client.get("/audit")
    assert (r.status_code, r.json()["detail"]["code"]) == (401, "missing_token")
    r = client.get("/audit", headers={"Authorization": f"Bearer {make_token('s', 'a@x.test', expires_in=-10)}"})
    assert (r.status_code, r.json()["detail"]["code"]) == (401, "invalid_token")


@pytest.mark.ac("AC-68")
def test_the_refusal_of_an_ordinary_user_has_the_body_the_web_reads(client, admin):
    _, user_id = register(client, "sub-user", "user@x.test")
    client.post(f"/accounts/{user_id}/approve", headers=admin)
    r = client.get("/audit", headers=auth("sub-user", "user@x.test"))
    assert r.status_code == 403
    assert r.json() == {"detail": {"code": "forbidden", "message": "Administrators only."}}


@pytest.mark.ac("AC-69")
def test_an_empty_trail_is_200_and_an_empty_list():
    engine = make_engine()
    with Session(engine) as s:  # an administrator who already exists, with no change recorded yet
        s.add(AccountRow(id="acc-ada", identity="sub-ada", name="Ada", email="ada@x.test", role="administrator",
                         status="active", created=__import__("datetime").datetime(2026, 1, 1), created_by=None))
        s.commit()
    verifier = JwtTokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key())
    app = create_app(Settings(keycloak_url="http://kc.test"), verifier, FakeIdp(), engine)
    r = TestClient(app).get("/audit", headers=auth("sub-ada", "ada@x.test", name="Ada"))
    assert (r.status_code, r.json()) == (200, [])


def test_the_audit_route_is_served_by_the_audit_context_and_not_by_access():
    app = create_app(Settings(keycloak_url="http://kc.test"), JwtTokenVerifier(ISSUER, AUDIENCE, lambda _t: KEY.public_key()),
                     FakeIdp(), make_engine())
    modules = {r.endpoint.__module__ for r in _api_routes(app) if r.path == "/audit"}
    assert modules == {"app.audit.adapters.inbound.http"}


@pytest.mark.ac("AC-56")
def test_a_change_and_its_entry_use_the_same_session_so_a_rolled_back_request_leaves_no_entry(client, admin, idp):
    """Reinstating while Keycloak is down fails after nothing was written: the trail has no entry for it."""
    _, maya_id = register(client, "sub-maya", "maya@x.test")
    client.post(f"/accounts/{maya_id}/approve", headers=admin)
    client.post(f"/accounts/{maya_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    before = client.get("/audit", headers=admin).json()
    idp.fail = True
    assert client.post(f"/accounts/{maya_id}/reinstate", headers=admin, json={"reason": "Back"}).status_code == 502
    assert client.get("/audit", headers=admin).json() == before
