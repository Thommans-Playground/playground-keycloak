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
    # PostgreSQL, as on Amazon RDS. `docker compose up -d api-db` starts it on localhost:5433.
    database_url: str = "postgresql+psycopg://playground_api:playground-api-dev@localhost:5433/playground"
    # The role the API connects with (created by migration 0002). Only the migration reads this one.
    api_db_user: str = "playground_api"
    # Comma separated. While no administrator exists, a person with one of these verified emails becomes one.
    # Empty by default: with nothing set, nobody becomes an administrator (fail closed). Local work sets it.
    bootstrap_admin_emails: str = ""

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
