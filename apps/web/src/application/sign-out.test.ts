// Verifies UC-A2 (AC-2): signing out forgets our session and points at Keycloak's end session address.
// SO-1 is AC-2. SO-2 is proposed.
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

test("SO-2: signing out twice is harmless", async () => {
  await signOut({ idp, sessions }, "s1");
  const again = await signOut({ idp, sessions }, "s1");
  assert.equal(again.redirectTo, "https://kc.test/logout?hint=");
});

test("signing out with no cookie still works", async () => {
  const { redirectTo } = await signOut({ idp, sessions }, undefined);
  assert.equal(redirectTo, "https://kc.test/logout?hint=");
});

test("if Keycloak cannot be reached our session is still gone and the answer is to go home", async () => {
  idp.endSessionFails = true;
  const { redirectTo } = await signOut({ idp, sessions }, "s1");
  assert.equal(redirectTo, null);
  assert.equal(await sessions.get("s1"), null);
});
