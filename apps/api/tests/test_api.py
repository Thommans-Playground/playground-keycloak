import uuid

import pytest
from fastapi.routing import APIRoute
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


@pytest.mark.ac("AC-75")
@pytest.mark.rule("RULE-A5")
def test_bootstrap_admin_needs_a_verified_email(client):
    r = client.get("/me", headers=auth("sub-fake", "ada@x.test", verified=False)).json()
    assert (r["role"], r["status"]) == ("user", "pending")


@pytest.mark.ac("AC-74")
@pytest.mark.rule("RULE-A5")
def test_the_setup_email_makes_the_first_administrator(client):
    r = client.get("/me", headers=auth("sub-ada", "ada@x.test", name="Ada")).json()
    assert (r["role"], r["status"]) == ("administrator", "active")


@pytest.mark.ac("AC-61")
@pytest.mark.rule("RULE-A5")
def test_the_setup_email_with_another_sub_is_pending_once_an_administrator_exists(client, admin):
    r = client.get("/me", headers=auth("sub-ada-2", "ada@x.test", name="Ada 2")).json()
    assert (r["role"], r["status"]) == ("user", "pending")
    assert client.get("/me", headers=admin).json()["role"] == "administrator"
    action = [e["action"] for e in client.get("/audit", headers=admin).json() if e["target_id"] == r["id"]]
    assert action == ["register"]


def test_name_and_email_follow_the_token_but_identity_is_the_link(client):
    old = client.get("/me", headers=auth("sub-m", "m@x.test", name="Old")).json()
    new = client.get("/me", headers=auth("sub-m", "renamed@x.test", name="New")).json()
    assert new["id"] == old["id"] and new["email"] == "renamed@x.test" and new["name"] == "New"


FIVE = ("approve", "deactivate", "reinstate", "promote", "demote")


def _refused_all_five(client, admin, idp, actor):
    _, target_id = register(client, "sub-target", "target@x.test")
    idp.calls.clear()
    for action in FIVE:
        r = client.post(f"/accounts/{target_id}/{action}", headers=actor, json={"reason": "Not allowed to"})
        assert r.status_code == 403, action
    shown = next(a for a in client.get("/accounts", headers=admin).json() if a["id"] == target_id)
    assert (shown["status"], shown["role"]) == ("pending", "user")
    assert idp.calls == [], "nothing reached Keycloak"


# FR-4: an approved ordinary user is refused all five commands, and the target stays as it was
@pytest.mark.ac("AC-63")
def test_an_ordinary_user_is_refused_all_five_commands(client, admin, idp):
    actor, actor_id = register(client, "sub-actor", "actor@x.test")
    assert client.post(f"/accounts/{actor_id}/approve", headers=admin).status_code == 200
    _refused_all_five(client, admin, idp, actor)


@pytest.mark.ac("AC-63")
def test_a_pending_person_is_refused_all_five_commands(client, admin, idp):
    actor, _ = register(client, "sub-actor", "actor@x.test")
    _refused_all_five(client, admin, idp, actor)


@pytest.mark.ac("AC-63")
def test_a_deactivated_person_is_refused_all_five_commands(client, admin, idp):
    actor, actor_id = register(client, "sub-actor", "actor@x.test")
    client.post(f"/accounts/{actor_id}/approve", headers=admin)
    client.post(f"/accounts/{actor_id}/promote", headers=admin, json={"reason": "Helps approve"})
    client.post(f"/accounts/{actor_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    _refused_all_five(client, admin, idp, actor)


def _api_routes(app_or_router):
    """Every APIRoute, also those of included routers (FastAPI keeps an included router as a wrapper)."""
    for r in app_or_router.routes:
        if isinstance(r, APIRoute):
            yield r
        elif hasattr(r, "original_router"):
            yield from _api_routes(r.original_router)


# FR-3: every route but /me and /health is closed to a pending person
@pytest.mark.ac("AC-4")
def test_every_route_but_me_and_health_refuses_a_pending_person(client, admin):
    pending, _ = register(client, "sub-maya", "maya@x.test")
    skipped = {"/me", "/health", "/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}
    routes = [r for r in _api_routes(client.app) if r.path not in skipped]
    assert len(routes) >= 7, "the table must really cover the routes"
    for route in routes:
        path = route.path.replace("{account_id}", str(uuid.uuid4()))
        for method in route.methods:
            kwargs = {"json": {"reason": "a reason"}} if method in {"POST", "PUT", "PATCH", "DELETE"} else {}
            r = client.request(method, path, headers=pending, **kwargs)
            assert (r.status_code, r.json()["detail"]["code"]) == (403, "account_pending"), f"{method} {route.path}"


# FR-4: approving what does not exist, or what is not pending, is refused and leaves no trace
@pytest.mark.ac("AC-76")
def test_approving_an_unknown_or_not_pending_account_is_refused_and_changes_nothing(client, admin, idp):
    _, maya_id = register(client, "sub-maya", "maya@x.test")
    client.post(f"/accounts/{maya_id}/approve", headers=admin)
    before_audit = client.get("/audit", headers=admin).json()
    before_accounts = client.get("/accounts", headers=admin).json()

    r = client.post(f"/accounts/{uuid.uuid4()}/approve", headers=admin)
    assert (r.status_code, r.json()["code"]) == (404, "account_not_found")
    r = client.post(f"/accounts/{maya_id}/approve", headers=admin)  # already active
    assert (r.status_code, r.json()["code"]) == (409, "invalid_transition")

    assert client.get("/audit", headers=admin).json() == before_audit
    assert client.get("/accounts", headers=admin).json() == before_accounts
    assert idp.calls == []


# decision 10: identity is the sub, never the email. No criterion; this kills the mutation "match by email".
def test_a_known_email_with_a_new_sub_does_not_take_over_the_account(client):
    first = client.get("/me", headers=auth("sub-one", "same@x.test", name="First")).json()
    second = client.get("/me", headers=auth("sub-two", "same@x.test", name="Second")).json()
    assert second["id"] != first["id"], "a second account, not the first one"
    assert second["status"] == "pending" and second["role"] == "user"
    again = client.get("/me", headers=auth("sub-one", "same@x.test", name="First")).json()
    assert again == first, "the first account is unchanged"


# approving does not call Keycloak, and a user cannot approve
@pytest.mark.ac("AC-5")
def test_administrator_approves_and_member_cannot(client, admin, idp):
    maya, maya_id = register(client, "sub-maya", "maya@x.test")
    bob, bob_id = register(client, "sub-bob", "bob@x.test")
    assert client.post(f"/accounts/{bob_id}/approve", headers=maya).status_code == 403  # pending
    assert client.post(f"/accounts/{maya_id}/approve", headers=admin).json()["status"] == "active"
    assert client.get("/me", headers=maya).json()["status"] == "active"  # the next request shows it
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


@pytest.mark.ac("AC-59")
def test_keycloak_failure_changes_nothing(client, admin, idp):
    maya, maya_id = register(client, "sub-maya", "maya@x.test")
    client.post(f"/accounts/{maya_id}/approve", headers=admin)
    client.post(f"/accounts/{maya_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    idp.fail = True
    r = client.post(f"/accounts/{maya_id}/reinstate", headers=admin, json={"reason": "Came back"})
    assert (r.status_code, r.json()["code"]) == (502, "identity_provider_unavailable")
    assert "Keycloak" in r.json()["message"]  # the administrator is told what failed
    assert client.get("/me", headers=maya).json()["detail"]["code"] == "account_deactivated"


def test_every_change_is_audited_with_its_reason(client, admin):
    maya, maya_id = register(client, "sub-maya", "maya@x.test")
    client.post(f"/accounts/{maya_id}/approve", headers=admin)
    client.post(f"/accounts/{maya_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    entries = client.get("/audit", headers=admin).json()
    assert [(e["action"], e["reason"]) for e in entries[:2]] == [("deactivate", "Left the team"), ("approve", None)]
    assert entries[0]["actor_id"] == me_id(client, admin)


# AC-73 and decision 10: same email, different sub: two accounts, each warns about the other. Nothing is blocked.
@pytest.mark.ac("AC-73")
def test_the_list_warns_of_accounts_with_the_same_email_and_approving_is_still_allowed(client, admin):
    first, second = auth("sub-one", "same@x.test", name="One"), auth("sub-two", "Same@x.test ", name="Two")
    first_id, second_id = me_id(client, first), me_id(client, second)
    assert first_id != second_id
    listed = {a["id"]: a for a in client.get("/accounts", headers=admin).json()}
    assert listed[second_id]["status"] == "pending"
    assert listed[first_id]["duplicate_of"] == [{"id": second_id, "name": "Two", "status": "pending"}]
    assert listed[second_id]["duplicate_of"] == [{"id": first_id, "name": "One", "status": "pending"}]
    assert [a["duplicate_of"] for a in listed.values() if a["email"] == "ada@x.test"] == [[]]
    assert "duplicate_of" not in client.get("/me", headers=first).json()
    # a deactivated account with the same email still counts, and approving the duplicate still works
    assert client.post(f"/accounts/{first_id}/approve", headers=admin).status_code == 200
    client.post(f"/accounts/{first_id}/deactivate", headers=admin, json={"reason": "Left the team"})
    listed = {a["id"]: a for a in client.get("/accounts", headers=admin).json()}
    assert listed[second_id]["duplicate_of"] == [{"id": first_id, "name": "One", "status": "deactivated"}]
    assert client.post(f"/accounts/{second_id}/approve", headers=admin).json()["status"] == "active"
