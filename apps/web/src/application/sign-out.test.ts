// UC-A2: signing out forgets our session and points at Keycloak's end session address.
// A person with no session of ours goes home and Keycloak is not asked (decision 15).
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { signOut } from "./sign-out.ts";
import { InMemorySessionStore } from "../adapters/in-memory-stores.ts";
import { FakeIdentityProvider } from "../testing/fakes.ts";

let idp: FakeIdentityProvider;
let sessions: InMemorySessionStore;
beforeEach(async () => {
  idp = new FakeIdentityProvider();
  sessions = new InMemorySessionStore();
  await sessions.put("s1", { idToken: "the-id-token", accessToken: "a", refreshToken: "r", accessExpiresAt: 1 });
});

test("SO-1: the session is forgotten and the answer is Keycloak's address with the ID token as a hint (Verifies AC-2)", async () => {
  const { redirectTo } = await signOut({ idp, sessions }, "s1");
  assert.equal(redirectTo, "https://kc.test/logout?hint=the-id-token");
  assert.equal(await sessions.get("s1"), null);
});

test("signing out twice is harmless: the second time the person goes home and Keycloak is not asked", async () => {
  await signOut({ idp, sessions }, "s1");
  idp.endSessionCalls = 0;
  const again = await signOut({ idp, sessions }, "s1");
  assert.equal(again.redirectTo, null);
  assert.equal(idp.endSessionCalls, 0);
});

test("signing out with no cookie goes home and Keycloak is not asked", async () => {
  const { redirectTo } = await signOut({ idp, sessions }, undefined);
  assert.equal(redirectTo, null);
  assert.equal(idp.endSessionCalls, 0);
});

test("a session id nobody holds gets the same answer as no cookie", async () => {
  const { redirectTo } = await signOut({ idp, sessions }, "not-a-session");
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
  const { redirectTo } = await signOut({ idp, sessions: broken }, "s1");
  assert.equal(redirectTo, null);
});

test("if Keycloak cannot be reached our session is still gone and the answer is to go home", async () => {
  idp.endSessionFails = true;
  const { redirectTo } = await signOut({ idp, sessions }, "s1");
  assert.equal(redirectTo, null);
  assert.equal(await sessions.get("s1"), null);
});
