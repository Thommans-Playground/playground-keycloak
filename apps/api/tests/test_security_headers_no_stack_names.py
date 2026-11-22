# Names that tell an attacker which framework or server answers.
STACK_NAMES = ("uvicorn", "starlette", "fastapi", "python", "express", "next.js")


# NFR-6 (a guard, not the proof of AC-97)
# This sees only the app under the test client. The `server: uvicorn` header is added by the uvicorn server, not by
# the app, so it is out of reach here. It checks that our own code never sets `server` or `x-powered-by`. It carries
# no AC-97 tag on purpose: AC-97 is proved by tests/integration/test_security_headers_running.py, which reads the
# headers of the running server.
def test_no_answer_of_the_api_carries_a_header_naming_the_framework(client):
    answers = [client.get("/health"), client.get("/me")]  # an answer, and a refused one (no token)
    assert answers[1].status_code == 401
    for answer in answers:
        headers = {k.lower(): v.lower() for k, v in answer.headers.items()}
        assert "x-powered-by" not in headers
        server = headers.get("server", "")
        assert not any(name in server for name in STACK_NAMES), f"server header names the stack: {server}"
