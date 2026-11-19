// A contract for the two store ports. Any implementation (in memory today, Redis on ElastiCache later)
// registers the same tests by calling these functions with a factory that returns a fresh, empty store.
import assert from "node:assert/strict";
import { test } from "node:test";
import type { LoginAttemptStore, SessionStore } from "../application/ports.ts";
import type { LoginAttempt } from "../domain/login-attempt.ts";
import type { Session } from "../domain/session.ts";

const attempt = (n: number): LoginAttempt => ({
  state: `state-${n}`,
  nonce: `nonce-${n}`,
  pkceVerifier: `verifier-${n}`,
  returnTo: `/page-${n}`,
  startedAt: 1_000_000 + n,
});

const session = (n: number): Session => ({
  idToken: `id-${n}`,
  accessToken: `at-${n}`,
  refreshToken: `rt-${n}`,
  accessExpiresAt: 2_000_000 + n,
});

export function loginAttemptStoreContract(name: string, create: () => LoginAttemptStore) {
  test(`${name}: save then take returns the attempt`, async () => {
    const store = create();
    await store.save("a", attempt(1));
    assert.deepEqual(await store.take("a"), attempt(1));
  });

  test(`${name}: take removes the attempt, so a second take is null (Verifies AC-38, RULE-A7)`, async () => {
    const store = create();
    await store.save("a", attempt(1));
    assert.deepEqual(await store.take("a"), attempt(1));
    assert.equal(await store.take("a"), null);
  });

  test(`${name}: take of undefined or an unknown id is null`, async () => {
    const store = create();
    await store.save("a", attempt(1));
    assert.equal(await store.take(undefined), null);
    assert.equal(await store.take("unknown"), null);
    assert.deepEqual(await store.take("a"), attempt(1), "a failed take must not remove other attempts");
  });

  test(`${name}: attempts under two ids stay apart`, async () => {
    const store = create();
    await store.save("a", attempt(1));
    await store.save("b", attempt(2));
    assert.deepEqual(await store.take("b"), attempt(2));
    assert.deepEqual(await store.take("a"), attempt(1));
  });

  test(`${name}: saving again under the same id replaces the attempt`, async () => {
    const store = create();
    await store.save("a", attempt(1));
    await store.save("a", attempt(2));
    assert.deepEqual(await store.take("a"), attempt(2));
    assert.equal(await store.take("a"), null);
  });
}

export function sessionStoreContract(name: string, create: () => SessionStore) {
  test(`${name}: put then get returns the session and does not remove it`, async () => {
    const store = create();
    await store.put("s", session(1));
    assert.deepEqual(await store.get("s"), session(1));
    assert.deepEqual(await store.get("s"), session(1));
  });

  test(`${name}: take returns the session and removes it`, async () => {
    const store = create();
    await store.put("s", session(1));
    assert.deepEqual(await store.take("s"), session(1));
    assert.equal(await store.take("s"), null);
    assert.equal(await store.get("s"), null);
  });

  test(`${name}: get and take of undefined or an unknown id are null`, async () => {
    const store = create();
    await store.put("s", session(1));
    assert.equal(await store.get(undefined), null);
    assert.equal(await store.get("unknown"), null);
    assert.equal(await store.take(undefined), null);
    assert.equal(await store.take("unknown"), null);
    assert.deepEqual(await store.get("s"), session(1));
  });

  test(`${name}: a session without a refresh token is kept as it is`, async () => {
    const store = create();
    const s: Session = { ...session(1), refreshToken: undefined };
    await store.put("s", s);
    const got = await store.get("s");
    assert.equal(got?.refreshToken, undefined);
    assert.equal(got?.accessToken, s.accessToken);
  });

  test(`${name}: put again under the same id replaces the session`, async () => {
    const store = create();
    await store.put("s", session(1));
    await store.put("s", session(2));
    assert.deepEqual(await store.get("s"), session(2));
  });

  test(`${name}: two sessions stay apart`, async () => {
    const store = create();
    await store.put("s1", session(1));
    await store.put("s2", session(2));
    assert.deepEqual(await store.take("s1"), session(1));
    assert.deepEqual(await store.get("s2"), session(2));
  });
}
