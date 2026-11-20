import time

import httpx

from app.infrastructure.config import Settings


class KeycloakAdmin:
    """Enable, disable and sign out people, using the `playground-backend` service account."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self._s = settings
        self._http = client or httpx.Client(timeout=10)
        self._token: str | None = None
        self._expires = 0.0

    def _bearer(self) -> dict[str, str]:
        if not self._token or time.time() > self._expires - 10:
            r = self._http.post(
                f"{self._s.internal_realm_url}/protocol/openid-connect/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._s.keycloak_backend_client_id,
                    "client_secret": self._s.keycloak_backend_client_secret,
                },
            )
            r.raise_for_status()
            body = r.json()
            self._token = body["access_token"]
            self._expires = time.time() + body["expires_in"]
        return {"Authorization": f"Bearer {self._token}"}

    @property
    def _users(self) -> str:
        return f"{self._s.keycloak_internal_url or self._s.keycloak_url}/admin/realms/{self._s.keycloak_realm}/users"

    def _set_enabled(self, identity: str, enabled: bool) -> None:
        # Send the whole user back: a partial PUT can fail the realm's user profile checks.
        r = self._http.get(f"{self._users}/{identity}", headers=self._bearer())
        r.raise_for_status()
        user = r.json()
        user["enabled"] = enabled
        self._http.put(f"{self._users}/{identity}", headers=self._bearer(), json=user).raise_for_status()

    def enable_user(self, identity: str) -> None:
        self._set_enabled(identity, True)

    def disable_user(self, identity: str) -> None:
        self._set_enabled(identity, False)

    def end_sessions(self, identity: str) -> None:
        self._http.post(f"{self._users}/{identity}/logout", headers=self._bearer()).raise_for_status()
