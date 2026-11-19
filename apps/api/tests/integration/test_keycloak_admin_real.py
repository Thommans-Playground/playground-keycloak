"""The real KeycloakAdmin adapter against the running Keycloak, with a throwaway user."""

import httpx
import pytest

from app.access.adapters.keycloak_admin import KeycloakAdmin
from tests.integration import helpers
from tests.integration.helpers import LoginRefused, login

pytestmark = pytest.mark.integration


@pytest.fixture
def admin():
    return KeycloakAdmin(helpers.settings(), httpx.Client(timeout=helpers.TIMEOUT))


@pytest.mark.ac("AC-6")
def test_disable_turns_the_user_off_and_keycloak_refuses_the_login(admin, throwaway_user):
    login(throwaway_user)  # works before
    admin.disable_user(throwaway_user.id)
    assert helpers.kc_user(throwaway_user.id).json()["enabled"] is False
    with pytest.raises(LoginRefused):
        login(throwaway_user)


@pytest.mark.ac("AC-7")
def test_enable_turns_the_user_on_and_the_login_works_again(admin, throwaway_user):
    admin.disable_user(throwaway_user.id)
    with pytest.raises(LoginRefused):
        login(throwaway_user)
    admin.enable_user(throwaway_user.id)
    assert helpers.kc_user(throwaway_user.id).json()["enabled"] is True
    assert login(throwaway_user)


def test_end_sessions_removes_the_keycloak_sessions(admin, throwaway_user):
    login(throwaway_user)
    assert helpers.kc_sessions(throwaway_user.id) != []
    admin.end_sessions(throwaway_user.id)
    assert helpers.kc_sessions(throwaway_user.id) == []


@pytest.mark.parametrize("call", ["disable_user", "enable_user", "end_sessions"])
def test_an_unknown_user_id_raises_an_http_status_error(admin, call):
    with pytest.raises(httpx.HTTPStatusError) as e:
        getattr(admin, call)("00000000-0000-0000-0000-000000000000")
    assert e.value.response.status_code == 404


def test_the_admin_token_is_obtained_once_and_reused(admin, throwaway_user, monkeypatch):
    posts = []
    real = admin._http.post

    def spy(url, *a, **kw):
        posts.append(url)
        return real(url, *a, **kw)

    monkeypatch.setattr(admin._http, "post", spy)
    admin.disable_user(throwaway_user.id)
    admin.enable_user(throwaway_user.id)
    token_calls = [u for u in posts if u.endswith("/protocol/openid-connect/token")]
    assert len(token_calls) == 1
    assert admin._token
