import pytest

from app.access.service import AccessService
from app.config import Settings
from tests.fakes import FakeAccounts, FakeAudit, FakeIdp


@pytest.mark.ac("AC-75")
@pytest.mark.rule("RULE-A5")
def test_the_setup_list_fails_closed_when_nothing_is_set(monkeypatch):
    monkeypatch.delenv("BOOTSTRAP_ADMIN_EMAILS", raising=False)
    settings = Settings(_env_file=None)  # no .env, no environment: the code default alone
    assert settings.bootstrap_admins == set()
    svc = AccessService(FakeAccounts(), FakeAudit(), FakeIdp(), settings.bootstrap_admins)
    for email in ("admin@example.test", "ada@x.test"):
        assert svc.account_for(f"sub-{email}", "Someone", email, True).status.value == "pending"
