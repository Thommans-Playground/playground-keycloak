"""KeycloakAdmin against httpx.MockTransport: which calls it makes, in which order, with which body."""

import json

import httpx
import pytest

from app.access.adapters import keycloak_admin as module
from app.access.adapters.keycloak_admin import KeycloakAdmin
from app.config import Settings

SETTINGS = Settings(keycloak_url="http://kc.test", keycloak_realm="playground")
TOKEN_PATH = "/realms/playground/protocol/openid-connect/token"
USER = {"id": "sub-1", "username": "bo", "email": "bo@x.test", "enabled": True, "attributes": {"k": ["v"]}}


class Kc:
    """A tiny fake Keycloak that records every request."""

    def __init__(self, expires_in=300, fail_on=None, status=500):
        self.requests: list[httpx.Request] = []
        self.expires_in, self.fail_on, self.status = expires_in, fail_on, status
        self.tokens = 0

    def __call__(self, req: httpx.Request) -> httpx.Response:
        self.requests.append(req)
        if self.fail_on and self.fail_on(req):
            return httpx.Response(self.status)
        if req.url.path == TOKEN_PATH:
            self.tokens += 1
            return httpx.Response(200, json={"access_token": f"tok-{self.tokens}", "expires_in": self.expires_in})
        if req.method == "GET":
            return httpx.Response(200, json=dict(USER))
        return httpx.Response(204)

    def admin(self, **kw) -> KeycloakAdmin:
        return KeycloakAdmin(SETTINGS, httpx.Client(transport=httpx.MockTransport(self)))


def calls(kc):
    return [(r.method, r.url.path) for r in kc.requests]


# Verifies AC-6 (the Keycloak half): the person is disabled at Keycloak
def test_disable_gets_the_user_then_puts_the_whole_user_with_enabled_false():
    kc = Kc()
    kc.admin().disable_user("sub-1")
    assert calls(kc) == [("POST", TOKEN_PATH), ("GET", "/admin/realms/playground/users/sub-1"),
                         ("PUT", "/admin/realms/playground/users/sub-1")]
    put = kc.requests[-1]
    assert json.loads(put.content) == {**USER, "enabled": False}
    assert put.headers["Authorization"] == "Bearer tok-1"
    assert kc.requests[1].headers["Authorization"] == "Bearer tok-1"


# Verifies AC-7: the person is enabled again at Keycloak
def test_enable_puts_the_whole_user_with_enabled_true():
    kc = Kc()
    kc.admin().enable_user("sub-1")
    assert json.loads(kc.requests[-1].content) == {**USER, "enabled": True}
    assert kc.requests[-1].method == "PUT"


def test_end_sessions_posts_logout_with_no_body():
    kc = Kc()
    kc.admin().end_sessions("sub-1")
    assert calls(kc) == [("POST", TOKEN_PATH), ("POST", "/admin/realms/playground/users/sub-1/logout")]
    assert kc.requests[-1].content == b""
    assert kc.requests[-1].headers["Authorization"] == "Bearer tok-1"


def test_the_admin_token_is_asked_for_with_client_credentials():
    kc = Kc()
    kc.admin().end_sessions("sub-1")
    body = dict(p.split("=") for p in kc.requests[0].content.decode().split("&"))
    assert body == {"grant_type": "client_credentials", "client_id": "playground-backend",
                    "client_secret": "playground-backend-dev-secret"}
    assert kc.requests[0].method == "POST"


def test_the_token_is_reused_while_it_is_valid():
    kc = Kc(expires_in=300)
    admin = kc.admin()
    admin.disable_user("sub-1")
    admin.end_sessions("sub-1")
    assert kc.tokens == 1


def test_the_token_is_refreshed_when_close_to_expiry(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(module.time, "time", lambda: now[0])
    kc = Kc(expires_in=300)
    admin = kc.admin()
    admin.end_sessions("sub-1")
    now[0] += 289  # 11 seconds left: still reused
    admin.end_sessions("sub-1")
    assert kc.tokens == 1
    now[0] += 2  # 9 seconds left: inside the 10 second margin
    admin.end_sessions("sub-1")
    assert kc.tokens == 2
    assert kc.requests[-1].headers["Authorization"] == "Bearer tok-2"


def test_internal_url_is_used_for_calls_when_set():
    kc = Kc()
    s = Settings(keycloak_url="http://public.test", keycloak_internal_url="http://keycloak:8080")
    KeycloakAdmin(s, httpx.Client(transport=httpx.MockTransport(kc))).end_sessions("sub-1")
    assert {r.url.host for r in kc.requests} == {"keycloak"}


@pytest.mark.parametrize("call,failing", [
    ("enable_user", "token"), ("enable_user", "get"), ("enable_user", "put"),
    ("disable_user", "token"), ("disable_user", "get"), ("disable_user", "put"),
    ("end_sessions", "token"), ("end_sessions", "logout"),
])
def test_a_5xx_is_raised_as_an_http_status_error(call, failing):
    def hit(r):
        return {"token": r.url.path == TOKEN_PATH, "get": r.method == "GET", "put": r.method == "PUT",
                "logout": r.url.path.endswith("/logout")}[failing]

    with pytest.raises(httpx.HTTPStatusError):
        getattr(Kc(fail_on=hit).admin(), call)("sub-1")


def test_a_connection_error_is_raised_as_an_httpx_error():
    def boom(req):
        raise httpx.ConnectError("down", request=req)

    admin = KeycloakAdmin(SETTINGS, httpx.Client(transport=httpx.MockTransport(boom)))
    with pytest.raises(httpx.ConnectError):
        admin.disable_user("sub-1")


def test_the_service_turns_adapter_failures_into_identity_provider_unavailable():
    """The adapter raises httpx errors; the conversion is the service's job (service.py), not the adapter's."""
    from datetime import datetime
    from app.access.domain.account import Account, Action, Role, Status
    from app.access.service import AccessService, IdentityProviderUnavailable
    from tests.fakes import FakeAccounts, FakeAudit

    kc = Kc(fail_on=lambda r: r.url.path == TOKEN_PATH)
    ada = Account("a", "sa", "Ada", "a@x.test", Role.administrator, Status.active, datetime(2026, 1, 1))
    bo = Account("t", "sub-1", "Bo", "b@x.test", Role.user, Status.active, datetime(2026, 1, 2))
    accounts = FakeAccounts()
    accounts.add(ada)
    accounts.add(bo)
    svc = AccessService(accounts, FakeAudit(), kc.admin(), set())
    with pytest.raises(IdentityProviderUnavailable):
        svc.change(ada, "t", Action.deactivate, "left the company")
    assert accounts.by_id("t").status is Status.active
