// The Redis stores against a real Redis (INTEGRATION=1), through the same contract as the in-memory ones.
// REDIS_TEST_URL defaults to the redis service of the root docker-compose.yml (host port 6380).
import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { createClient } from "redis";
import { INTEGRATION } from "../testing/stack.ts";
import { RedisLoginAttemptStore, RedisSessionStore, type RedisLike } from "./redis-stores.ts";
import { loginAttemptStoreContract, sessionStoreContract } from "./store-contract.ts";

const url = process.env.REDIS_TEST_URL ?? "redis://localhost:6380";
const client = createClient({ url });
let prefix = 0;
// A fresh key prefix for each store, so tests never see each other's keys.
const fresh = () => `it:${process.pid}:${Date.now()}:${prefix++}:`;

before(async () => {
  if (INTEGRATION) await client.connect();
});
after(async () => {
  if (client.isOpen) await client.close();
});

if (INTEGRATION) {
  const redis = client as unknown as RedisLike;
  // The contract's attempts started at 1_000_000 ms after the epoch, so the clock stands just after that.
  loginAttemptStoreContract(
    "RedisLoginAttemptStore",
    () => new RedisLoginAttemptStore(redis, { prefix: fresh(), now: () => 1_000_100 }),
  );
  sessionStoreContract("RedisSessionStore", () => new RedisSessionStore(redis, { prefix: fresh() }));

  test("RedisLoginAttemptStore: the key expires by itself after the attempt's remaining life", async () => {
    const p = fresh();
    const now = Date.now();
    const store = new RedisLoginAttemptStore(redis, { prefix: p, now: () => now });
    await store.save("a", { state: "s", nonce: "n", pkceVerifier: "v", returnTo: "/", startedAt: now - 60_000 });
    const ttl = await client.pTTL(`${p}a`);
    assert.ok(ttl > 0 && ttl <= 9 * 60_000 + 1000, `ttl ${ttl}`);
  });

  test("RedisLoginAttemptStore: an attempt already past its life is not stored", async () => {
    const p = fresh();
    const now = Date.now();
    const store = new RedisLoginAttemptStore(redis, { prefix: p, now: () => now });
    await store.save("a", { state: "s", nonce: "n", pkceVerifier: "v", returnTo: "/", startedAt: now - 11 * 60_000 });
    assert.equal(await store.take("a"), null);
  });

  test("RedisLoginAttemptStore: two takes at once give the attempt to only one", async () => {
    const store = new RedisLoginAttemptStore(redis, { prefix: fresh() });
    await store.save("a", { state: "s", nonce: "n", pkceVerifier: "v", returnTo: "/", startedAt: Date.now() });
    const got = await Promise.all([store.take("a"), store.take("a"), store.take("a")]);
    assert.equal(got.filter((x) => x !== null).length, 1);
  });

  test("RedisSessionStore: the key carries a TTL, so an abandoned session goes away", async () => {
    const p = fresh();
    const store = new RedisSessionStore(redis, { prefix: p, ttlSeconds: 120 });
    await store.put("s", { idToken: "i", accessToken: "a", refreshToken: "r", accessExpiresAt: 1 });
    const ttl = await client.ttl(`${p}s`);
    assert.ok(ttl > 0 && ttl <= 120, `ttl ${ttl}`);
  });
} else {
  test("redis stores: set INTEGRATION=1 to run against a real Redis", { skip: "set INTEGRATION=1" }, () => {});
}
