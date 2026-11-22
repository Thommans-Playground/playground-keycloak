"""The headers the RUNNING API sends, as a browser or an attacker sees them. NFR-6.

The unit test client calls the app directly, so it never sees what the server adds on the way out (the `server`
header comes from uvicorn). This reads a real answer from the running stack."""

import httpx
import pytest

from tests.integration import helpers

pytestmark = pytest.mark.integration

# Names that tell an attacker which framework or server answers.
STACK_NAMES = ("uvicorn", "starlette", "fastapi", "python")


@pytest.mark.ac("AC-97")
def test_no_answer_of_the_running_api_names_the_framework_or_server():
    with httpx.Client(base_url=helpers.API_URL, timeout=helpers.TIMEOUT) as c:
        answers = [c.get("/health"), c.get("/me")]  # an answer, and a refused one (no token)
    assert answers[1].status_code == 401
    for answer in answers:
        headers = {k.lower(): v.lower() for k, v in answer.headers.items()}
        assert "x-powered-by" not in headers
        server = headers.get("server", "")
        assert not any(name in server for name in STACK_NAMES), f"the server header names the stack: {server}"
