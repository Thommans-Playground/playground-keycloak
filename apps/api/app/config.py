from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    keycloak_url: str = "http://localhost:8080"
    # Where this process reaches Keycloak when that differs from the public address (Docker: http://keycloak:8080).
    keycloak_internal_url: str | None = None
    keycloak_realm: str = "playground"
    api_audience: str = "playground-api"
    keycloak_backend_client_id: str = "playground-backend"
    keycloak_backend_client_secret: str = "playground-backend-dev-secret"
    database_url: str = "sqlite:///./playground.db"
    # Comma separated. A person with one of these verified emails becomes the first administrator.
    bootstrap_admin_emails: str = "admin@example.test"

    @property
    def issuer(self) -> str:
        """The `iss` in tokens. Always the public address."""
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}"

    @property
    def internal_realm_url(self) -> str:
        return f"{self.keycloak_internal_url or self.keycloak_url}/realms/{self.keycloak_realm}"

    @property
    def bootstrap_admins(self) -> set[str]:
        return {e.strip().lower() for e in self.bootstrap_admin_emails.split(",") if e.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
