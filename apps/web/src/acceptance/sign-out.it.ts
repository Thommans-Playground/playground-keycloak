// UC-A2 sign out, through the running web app and Keycloak (INTEGRATION=1). No browser.
import assert from "node:assert/strict";
import { backend, config, http, itest, looksLikeJwt, openAtKeycloak, signIn, throwaway, guardStack, CookieJar } from "../testing/stack.ts";

guardStack();

const home = `${config.appUrl}/`;

itest("a GET to the sign out address does nothing, and the session still works (Verifies AC-71)", async () => {
  const user = await throwaway();
  const s = await signIn(user);
  const res = await http(`${config.appUrl}/auth/logout`, { method: "GET", jar: s.jar });
  assert.equal(res.status, 405, "only a POST signs out");
  assert.ok(!(res.headers.get("location") ?? "").includes("/protocol/openid-connect/logout"), "no redirect to Keycloak");
  assert.equal((await backend(s.jar, "GET", "me")).status, 200, "the session still works");
  assert.ok(s.jar.cookie(config.appUrl, "playground_session"), "the cookie is still there");
});

itest("sign out sends Keycloak the ID token hint and our home page, and ends on our home page (Verifies AC-72)", async () => {
  const user = await throwaway();
  const s = await signIn(user);
  const out = await http(`${config.appUrl}/auth/logout`, { method: "POST", jar: s.jar });
  assert.equal(out.status, 303);
  const endSession = new URL(out.headers.get("location")!);
  assert.match(endSession.pathname, /\/protocol\/openid-connect\/logout$/);
  // what the real adapter builds: the person's own ID token as the hint, and exactly our home page to return to
  assert.ok(looksLikeJwt(endSession.searchParams.get("id_token_hint") ?? ""), "the ID token is the hint");
  assert.equal(endSession.searchParams.get("post_logout_redirect_uri"), home);
  assert.equal(endSession.searchParams.get("client_id"), "playground-web");
  // Keycloak accepts it and sends the person back to our home page, not to an error page
  const kc = await http(endSession.href, { jar: s.jar });
  assert.ok(kc.status >= 300 && kc.status < 400, `Keycloak redirects, got ${kc.status}`);
  assert.equal(new URL(kc.headers.get("location")!, endSession.href).href, home);
  const page = await http(home, { jar: s.jar });
  assert.ok(page.status < 400 || (page.status >= 300 && page.status < 400), `our home page answers, got ${page.status}`);
});

itest("control: if Keycloak's session is NOT ended, the next sign in is silent (so the login form after sign out proves something)", async () => {
  const user = await throwaway();
  const s = await signIn(user);
  const start = await http(`${config.appUrl}/auth/login`, { jar: s.jar.clone() });
  const next = await openAtKeycloak(start.headers.get("location")!, s.jar.clone());
  assert.equal(next.kind, "callback", "Keycloak still remembers the person when nobody ended its session");
});

itest("signing out with no session goes home, and does not send the person to Keycloak", async () => {
  const res = await http(`${config.appUrl}/auth/logout`, { method: "POST", jar: new CookieJar() });
  assert.equal(res.status, 303);
  assert.equal(new URL(res.headers.get("location")!, config.appUrl).href, home);
  const cleared = res.headers.getSetCookie().find((c) => c.startsWith("playground_session="));
  assert.ok(cleared, "the cookie is cleared on this path too");
});
