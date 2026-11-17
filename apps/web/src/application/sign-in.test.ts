// The sign in use cases, tested with a strict fake Keycloak and the in-memory stores.
// Labels SI-n are the sign in lesson's own. SI-1 and SI-2 are AC-78 in docs/requirements.
import assert from "node:assert/strict";
import { beforeEach, test } from "node:test";
import { finishLogin, isSignInFailed, SignInFailed, startLogin, type SignInDeps } from "./sign-in.ts";
import { InMemoryLoginAttemptStore, InMemorySessionStore } from "../adapters/in-memory-stores.ts";
import { FakeIdentityProvider } from "../testing/fakes.ts";

let now = 1_000_000;
let ids = 0;
let idp: FakeIdentityProvider;
let deps: SignInDeps;

beforeEach(() => {
  now = 1_000_000;
  ids = 0;
  idp = new FakeIdentityProvider(() => now);
  deps = { idp, attempts: new InMemoryLoginAttemptStore(), sessions: new InMemorySessionStore(), now: () => now, newId: () => `id-${++ids}` };
});

const callback = (code: string, state: string) => new URL(`http://app.test/auth/callback?code=${code}&state=${state}`);

test("SI-1: starting a login sends the person to Keycloak and remembers the attempt (Verifies AC-78)", async () => {
  const { attemptId, redirectTo } = await startLogin(deps, { returnTo: "/admin/accounts", register: false });
  assert.match(redirectTo, /^https:\/\/kc\.test\/auth\?state=state-1/);
  assert.equal(attemptId, "id-1");
});

test("a person who asked to register is sent to the registration form", async () => {
  await startLogin(deps, { returnTo: null, register: true });
  assert.deepEqual(idp.lastBegin, { register: true });
});

test("SI-2: finishing a login makes a session and returns to the page asked for (Verifies AC-78)", async () => {
  const { attemptId } = await startLogin(deps, { returnTo: "/admin/accounts", register: false });
  const { sessionId, returnTo } = await finishLogin(deps, attemptId, callback("code-1", "state-1"));
  assert.equal(returnTo, "/admin/accounts");
  const session = await deps.sessions.get(sessionId);
  assert.equal(session?.accessToken, "at-code-1");
});

test("SI-5: the result holds a session id and an address, never a token", async () => {
  const { attemptId } = await startLogin(deps, { returnTo: null, register: false });
  const result = await finishLogin(deps, attemptId, callback("code-1", "state-1"));
  assert.deepEqual(Object.keys(result).sort(), ["returnTo", "sessionId"]);
});

test("SI-3: an outside return address becomes the default", async () => {
  for (const bad of ["https://evil.example", "//evil.example", "/\\evil.example"]) {
    const { attemptId, redirectTo } = await startLogin(deps, { returnTo: bad, register: false });
    const state = new URL(redirectTo).searchParams.get("state")!;
    const { returnTo } = await finishLogin(deps, attemptId, callback(`c-${bad}`, state));
    assert.equal(returnTo, "/dashboard", bad);
  }
});

const fails = (code: string) => (e: unknown) => e instanceof SignInFailed && e.code === code;

test("SI-4: an unknown attempt fails", async () => {
  await assert.rejects(finishLogin(deps, "nope", callback("c", "state-1")), fails("login_expired"));
});

test("SI-4: a missing attempt cookie fails", async () => {
  await assert.rejects(finishLogin(deps, undefined, callback("c", "state-1")), fails("login_expired"));
});

test("SI-4: an attempt works once", async () => {
  const { attemptId } = await startLogin(deps, { returnTo: null, register: false });
  await finishLogin(deps, attemptId, callback("code-1", "state-1"));
  await assert.rejects(finishLogin(deps, attemptId, callback("code-2", "state-1")), fails("login_expired"));
});

test("SI-4: an attempt older than ten minutes fails", async () => {
  const { attemptId } = await startLogin(deps, { returnTo: null, register: false });
  now += 10 * 60 * 1000;
  await assert.rejects(finishLogin(deps, attemptId, callback("code-1", "state-1")), fails("login_expired"));
});

test("SI-4: a callback with the wrong state fails and makes no session", async () => {
  const { attemptId } = await startLogin(deps, { returnTo: null, register: false });
  await assert.rejects(finishLogin(deps, attemptId, callback("code-1", "someone-elses-state")), fails("login_failed"));
});

test("a code that was used before fails", async () => {
  const first = await startLogin(deps, { returnTo: null, register: false });
  await finishLogin(deps, first.attemptId, callback("code-1", "state-1"));
  const second = await startLogin(deps, { returnTo: null, register: false });
  await assert.rejects(finishLogin(deps, second.attemptId, callback("code-1", "state-2")), fails("login_failed"));
});

test("a callback Keycloak marked as an error fails as refused", async () => {
  const { attemptId } = await startLogin(deps, { returnTo: null, register: false });
  const url = new URL("http://app.test/auth/callback?error=access_denied&state=state-1");
  await assert.rejects(finishLogin(deps, attemptId, url), fails("login_refused"));
});

test("a sign in failure is recognised by what it says, even from another copy of the class", () => {
  // Next.js can bundle a route and the use cases separately, so `instanceof` cannot be trusted across them.
  const copy = Object.assign(new Error("login_expired"), { name: "SignInFailed", code: "login_expired" });
  assert.equal(isSignInFailed(copy), true);
  assert.equal(isSignInFailed(new SignInFailed("login_failed")), true);
  assert.equal(isSignInFailed(new Error("something else")), false);
  assert.equal(isSignInFailed("login_expired"), false);
});
