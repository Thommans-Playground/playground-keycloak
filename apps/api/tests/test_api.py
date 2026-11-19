import pytest
from tests.conftest import KEY, OTHER_KEY, auth, make_token, me_id, register


# no token, expired token, token not from the identity provider
@pytest.mark.ac("AC-33")
def test_requests_without_a_valid_token_are_refused(client):
    assert client.get("/me").status_code == 401
    cases = {
        "expired": make_token("s", "a@x.test", expires_in=-10),
        "wrong signer": make_token("s", "a@x.test", key=OTHER_KEY),
        "wrong issuer": make_token("s", "a@x.test", issuer="http://evil.test/realms/playground"),
        "wrong audience": make_token("s", "a@x.test", audience="someone-else"),
    }
    for token in cases.values():
        r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401, token
        assert r.json()["detail"]["code"] == "invalid_token"


# FR-3
@pytest.mark.ac("AC-3")
def test_unknown_person_gets_one_pending_account(client):
    h = auth("sub-maya", "maya@x.test", name="Maya")
    first = client.get("/me", headers=h).json()
    assert (first["status"], first["role"]) == ("pending", "user")
    assert client.get("/me", headers=h).json()["id"] == first["id"]
    assert client.get("/me", headers=auth("sub-ada", "ada@x.test")).status_code == 200


# FR-3
@pytest.mark.ac("AC-4")
def test_pending_person_sees_only_their_status(client):
    h, _ = register(client, "sub-maya", "maya@x.test")
    assert client.get("/me", headers=h).json()["status"] == "pending"
    for path in ("/accounts", "/audit"):
        r = client.get(path, headers=h)
        assert (r.status_code, r.json()["detail"]["code"]) == (403, "account_pending")


def test_bootstrap_admin_needs_a_verified_email(client):
    r = client.get("/me", headers=auth("sub-fake", "ada@x.test", verified=False)).json()
    assert (r["role"], r["status"]) == ("user", "pending")


def test_name_and_email_follow_the_token_but_identity_is_the_link(client):
    old = client.get("/me", headers=auth("sub-m", "m@x.test", name="Old")).json()
    new = client.get("/me", headers=auth("sub-m", "renamed@x.test", name="New")).json()
    assert new["id"] == old["id"] and new["email"] == "renamed@x.test" and new["name"] == "New"


# approving does not call Keycloak, and a user cannot approve
@pytest.mark.ac("AC-5")
@pytest.mark.ac("AC-63")
def test_administrator_approves_and_member_cannot(client, admin, idp):
    maya, maya_id = register(client, "sub-maya", "maya@x.test")
    bob, bob_id = register(client, "sub-bob", "bob@x.test")
    assert client.post(f"/accounts/{bob_id}/approve", headers=maya).status_code == 403  # pending
    assert client.post(f"/accounts/{maya_id}/approve", headers=admin).json()["status"] == "active"
    assert idp.calls == []
    # Maya is active but a plain user: still cannot approve (NFR-1, AC-32)
    r = client.post(f"/accounts/{bob_id}/approve", headers=maya)
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "forbidden")
    assert client.get("/accounts", headers=admin).json()[-1]["status"] == "pending"


# FR-4
@pytest.mark.ac("AC-6")
@pytest.mark.ac("AC-64")
@pytest.mark.rule("RULE-A3")
def test_deactivate_needs_reason_disables_in_keycloak_and_blocks_next_request(client, admin, idp):
    maya, maya_id = register(client, "sub-maya", "maya@x.test")
    client.post(f"/accounts/{maya_id}/approve", headers=admin)

    r = client.post(f"/accounts/{maya_id}/deactivate", headers=admin, json={"reason": " "})
    assert (r.status_code, r.json()["code"]) == (422, "reason_required")
    assert client.get("/me", headers=maya).json()["status"] == "active"

    r = client.post(f"/accounts/{maya_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    assert r.json()["status"] == "deactivated"
    assert idp.calls == [("disable", "sub-maya"), ("logout", "sub-maya")]
    r = client.get("/me", headers=maya)  # the same, still valid token
    assert (r.status_code, r.json()["detail"]["code"]) == (403, "account_deactivated")
    assert any(a["id"] == maya_id and a["status"] == "deactivated" for a in client.get("/accounts", headers=admin).json())


# FR-4
@pytest.mark.ac("AC-7")
def test_reinstate_enables_in_keycloak(client, admin, idp):
    maya, maya_id = register(client, "sub-maya", "maya@x.test")
    client.post(f"/accounts/{maya_id}/approve", headers=admin)
    client.post(f"/accounts/{maya_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    idp.calls.clear()
    assert client.post(f"/accounts/{maya_id}/reinstate", headers=admin, json={"reason": "Came back"}).json()["status"] == "active"
    assert idp.calls == [("enable", "sub-maya")]
    assert client.get("/me", headers=maya).json()["status"] == "active"


# promote, demote and self change through the API
@pytest.mark.ac("AC-49")
@pytest.mark.ac("AC-50")
@pytest.mark.ac("AC-65")
@pytest.mark.rule("RULE-A2")
def test_admin_rules_over_http(client, admin):
    ada_id = me_id(client, admin)
    r = client.post(f"/accounts/{ada_id}/deactivate", headers=admin, json={"reason": "oops no"})
    assert (r.status_code, r.json()["code"]) == (403, "cannot_change_self")

    bob, bob_id = register(client, "sub-bob", "bob@x.test")
    client.post(f"/accounts/{bob_id}/approve", headers=admin)
    client.post(f"/accounts/{bob_id}/promote", headers=admin, json={"reason": "Helps approve"})
    # Now Bob can demote Ada, but cannot demote himself, and the last admin is kept
    assert client.post(f"/accounts/{ada_id}/demote", headers=bob, json={"reason": "Rotation"}).status_code == 200
    r = client.post(f"/accounts/{bob_id}/demote", headers=bob, json={"reason": "Rotation"})
    assert r.json()["code"] == "cannot_change_self"


def test_keycloak_failure_changes_nothing(client, admin, idp):
    maya, maya_id = register(client, "sub-maya", "maya@x.test")
    client.post(f"/accounts/{maya_id}/approve", headers=admin)
    idp.fail = True
    r = client.post(f"/accounts/{maya_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    assert (r.status_code, r.json()["code"]) == (502, "identity_provider_unavailable")
    assert client.get("/me", headers=maya).json()["status"] == "active"


def test_every_change_is_audited_with_its_reason(client, admin):
    maya, maya_id = register(client, "sub-maya", "maya@x.test")
    client.post(f"/accounts/{maya_id}/approve", headers=admin)
    client.post(f"/accounts/{maya_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    entries = client.get("/audit", headers=admin).json()
    assert [(e["action"], e["reason"]) for e in entries[:2]] == [("deactivate", "Left the team"), ("approve", None)]
    assert entries[0]["actor_id"] == me_id(client, admin)
