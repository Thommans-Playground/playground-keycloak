// AC-48 / NFR-5 / ADR 0010: one JSON line for each event, only the allowed keys, no secret.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";
import { JsonSecurityLog } from "./json-security-log.ts";

function make() {
  const out: string[] = [];
  return {
    out,
    log: new JsonSecurityLog(
      (line) => out.push(line),
      () => new Date("2026-11-20T10:00:00.000Z"),
    ),
  };
}
const ALLOWED = new Set(["ts", "event", "result", "person_id", "session", "reason"]);
const TOKEN = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxMjMifQ.c2lnbmF0dXJl";

test("one event is one line of valid JSON ending in a newline, with the expected keys (Verifies AC-48)", () => {
  const { out, log } = make();
  log.event({ name: "sign_in", result: "refused", personId: "p-1", sessionId: "abc", reason: "login_expired" });
  assert.equal(out.length, 1);
  assert.ok(out[0].endsWith("\n"));
  assert.equal(out[0].trim().split("\n").length, 1);
  const o = JSON.parse(out[0]);
  assert.deepEqual(Object.keys(o).sort(), [...ALLOWED].sort());
  assert.equal(o.ts, "2026-11-20T10:00:00.000Z");
  assert.equal(o.event, "sign_in");
  assert.equal(o.result, "refused");
  assert.equal(o.person_id, "p-1");
  assert.equal(o.reason, "login_expired");
});

test("the session is the first 16 hex characters of its SHA-256, never the id (Verifies AC-48)", () => {
  const { out, log } = make();
  log.event({ name: "session_start", result: "ok", sessionId: "the-raw-session-id" });
  const o = JSON.parse(out[0]);
  assert.equal(o.session, createHash("sha256").update("the-raw-session-id").digest("hex").slice(0, 16));
  assert.match(o.session, /^[0-9a-f]{16}$/);
  assert.ok(!out[0].includes("the-raw-session-id"));
});

test("keys that are not known are left out, and nothing outside the allowed keys is written (Verifies AC-48)", () => {
  const { out, log } = make();
  log.event({ name: "sign_in", result: "ok", accessToken: TOKEN, code: "abc", state: "s" } as never);
  const o = JSON.parse(out[0]);
  for (const k of Object.keys(o)) assert.ok(ALLOWED.has(k), k);
  assert.ok(!out[0].includes(TOKEN));
});

test("a reason that is not a short [a-z_] code is dropped, so a token cannot reach the output (Verifies AC-48)", () => {
  for (const bad of [TOKEN, "Login Expired", "a".repeat(100), "code=abc123", ""]) {
    const { out, log } = make();
    log.event({ name: "sign_in", result: "refused", reason: bad });
    const o = JSON.parse(out[0]);
    assert.ok(!("reason" in o), `kept ${bad}`);
    if (bad) assert.ok(!out[0].includes(bad));
  }
});

test("a token-looking session id is only ever written as its hash (Verifies AC-48)", () => {
  const { out, log } = make();
  log.event({ name: "session_end", result: "ok", sessionId: TOKEN });
  assert.ok(!out[0].includes(TOKEN));
  assert.match(JSON.parse(out[0]).session, /^[0-9a-f]{16}$/);
});

test("person_id and session are left out when not known (Verifies AC-48)", () => {
  const { out, log } = make();
  log.event({ name: "sign_in", result: "refused", reason: "login_failed" });
  const o = JSON.parse(out[0]);
  assert.ok(!("person_id" in o) && !("session" in o));
});
