// The web server calls the API for the person, adding their access token. Verifies AC-33's other half:
// with no session there is no call at all.
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { makeAccessToken } from "./access-token.ts";
import { makeCallBackend } from "./call-backend.ts";
import { InMemorySessionStore } from "../adapters/in-memory-stores.ts";
import { FakeBackendApi, FakeIdentityProvider, FakeSecurityLog } from "../testing/fakes.ts";

const now = 1_000_000;
let backend: FakeBackendApi;
let idp: FakeIdentityProvider;
let sessions: InMemorySessionStore;
let callBackend: ReturnType<typeof makeCallBackend>;

beforeEach(async () => {
  backend = new FakeBackendApi();
  idp = new FakeIdentityProvider(() => now);
  sessions = new InMemorySessionStore();
  await sessions.put("s1", { idToken: "i", accessToken: "at-1", refreshToken: "r", accessExpiresAt: now + 120_000 });
  callBackend = makeCallBackend({
    accessTokenFor: makeAccessToken({ idp, sessions, now: () => now, log: new FakeSecurityLog() }),
    backend,
  });
});

test("with no session nothing is sent to the API", async () => {
  assert.deepEqual(await callBackend(undefined, { method: "GET", path: "me" }), { kind: "no_session" });
  assert.equal(backend.calls.length, 0);
});

test("the person's access token is added and the answer is passed back", async () => {
  backend.answer = { status: 200, body: '{"name":"Maya"}', contentType: "application/json" };
  const result = await callBackend("s1", { method: "GET", path: "me" });
  assert.deepEqual(result, { kind: "response", status: 200, body: '{"name":"Maya"}', contentType: "application/json" });
  assert.equal(backend.calls[0].accessToken, "at-1");
  assert.equal(backend.calls[0].req.path, "me");
});

test("an API refusal is passed back as it is", async () => {
  backend.answer = { status: 403, body: '{"detail":{"code":"account_pending"}}', contentType: "application/json" };
  const result = await callBackend("s1", { method: "GET", path: "accounts" });
  assert.equal(result.kind === "response" && result.status, 403);
});

test("an API that is down is reported as unreachable", async () => {
  backend.fail = true;
  assert.deepEqual(await callBackend("s1", { method: "GET", path: "me" }), { kind: "unreachable" });
});

test("a DELETE goes through with its method and no body (Verifies AC-20)", async () => {
  await callBackend("s1", { method: "DELETE", path: "projects/p1/members/a1" });
  assert.equal(backend.calls[0].req.method, "DELETE");
  assert.equal(backend.calls[0].req.path, "projects/p1/members/a1");
  assert.equal(backend.calls[0].req.body, undefined);
  assert.equal(backend.calls[0].accessToken, "at-1");
});
