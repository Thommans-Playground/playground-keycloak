// UC-A3 and UC-A4 account decisions, driven by the administrator through the running web app (INTEGRATION=1).
// Only throwaway accounts change state. admin@ and maya@ are never touched.
import assert from "node:assert/strict";
import {
  adminSignIn, backend, hasLoginForm, itest, keycloakUser, loginAtKeycloak, signIn, throwaway, guardStack, config, CookieJar, http,
  type ThrowawayUser,
} from "../testing/stack.ts";

guardStack();

const REASON = "Integration test: a decision with a reason.";

async function pendingPerson() {
  const user = await throwaway();
  const { jar } = await signIn(user);
  const me = await backend(jar, "GET", "me");
  assert.equal(me.json.status, "pending");
  return { user, jar, id: me.json.id as string };
}

async function activePerson() {
  const p = await pendingPerson();
  const admin = await adminSignIn();
  const ok = await backend(admin, "POST", `accounts/${p.id}/approve`);
  assert.equal(ok.status, 200);
  return { ...p, admin };
}

itest("an administrator approves a pending account: the next request is active, with no change in Keycloak", async () => {
  const p = await pendingPerson();
  const admin = await adminSignIn();
  const before = await backend(p.jar, "GET", "accounts");
  assert.equal(before.status, 403);
  const kcBefore = await keycloakUser(p.user.id);
  const res = await backend(admin, "POST", `accounts/${p.id}/approve`);
  assert.equal(res.status, 200);
  assert.equal(res.json.status, "active");
  const me = await backend(p.jar, "GET", "me"); // the same session, no new sign in
  assert.equal(me.status, 200);
  assert.equal(me.json.status, "active");
  assert.deepEqual(await keycloakUser(p.user.id), kcBefore, "Keycloak was not changed");
});

itest("after approval the same person's next dashboard shows their own page, not 'Waiting for approval' (Verifies AC-5)", async () => {
  const p = await pendingPerson();
  const before = await http(`${config.appUrl}/dashboard`, { jar: p.jar });
  assert.equal(before.status, 200);
  assert.match(await before.text(), /Waiting for approval/);

  const admin = await adminSignIn();
  assert.equal((await backend(admin, "POST", `accounts/${p.id}/approve`)).status, 200);

  // the SAME session jar, no new sign in
  const after = await http(`${config.appUrl}/dashboard`, { jar: p.jar });
  assert.equal(after.status, 200);
  const html = await after.text();
  assert.doesNotMatch(html, /Waiting for approval/);
  assert.match(html, /Hello, /, "their own page");
  const me = await backend(p.jar, "GET", "me");
  assert.equal(me.json.status, "active");
});

itest("a user who is not an administrator is refused every decision and the account stays as it was (Verifies AC-63)", async () => {
  const target = await pendingPerson();
  const pendingActor = await pendingPerson();
  const activeActor = await activePerson();
  for (const actor of [pendingActor, activeActor]) {
    for (const action of ["approve", "deactivate", "reinstate", "promote", "demote"]) {
      const res = await backend(actor.jar, "POST", `accounts/${target.id}/${action}`, { reason: REASON });
      assert.equal(res.status, 403, `${action} by a non administrator`);
    }
  }
  const me = await backend(target.jar, "GET", "me");
  assert.equal(me.json.status, "pending");
  assert.equal(me.json.role, "user");
  // and the administrator sees the same: the target is as it was
  const admin = await adminSignIn();
  const list = await backend(admin, "GET", "accounts");
  const shown = list.json.find((a: { id: string }) => a.id === target.id);
  assert.deepEqual([shown.status, shown.role], ["pending", "user"]);
});

itest("deactivate: no reason is refused; with a reason the person is refused at once and cannot sign in (Verifies AC-6) (Verifies AC-64)", async () => {
  const p = await activePerson();
  for (const body of [undefined, {}, { reason: "" }, { reason: "   " }]) {
    const res = await backend(p.admin, "POST", `accounts/${p.id}/deactivate`, body);
    assert.equal(res.status, 422, `no reason: ${JSON.stringify(body)}`);
  }
  assert.equal((await backend(p.jar, "GET", "me")).json.status, "active", "still active");
  assert.equal((await keycloakUser(p.user.id)).enabled, true, "Keycloak untouched");

  const res = await backend(p.admin, "POST", `accounts/${p.id}/deactivate`, { reason: REASON });
  assert.equal(res.status, 200);
  assert.equal(res.json.status, "deactivated");

  const me = await backend(p.jar, "GET", "me"); // the session that was open
  assert.equal(me.status, 403);
  assert.equal(me.code, "account_deactivated");
  assert.equal((await keycloakUser(p.user.id)).enabled, false, "Keycloak disabled the person");

  const again = await signInAttempt(p.user);
  assert.equal(again.kind, "form");
  if (again.kind === "form") {
    assert.ok(hasLoginForm(again.html), "the login form comes back");
    assert.match(again.html, /kc-feedback-text|alert-error|disabled|Invalid/i, "with an error");
  }
});

itest("a deactivated person with a still valid session opens the dashboard: refused, and the page says so (Verifies AC-67)", async () => {
  const p = await activePerson();
  assert.equal((await backend(p.admin, "POST", `accounts/${p.id}/deactivate`, { reason: REASON })).status, 200);
  // the session cookie in p.jar is untouched: the person still holds it
  const page = await http(`${config.appUrl}/dashboard`, { jar: p.jar });
  assert.equal(page.status, 200);
  assert.match(await page.text(), /Your account is deactivated/);
  const me = await backend(p.jar, "GET", "me");
  assert.equal(me.status, 403);
  assert.equal(me.code, "account_deactivated");
});

itest("reinstate: no reason is refused; with a reason the person can use the product again (Verifies AC-57) (Verifies AC-7)", async () => {
  const p = await activePerson();
  assert.equal((await backend(p.admin, "POST", `accounts/${p.id}/deactivate`, { reason: REASON })).status, 200);

  for (const body of [undefined, { reason: "" }]) {
    const res = await backend(p.admin, "POST", `accounts/${p.id}/reinstate`, body);
    assert.equal(res.status, 422);
  }
  assert.equal((await backend(p.jar, "GET", "me")).code, "account_deactivated", "still deactivated");
  assert.equal((await keycloakUser(p.user.id)).enabled, false);

  const res = await backend(p.admin, "POST", `accounts/${p.id}/reinstate`, { reason: REASON });
  assert.equal(res.status, 200);
  assert.equal(res.json.status, "active");
  assert.equal((await keycloakUser(p.user.id)).enabled, true, "enabled in Keycloak again");

  const fresh = await signIn(p.user);
  assert.equal(new URL(fresh.location).pathname, "/dashboard");
  const me = await backend(fresh.jar, "GET", "me");
  assert.equal(me.status, 200);
  assert.equal(me.json.status, "active");
  assert.equal(me.json.id, p.id, "the same account, with its history");
});

/** A new browser tries to sign in. */
async function signInAttempt(user: ThrowawayUser) {
  const jar = new CookieJar();
  const start = await http(`${config.appUrl}/auth/login`, { jar });
  return loginAtKeycloak(start.headers.get("location")!, jar, user);
}
