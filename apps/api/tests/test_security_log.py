"""NFR-5 / AC-48 (API half, ADR 0013) and AC-82 (UC-L1 step 6): refusals and the audit read write one log line,
never a token, and a read or a refusal never writes an audit entry."""

import io
import json
import re

import pytest

from app.infrastructure.security_log import JsonStdoutSecurityLog
from tests.conftest import OTHER_KEY, make_token, me_id, register

ALLOWED = {"ts", "event", "result", "person_id", "session", "reason"}
BEARER = make_token("sub-x", "secret@x.test")


def one(security_log):
    assert len(security_log.events) == 1, security_log.events
    return security_log.events[0]


def approved(client, admin, sub="sub-maya", email="maya@x.test"):
    h, pid = register(client, sub, email)
    client.post(f"/accounts/{pid}/approve", headers=admin)
    return h, pid


def trail_size(client, admin):
    return len(client.get("/audit", headers=admin).json())


# ---- AC-48, the guards ----


@pytest.mark.ac("AC-48")
def test_a_missing_token_is_logged_once(client, security_log):
    assert client.get("/me").status_code == 401
    assert security_log.events == [
        {
            "event": "request_refused",
            "result": "refused",
            "person_id": None,
            "session_id": None,
            "reason": "missing_token",
        }
    ]


@pytest.mark.ac("AC-48")
def test_an_invalid_token_is_logged_once_without_the_token(client, security_log):
    bad = make_token("s", "a@x.test", key=OTHER_KEY)
    assert client.get("/me", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
    e = one(security_log)
    assert (e["event"], e["result"], e["reason"], e["person_id"]) == (
        "request_refused",
        "refused",
        "invalid_token",
        None,
    )
    assert bad not in json.dumps(security_log.events)


@pytest.mark.ac("AC-48")
def test_a_pending_person_is_logged_with_their_id(client, security_log):
    h, pid = register(client, "sub-maya", "maya@x.test")
    security_log.events.clear()
    assert client.get("/accounts", headers=h).status_code == 403
    e = one(security_log)
    assert (e["reason"], e["person_id"], e["result"]) == ("account_pending", pid, "refused")


@pytest.mark.ac("AC-48")
def test_a_deactivated_person_is_logged_with_their_id(client, admin, security_log):
    h, pid = approved(client, admin)
    client.post(f"/accounts/{pid}/deactivate", headers=admin, json={"reason": "left the company"})
    security_log.events.clear()
    assert client.get("/me", headers=h).status_code == 403
    e = one(security_log)
    assert (e["reason"], e["person_id"]) == ("account_deactivated", pid)


@pytest.mark.ac("AC-48")
def test_a_non_administrator_is_logged_as_forbidden(client, admin, security_log):
    h, pid = approved(client, admin)
    security_log.events.clear()
    assert client.get("/accounts", headers=h).status_code == 403
    e = one(security_log)
    assert (e["reason"], e["person_id"]) == ("forbidden", pid)


@pytest.mark.ac("AC-48")
def test_a_rule_refusal_is_logged_with_the_actor_and_the_code(client, admin, security_log):
    ada = me_id(client, admin)
    security_log.events.clear()
    r = client.post(f"/accounts/{ada}/deactivate", headers=admin, json={"reason": "typed text, not logged"})
    assert r.status_code == 403
    e = one(security_log)
    assert (e["event"], e["result"], e["reason"], e["person_id"]) == (
        "request_refused",
        "refused",
        r.json()["code"],
        ada,
    )
    assert "typed text" not in json.dumps(security_log.events)


@pytest.mark.ac("AC-48")
def test_a_successful_request_logs_nothing(client, admin, security_log):
    assert client.get("/accounts", headers=admin).status_code == 200
    assert client.get("/me", headers=admin).status_code == 200
    assert security_log.events == []


# ---- AC-82, the audit read ----


@pytest.mark.ac("AC-82")
def test_an_administrator_who_reads_the_trail_writes_one_audit_read_line(client, admin, security_log):
    ada = me_id(client, admin)
    security_log.events.clear()
    assert client.get("/audit", headers=admin).status_code == 200
    e = one(security_log)
    assert (e["event"], e["result"], e["person_id"], e["reason"]) == ("audit_read", "ok", ada, None)


@pytest.mark.ac("AC-82")
def test_reading_the_trail_writes_no_audit_entry(client, admin):
    before = trail_size(client, admin)
    client.get("/audit", headers=admin)
    client.get("/audit", headers=admin)
    assert trail_size(client, admin) == before


@pytest.mark.ac("AC-82")
def test_a_refused_read_by_a_known_non_administrator_logs_forbidden_and_writes_no_entry(client, admin, security_log):
    h, pid = approved(client, admin)
    before = trail_size(client, admin)
    security_log.events.clear()
    assert client.get("/audit", headers=h).status_code == 403
    e = one(security_log)
    assert (e["event"], e["result"], e["reason"], e["person_id"]) == ("request_refused", "refused", "forbidden", pid)
    assert trail_size(client, admin) == before


@pytest.mark.ac("AC-82")
def test_a_refused_read_by_a_pending_person_logs_the_refusal_and_writes_no_entry(client, admin, security_log):
    h, pid = register(client, "sub-maya", "maya@x.test")
    before = trail_size(client, admin)
    security_log.events.clear()
    assert client.get("/audit", headers=h).status_code == 403
    e = one(security_log)
    assert (e["reason"], e["person_id"]) == ("account_pending", pid)
    assert trail_size(client, admin) == before


@pytest.mark.ac("AC-82")
def test_a_refused_read_with_no_token_logs_the_refusal_and_writes_no_entry(client, admin, security_log):
    before = trail_size(client, admin)
    security_log.events.clear()
    assert client.get("/audit").status_code == 401
    assert one(security_log)["reason"] == "missing_token"
    assert trail_size(client, admin) == before


# ---- AC-48, the adapter ----


def emit(**kw):
    out = io.StringIO()
    JsonStdoutSecurityLog(stream=out).event("request_refused", "refused", **kw)
    return out.getvalue()


@pytest.mark.ac("AC-48")
def test_the_adapter_writes_one_json_line_with_only_allowed_keys():
    text = emit(person_id="p-1", session_id="sid-123", reason="forbidden")
    assert text.endswith("\n") and text.count("\n") == 1
    line = json.loads(text)
    assert set(line) <= ALLOWED
    assert (line["event"], line["result"], line["person_id"], line["reason"]) == (
        "request_refused",
        "refused",
        "p-1",
        "forbidden",
    )
    assert line["ts"].endswith("+00:00") or line["ts"].endswith("Z")


@pytest.mark.ac("AC-48")
def test_optional_keys_are_absent_when_not_given():
    assert set(json.loads(emit())) == {"ts", "event", "result"}


@pytest.mark.ac("AC-48")
def test_the_session_is_a_16_character_hash_never_the_id():
    text = emit(session_id="raw-session-id")
    assert re.fullmatch(r"[0-9a-f]{16}", json.loads(text)["session"])
    assert "raw-session-id" not in text


@pytest.mark.ac("AC-48")
def test_a_token_given_as_reason_never_reaches_the_output():
    text = emit(reason=BEARER)
    assert BEARER not in text
    assert "reason" not in json.loads(text)


@pytest.mark.ac("AC-48")
def test_a_token_given_as_session_id_or_person_id_never_reaches_the_output():
    assert BEARER not in emit(session_id=BEARER)
    text = emit(person_id=BEARER)
    assert BEARER not in text and "person_id" not in json.loads(text)


@pytest.mark.ac("AC-48")
def test_free_text_reason_is_dropped_but_a_short_code_stays():
    assert "reason" not in json.loads(emit(reason="Left the company, see ticket 4"))
    assert json.loads(emit(reason="account_pending"))["reason"] == "account_pending"


@pytest.mark.ac("AC-48")
def test_an_event_or_result_that_is_not_a_short_code_is_replaced():
    out = io.StringIO()
    JsonStdoutSecurityLog(stream=out).event(BEARER, "Free text!")
    line = json.loads(out.getvalue())
    assert BEARER not in out.getvalue()
    assert (line["event"], line["result"]) == ("invalid_event", "invalid_result")


@pytest.mark.ac("AC-48")
def test_the_default_stream_is_stdout(capsys):
    JsonStdoutSecurityLog().event("request_refused", "refused", reason="forbidden")
    assert json.loads(capsys.readouterr().out)["reason"] == "forbidden"
