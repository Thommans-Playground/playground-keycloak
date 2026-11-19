import assert from "node:assert/strict";
import { test } from "node:test";
import { isExpired, LOGIN_ATTEMPT_TTL_MS, type LoginAttempt } from "./login-attempt.ts";

const attempt = (startedAt: number): LoginAttempt => ({ state: "s", nonce: "n", pkceVerifier: "v", returnTo: "/dashboard", startedAt });

test("an attempt lasts ten minutes (Verifies RULE-A8)", () => {
  assert.equal(LOGIN_ATTEMPT_TTL_MS, 10 * 60 * 1000);
});

test("SI-4: an attempt is live just before ten minutes and expired at ten (Verifies AC-38, RULE-A8)", () => {
  assert.equal(isExpired(attempt(0), LOGIN_ATTEMPT_TTL_MS - 1), false);
  assert.equal(isExpired(attempt(0), LOGIN_ATTEMPT_TTL_MS), true);
});
