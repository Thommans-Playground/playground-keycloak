import assert from "node:assert/strict";
import { test } from "node:test";
import { needsRefresh, REFRESH_SKEW_MS, type Session } from "./session.ts";

const session = (accessExpiresAt: number): Session => ({ idToken: "i", accessToken: "a", refreshToken: "r", accessExpiresAt });

test("a token with more than 30 seconds left is used as it is (Verifies AC-52, RULE-A10)", () => {
  assert.equal(REFRESH_SKEW_MS, 30_000);
  assert.equal(needsRefresh(session(100_000), 100_000 - 30_001), false);
});

test("a token with 30 seconds or less left is refreshed first (Verifies AC-52, RULE-A10)", () => {
  assert.equal(needsRefresh(session(100_000), 100_000 - 30_000), true);
  assert.equal(needsRefresh(session(100_000), 100_001), true);
});
