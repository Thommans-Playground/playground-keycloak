"""Helpers for the integration tests: a real Keycloak, real HTTP, no browser.

Addresses come from the environment, with local defaults (the docker compose stack)."""

import base64
import hashlib
import html
import os
import re
import secrets
import time
from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

import httpx

from app.infrastructure.config import Settings

KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
API_URL = os.environ.get("API_URL", "http://localhost:8000")
REALM = os.environ.get("KEYCLOAK_REALM", "playground")
WEB_CLIENT_ID = "playground-web"
WEB_CLIENT_SECRET = os.environ.get("WEB_CLIENT_SECRET", "playground-web-dev-secret")  # docker-compose.yml
REDIRECT_URI = "http://localhost:3000/auth/callback"  # the one registered for playground-web
PASSWORD = "It-Passw0rd!x"
ADMIN_EMAIL, ADMIN_PASSWORD = "admin@example.test", "Admin123!"
TIMEOUT = 10

REALM_URL = f"{KEYCLOAK_URL}/realms/{REALM}"
ADMIN_USERS = f"{KEYCLOAK_URL}/admin/realms/{REALM}/users"
OIDC = f"{REALM_URL}/protocol/openid-connect"


def settings() -> Settings:
    """Settings as the API would have them for this stack (backend client id and secret from app/config.py)."""
    return Settings(keycloak_url=KEYCLOAK_URL, keycloak_realm=REALM)


@dataclass
class User:
    id: str
    email: str
    password: str = PASSWORD


class LoginRefused(Exception):
    """Keycloak answered the login form with an error instead of a redirect."""


def admin_headers(client: httpx.Client | None = None) -> dict[str, str]:
    """A fresh service account token of playground-backend, straight from Keycloak."""
    s = settings()
    r = (client or httpx).post(
        f"{OIDC}/token",
        timeout=TIMEOUT,
        data={
            "grant_type": "client_credentials",
            "client_id": s.keycloak_backend_client_id,
            "client_secret": s.keycloak_backend_client_secret,
        },
    )
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def kc_user(user_id: str) -> httpx.Response:
    return httpx.get(f"{ADMIN_USERS}/{user_id}", headers=admin_headers(), timeout=TIMEOUT)


def kc_sessions(user_id: str) -> list:
    r = httpx.get(f"{ADMIN_USERS}/{user_id}/sessions", headers=admin_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def create_user(email: str | None = None, password: str = PASSWORD) -> User:
    email = email or f"it-{int(time.time())}-{secrets.token_hex(4)}@example.test"
    r = httpx.post(
        ADMIN_USERS,
        headers=admin_headers(),
        timeout=TIMEOUT,
        json={
            "username": email,
            "email": email,
            "firstName": "Integration",
            "lastName": "Test",
            "enabled": True,
            "emailVerified": True,
            "credentials": [{"type": "password", "value": password, "temporary": False}],
        },
    )
    r.raise_for_status()
    return User(id=r.headers["Location"].rsplit("/", 1)[1], email=email, password=password)


def delete_user(user_id: str) -> None:
    httpx.delete(f"{ADMIN_USERS}/{user_id}", headers=admin_headers(), timeout=TIMEOUT)


def login(user: User | str, password: str | None = None) -> str:
    """Authorization code flow with PKCE as playground-web, without a browser. Returns the access token.
    Raises LoginRefused when Keycloak shows the login form again with an error."""
    username = user.email if isinstance(user, User) else user
    password = password if password is not None else user.password
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(8)
    jar: dict[str, str] = {}

    def keep_cookies(response: httpx.Response) -> None:
        # Keycloak marks its cookies Secure even on http://localhost (browsers allow that, httpx does not),
        # so keep them by hand and send them on every request.
        for line in response.headers.get_list("set-cookie"):
            name, _, rest = line.partition("=")
            value = rest.split(";", 1)[0].strip('"')
            if value:
                jar[name.strip()] = value
            else:
                jar.pop(name.strip(), None)

    def send_cookies(request: httpx.Request) -> None:
        if jar:
            request.headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in jar.items())

    with httpx.Client(timeout=TIMEOUT, event_hooks={"request": [send_cookies], "response": [keep_cookies]}) as http:
        page = http.get(
            f"{OIDC}/auth",
            params={
                "client_id": WEB_CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "response_type": "code",
                "scope": "openid",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )
        assert page.status_code == 200, page.headers.get("location")
        form = re.search(r'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"', page.text) or re.search(
            r'<form[^>]*action="([^"]+)"[^>]*id="kc-form-login"', page.text
        )
        assert form, "the login form (kc-form-login) was not found"
        url = html.unescape(form.group(1))
        resp = http.post(url, data={"username": username, "password": password, "credentialId": ""})
        for _ in range(10):
            if resp.status_code not in (301, 302, 303, 307):
                raise LoginRefused(f"status {resp.status_code}: " + _error_text(resp.text))
            location = urljoin(str(resp.url), resp.headers["Location"])
            if location.startswith(REDIRECT_URI):
                break
            resp = http.get(location)
        else:
            raise LoginRefused("too many redirects")
        query = parse_qs(urlparse(location).query)
        assert query["state"] == [state]
        token = http.post(
            f"{OIDC}/token",
            data={
                "grant_type": "authorization_code",
                "code": query["code"][0],
                "redirect_uri": REDIRECT_URI,
                "client_id": WEB_CLIENT_ID,
                "client_secret": WEB_CLIENT_SECRET,
                "code_verifier": verifier,
            },
        )
        token.raise_for_status()
        return token.json()["access_token"]


def _error_text(page: str) -> str:
    m = re.search(r'id="input-error[^"]*"[^>]*>\s*(.*?)\s*</span>', page, re.S) or re.search(
        r'class="[^"]*alert-error[^"]*"[^>]*>.*?<span[^>]*>\s*(.*?)\s*</span>', page, re.S
    )
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else "(no error text found)"


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
