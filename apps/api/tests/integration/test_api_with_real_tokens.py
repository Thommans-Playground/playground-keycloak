"""The RUNNING API with real tokens from the running Keycloak, over HTTP."""

import httpx
import pytest

from tests.integration import helpers
from tests.integration.helpers import ADMIN_EMAIL, ADMIN_PASSWORD, LoginRefused, bearer, login

pytestmark = pytest.mark.integration


@pytest.fixture
def api():
    with httpx.Client(base_url=helpers.API_URL, timeout=helpers.TIMEOUT) as c:
        yield c


def code_of(r: httpx.Response) -> str:
    return r.json()["detail"]["code"]


@pytest.fixture
def admin_token():
    return login(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.mark.ac("AC-1")
@pytest.mark.ac("AC-3")
def test_a_new_person_gets_a_pending_account(api, throwaway_user):
    r = api.get("/me", headers=bearer(login(throwaway_user)))
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending"
    assert body["email"] == throwaway_user.email


def test_a_non_administrator_cannot_list_accounts(api, throwaway_user):
    r = api.get("/accounts", headers=bearer(login(throwaway_user)))
    assert r.status_code == 403


@pytest.mark.ac("AC-33")
@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer garbage"}, {"Authorization": "Bearer a.b.c"}])
def test_no_token_or_a_garbage_token_is_401(api, headers):
    r = api.get("/me", headers=headers)
    assert r.status_code == 401
    if headers:
        assert code_of(r) == "invalid_token"


def test_the_administrator_can_list_accounts(api, admin_token):
    r = api.get("/accounts", headers=bearer(admin_token))
    assert r.status_code == 200


@pytest.mark.ac("AC-63")
def test_an_ordinary_user_is_refused_all_five_commands(api, admin_token, throwaway_user):
    actor_token = login(throwaway_user)
    actor_id = api.get("/me", headers=bearer(actor_token)).json()["id"]
    target = helpers.create_user()
    try:
        target_id = api.get("/me", headers=bearer(login(target))).json()["id"]
        for stage in ("pending", "active user"):  # the actor is refused first as a pending person, then once approved
            if stage == "active user":
                assert api.post(f"/accounts/{actor_id}/approve", headers=bearer(admin_token), json={"reason": "integration test"}).status_code == 200
            for action in ("approve", "deactivate", "reinstate", "promote", "demote"):
                r = api.post(f"/accounts/{target_id}/{action}", headers=bearer(actor_token), json={"reason": "integration test"})
                assert r.status_code == 403, (stage, action)
        shown = next(a for a in api.get("/accounts", headers=bearer(admin_token)).json() if a["id"] == target_id)
        assert (shown["status"], shown["role"]) == ("pending", "user")
    finally:
        helpers.delete_user(target.id)


@pytest.mark.ac("AC-5")
def test_an_administrator_approves_and_the_person_gets_in(api, admin_token, throwaway_user):
    token = login(throwaway_user)
    account_id = api.get("/me", headers=bearer(token)).json()["id"]
    r = api.post(f"/accounts/{account_id}/approve", headers=bearer(admin_token), json={"reason": "integration test"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "active"
    assert api.get("/accounts", headers=bearer(token)).status_code == 403  # active, but not an administrator


@pytest.mark.ac("AC-6")
@pytest.mark.ac("AC-7")
def test_deactivate_then_reinstate_over_real_http_and_real_keycloak(api, admin_token, throwaway_user):
    token = login(throwaway_user)
    account_id = api.get("/me", headers=bearer(token)).json()["id"]
    admin = bearer(admin_token)
    r = api.post(f"/accounts/{account_id}/approve", headers=admin, json={"reason": "it"})
    assert r.status_code == 200, r.text

    # deactivate: the old, still valid token is refused, and Keycloak shows the user disabled
    r = api.post(f"/accounts/{account_id}/deactivate", headers=admin, json={"reason": "integration test"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "deactivated"
    again = api.get("/me", headers=bearer(token))
    assert again.status_code == 403 and code_of(again) == "account_deactivated"
    assert helpers.kc_user(throwaway_user.id).json()["enabled"] is False
    with pytest.raises(LoginRefused):
        login(throwaway_user)
    assert helpers.kc_sessions(throwaway_user.id) == []

    # reinstate: both sides come back
    r = api.post(f"/accounts/{account_id}/reinstate", headers=admin, json={"reason": "integration test"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "active"
    assert helpers.kc_user(throwaway_user.id).json()["enabled"] is True
    assert api.get("/me", headers=bearer(login(throwaway_user))).status_code == 200
