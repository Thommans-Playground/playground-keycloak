from fastapi.testclient import TestClient

from {{PACKAGE}}.main import create_app


def test_health_reports_ok() -> None:
    assert TestClient(create_app()).get("/health").json() == {"status": "ok"}
