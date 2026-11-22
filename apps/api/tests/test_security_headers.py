import pytest


# NFR-6
@pytest.mark.ac("AC-96")
def test_every_answer_carries_the_security_headers(client):
    answers = {"ok answer (/health)": client.get("/health"), "refused answer (/me, no token)": client.get("/me")}
    assert answers["refused answer (/me, no token)"].status_code == 401
    for name, r in answers.items():
        csp = r.headers.get("content-security-policy", "")
        assert "frame-ancestors 'none'" in csp, name
        assert r.headers.get("x-content-type-options") == "nosniff", name
        assert r.headers.get("referrer-policy"), name
