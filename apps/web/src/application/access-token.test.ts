// Verifies UC-A6: keep the session alive. The refresh is one at a time for each session.
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { makeAccessToken } from "./access-token.ts";
import { InMemorySessionStore } from "../adapters/in-memory-stores.ts";
import { FakeIdentityProvider, FakeSecurityLog } from "../testing/fakes.ts";
import type { Session } from "../domain/session.ts";

let now = 1_000_000;
let idp: FakeIdentityProvider;
let sessions: InMemorySessionStore;
let log: FakeSecurityLog;
let accessTokenFor: (id: string | undefined) => Promise<string | null>;
const session = (accessExpiresAt: number): Session => ({
  idToken: "i",
  accessToken: "at-old",
  refreshToken: "r",
  accessExpiresAt,
});

beforeEach(() => {
  now = 1_000_000;
  idp = new FakeIdentityProvider(() => now);
  sessions = new InMemorySessionStore();
  log = new FakeSecurityLog();
  accessTokenFor = makeAccessToken({ idp, sessions, now: () => now, log });
});

test("no session id, or an unknown one, gives no token", async () => {
  assert.equal(await accessTokenFor(undefined), null);
  assert.equal(await accessTokenFor("unknown"), null);
});

test("a token with time left is returned and nothing is refreshed", async () => {
  await sessions.put("s1", session(now + 120_000));
  assert.equal(await accessTokenFor("s1"), "at-old");
  assert.equal(idp.refreshes, 0);
});

test("a token about to expire is refreshed, and the new one is kept (Verifies AC-52)", async () => {
  await sessions.put("s1", session(now + 10_000));
  assert.equal(await accessTokenFor("s1"), "at-refreshed-1");
  assert.equal((await sessions.get("s1"))?.accessToken, "at-refreshed-1");
});

test("two requests at once share one refresh (Verifies AC-53)", async () => {
  await sessions.put("s1", session(now + 10_000));
  let release!: () => void;
  idp.gate = new Promise<void>((r) => (release = r));
  const a = accessTokenFor("s1");
  const b = accessTokenFor("s1");
  release();
  assert.deepEqual(await Promise.all([a, b]), ["at-refreshed-1", "at-refreshed-1"]);
  assert.equal(idp.refreshes, 1);
});

test("when Keycloak refuses the refresh the session ends (Verifies AC-54)", async () => {
  await sessions.put("s1", session(now + 10_000));
  idp.refreshFails = true;
  assert.equal(await accessTokenFor("s1"), null);
  assert.equal(await sessions.get("s1"), null);
  assert.equal(await accessTokenFor("s1"), null);
});

test("a token with time left, and a good refresh, write nothing (Verifies AC-48)", async () => {
  await sessions.put("s1", session(now + 120_000));
  await accessTokenFor("s1");
  await sessions.put("s2", session(now + 10_000));
  await accessTokenFor("s2");
  assert.deepEqual(log.events, []);
});

test("a refused refresh writes token_refresh refused and session_end ok, once for two shared callers (Verifies AC-48)", async () => {
  await sessions.put("s1", session(now + 10_000));
  idp.refreshFails = true;
  let release!: () => void;
  idp.gate = new Promise<void>((r) => (release = r));
  const a = accessTokenFor("s1");
  const b = accessTokenFor("s1");
  release();
  await Promise.all([a, b]);
  assert.deepEqual(log.events, [
    { name: "token_refresh", result: "refused", sessionId: "s1", reason: "refresh_refused" },
    { name: "session_end", result: "ok", sessionId: "s1", reason: "refresh_refused" },
  ]);
  assert.ok(!JSON.stringify(log.events).includes("at-old"));
});
