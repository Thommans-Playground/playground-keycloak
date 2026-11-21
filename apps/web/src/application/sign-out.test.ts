// UC-A2: signing out forgets our session and points at Keycloak's end session address.
// A person with no session of ours goes home and Keycloak is not asked (decision 15).
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { signOut } from "./sign-out.ts";
import { InMemorySessionStore } from "../adapters/in-memory-stores.ts";
import { FakeIdentityProvider, FakeSecurityLog } from "../testing/fakes.ts";

let idp: FakeIdentityProvider;
let sessions: InMemorySessionStore;
let log: FakeSecurityLog;
beforeEach(async () => {
  idp = new FakeIdentityProvider();
  log = new FakeSecurityLog();
  sessions = new InMemorySessionStore();
  await sessions.put("s1", { idToken: "the-id-token", accessToken: "a", refreshToken: "r", accessExpiresAt: 1 });
});

test("SO-1: the session is forgotten and the answer is Keycloak's address with the ID token as a hint (Verifies AC-2)", async () => {
  const { redirectTo } = await signOut({ idp, sessions, log }, "s1");
  assert.equal(redirectTo, "https://kc.test/logout?hint=the-id-token");
  assert.equal(await sessions.get("s1"), null);
});

test("signing out twice is harmless: the second time the person goes home and Keycloak is not asked", async () => {
  await signOut({ idp, sessions, log }, "s1");
  idp.endSessionCalls = 0;
  const again = await signOut({ idp, sessions, log }, "s1");
  assert.equal(again.redirectTo, null);
  assert.equal(idp.endSessionCalls, 0);
});

test("signing out with no cookie goes home and Keycloak is not asked", async () => {
  const { redirectTo } = await signOut({ idp, sessions, log }, undefined);
  assert.equal(redirectTo, null);
  assert.equal(idp.endSessionCalls, 0);
});

test("a session id nobody holds gets the same answer as no cookie", async () => {
  const { redirectTo } = await signOut({ idp, sessions, log }, "not-a-session");
  assert.equal(redirectTo, null);
  assert.equal(idp.endSessionCalls, 0);
});

test("if the session store fails the person still goes home, and the route can clear the cookie", async () => {
  const broken = {
    ...sessions,
    take: async () => {
      throw new Error("the store is down");
    },
  } as unknown as InMemorySessionStore;
  const { redirectTo } = await signOut({ idp, sessions: broken, log }, "s1");
  assert.equal(redirectTo, null);
});

test("if Keycloak cannot be reached our session is still gone and the answer is to go home", async () => {
  idp.endSessionFails = true;
  const { redirectTo } = await signOut({ idp, sessions, log }, "s1");
  assert.equal(redirectTo, null);
  assert.equal(await sessions.get("s1"), null);
});

test("signing out a real session writes one session_end ok line, reason sign_out (Verifies AC-48)", async () => {
  await signOut({ idp, sessions, log }, "s1");
  assert.deepEqual(log.events, [{ name: "session_end", result: "ok", sessionId: "s1", reason: "sign_out" }]);
  assert.ok(!JSON.stringify(log.events).includes("the-id-token"));
});

test("signing out with no session, a second time or a store that fails writes nothing (Verifies AC-48)", async () => {
  await signOut({ idp, sessions, log }, undefined);
  await signOut({ idp, sessions, log }, "not-a-session");
  await signOut({ idp, sessions, log }, "s1");
  log.events.length = 0;
  await signOut({ idp, sessions, log }, "s1");
  const broken = {
    take: async () => {
      throw new Error("the store is down");
    },
  } as unknown as InMemorySessionStore;
  await signOut({ idp, sessions: broken, log }, "s2");
  assert.deepEqual(log.events, []);
});

test("if Keycloak cannot be reached the session still ended, so session_end is still written (Verifies AC-48)", async () => {
  idp.endSessionFails = true;
  await signOut({ idp, sessions, log }, "s1");
  assert.equal(log.events.length, 1);
});
