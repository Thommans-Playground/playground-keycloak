// UC-A1 sign in and sign out, through the running web app, Keycloak and the API (INTEGRATION=1). No browser.
import assert from "node:assert/strict";
import {
  adminSignIn, backend, config, CookieJar, hasLoginForm, http, itest, loginAtKeycloak, looksLikeJwt, openAtKeycloak, signIn, throwaway, guardStack,
} from "../testing/stack.ts";

guardStack();

const path = (location: string) => new URL(location, config.appUrl);

itest("a new person signs in and lands on /dashboard with a session cookie that holds no token (Verifies AC-1, AC-41)", async () => {
  const user = await throwaway();
  const s = await signIn(user);
  assert.equal(path(s.location).origin, config.appUrl);
  assert.equal(path(s.location).pathname, "/dashboard");
  const cookie = s.jar.cookie(config.appUrl, "playground_session");
  assert.ok(cookie, "a session cookie was set");
  assert.ok(cookie.httpOnly, "the cookie is HttpOnly");
  assert.ok(!looksLikeJwt(cookie.value), "the cookie is a session id, not a token");
  // The browser holds nothing else that is a token either.
  for (const name of ["playground_session", "playground_login"]) {
    const c = s.jar.cookie(config.appUrl, name);
    if (c) assert.ok(!looksLikeJwt(c.value), `${name} is not a JWT`);
  }
});

itest("a new person is one pending account, and everything but /me is refused (Verifies AC-3, AC-4)", async () => {
  const user = await throwaway();
  const { jar } = await signIn(user);
  const first = await backend(jar, "GET", "me");
  const second = await backend(jar, "GET", "me");
  assert.equal(first.status, 200);
  assert.equal(first.json.status, "pending");
  assert.equal(first.json.email, user.email);
  assert.equal(second.json.id, first.json.id, "the second request finds the same account");
  const admin = await adminSignIn();
  const list = await backend(admin, "GET", "accounts?status=pending");
  assert.equal(list.status, 200);
  assert.equal(list.json.filter((a: { email: string }) => a.email === user.email).length, 1, "exactly one account");
  const other = await backend(jar, "GET", "accounts");
  assert.equal(other.status, 403);
  assert.equal(other.code, "account_pending");
});

itest("a callback that was already used is refused (Verifies AC-38)", async () => {
  const user = await throwaway();
  const s = await signIn(user);
  // the same callback, with a fresh jar that still holds the used login cookie
  const jar = new CookieJar();
  jar.set(config.appUrl, "playground_login", s.loginCookie!);
  const again = await http(s.callbackUrl, { jar });
  assert.ok(again.status >= 300 && again.status < 400);
  assert.match(again.headers.get("location")!, /[?&]error=/);
  assert.equal(jar.cookie(config.appUrl, "playground_session"), undefined, "no session was made");
});

itest("a callback with no login cookie is refused and makes no session (Verifies AC-42)", async () => {
  const user = await throwaway();
  const jar = new CookieJar();
  const start = await http(`${config.appUrl}/auth/login`, { jar });
  const kc = await loginAtKeycloak(start.headers.get("location")!, jar, user);
  assert.equal(kc.kind, "callback");
  if (kc.kind !== "callback") return;
  const other = new CookieJar(); // another browser: it never started this sign in
  const res = await http(kc.url, { jar: other });
  assert.match(res.headers.get("location")!, /[?&]error=/);
  assert.equal(other.cookie(config.appUrl, "playground_session"), undefined);
});

for (const hostile of ["//evil.example", "https://evil.example", "https://evil.example/dashboard", "/\\evil.example"]) {
  itest(`a hostile returnTo ${hostile} ends on a page of ours (Verifies AC-40)`, async () => {
    const user = await throwaway();
    const s = await signIn(user, { returnTo: hostile });
    const u = path(s.location);
    assert.equal(u.origin, config.appUrl);
    assert.notEqual(u.hostname, "evil.example");
  });
}

itest("a safe returnTo is honoured", async () => {
  const user = await throwaway();
  const s = await signIn(user, { returnTo: "/dashboard" });
  assert.equal(path(s.location).pathname, "/dashboard");
});

itest("sign out ends the session, and the next sign in asks for a password (Verifies AC-2)", async () => {
  const user = await throwaway();
  const s = await signIn(user);
  const old = s.sessionCookie!;
  assert.equal((await backend(s.jar, "GET", "me")).status, 200);

  const out = await http(`${config.appUrl}/auth/logout`, { method: "POST", jar: s.jar });
  assert.equal(out.status, 303);
  const endSession = out.headers.get("location")!;
  assert.match(endSession, /\/protocol\/openid-connect\/logout/);
  assert.equal(s.jar.cookie(config.appUrl, "playground_session"), undefined, "the cookie is cleared");
  // let Keycloak end its own session, as the browser would
  const kcEnd = await http(endSession, { jar: s.jar });
  assert.ok(kcEnd.status < 500);

  // our side: the old cookie no longer works, and a signed-out jar is refused
  const stale = new CookieJar();
  stale.set(config.appUrl, "playground_session", old);
  const replay = await backend(stale, "GET", "me");
  assert.ok(replay.status === 401 || replay.status === 403, `refused, got ${replay.status}`);
  const none = await backend(s.jar, "GET", "me");
  assert.ok(none.status === 401 || none.status === 403, `refused, got ${none.status}`);

  // Keycloak side: starting again shows the login page, not a silent sign in
  const start = await http(`${config.appUrl}/auth/login`, { jar: s.jar });
  const page = await openAtKeycloak(start.headers.get("location")!, s.jar);
  assert.equal(page.kind, "form", "Keycloak asked for a password");
  if (page.kind === "form") assert.ok(hasLoginForm(page.html), "the login form is present");
});

itest("a request with no session is answered 401 (Verifies AC-33, the web half)", async () => {
  const res = await backend(new CookieJar(), "GET", "me");
  assert.equal(res.status, 401);
});
