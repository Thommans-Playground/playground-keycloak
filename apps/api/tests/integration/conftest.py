import httpx
import pytest

from tests.integration import helpers


@pytest.fixture(scope="session", autouse=True)
def stack_is_up():
    """With INTEGRATION=1 an unreachable stack is a failure, never a skip."""
    for name, url in (("Keycloak", f"{helpers.REALM_URL}/.well-known/openid-configuration"),
                      ("API", f"{helpers.API_URL}/health")):
        try:
            httpx.get(url, timeout=5).raise_for_status()
        except Exception as exc:
            pytest.fail(f"{name} is not reachable at {url}: {exc}", pytrace=False)


@pytest.fixture
def throwaway_user():
    user = helpers.create_user()
    try:
        yield user
    finally:
        helpers.delete_user(user.id)
