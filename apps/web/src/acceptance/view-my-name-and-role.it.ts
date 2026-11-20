// UC-A5 view my name and role, through the running web app (INTEGRATION=1). Only throwaway accounts change state.
import assert from "node:assert/strict";
import { adminSignIn, backend, config, CookieJar, guardStack, http, itest, kcAdmin, signIn, throwaway, type ThrowawayUser } from "../testing/stack.ts";

guardStack();

const REASON = "Integration test: a decision with a reason.";

/** A throwaway person, signed in once (so the account exists) and approved by the administrator. */
async function approvedPerson() {
  const user = await throwaway();
  const { jar } = await signIn(user);
  const me = await backend(jar, "GET", "me");
  assert.equal(me.json.status, "pending");
  const admin = await adminSignIn();
  assert.equal((await backend(admin, "POST", `accounts/${me.json.id}/approve`)).status, 200);
  return { user, jar, admin, id: me.json.id as string };
}

async function dashboardOf(jar: CookieJar) {
  const res = await http(`${config.appUrl}/dashboard`, { jar });
  assert.equal(res.status, 200);
  return res.text();
}

/** The page as plain text. */
const stripTags = (s: string) => s.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ");
const fullName = (u: ThrowawayUser) => `${u.firstName} ${u.lastName}`;

itest("an approved person opens the dashboard and sees their name, the role user and their email (Verifies AC-8)", async () => {
  const p = await approvedPerson();
  const text = stripTags(await dashboardOf(p.jar));
  assert.match(text, new RegExp(`Hello, ${fullName(p.user)}`), "the greeting carries the name");
  assert.match(text, new RegExp(`Role\\s*user\\b`), "the role badge says user");
  assert.ok(text.includes(p.user.email), "the email row shows their email");
  assert.doesNotMatch(text, /Waiting for approval/);
});

itest("an administrator opens the dashboard and sees the role administrator (Verifies AC-8)", async () => {
  const p = await approvedPerson();
  const res = await backend(p.admin, "POST", `accounts/${p.id}/promote`, { reason: REASON });
  assert.equal(res.status, 200);
  assert.equal(res.json.role, "administrator");
  const text = stripTags(await dashboardOf(p.jar)); // the same session: the role is read on every request
  assert.match(text, new RegExp(`Hello, ${fullName(p.user)}`));
  assert.match(text, /Role\s*administrator\b/, "the role badge says administrator");
});

itest("the name shown follows Keycloak: after the name changes there, the next sign in shows the new name (Verifies AC-8)", async () => {
  const p = await approvedPerson();
  const newFirst = "Renamed";
  const put = await kcAdmin("PUT", `/users/${p.user.id}`, {
    username: p.user.email, email: p.user.email, firstName: newFirst, lastName: p.user.lastName,
  });
  assert.equal(put.status, 204, `Keycloak accepted the new name: ${put.status}`);
  // the name is copied from the token, and the open session still holds the old token: a new sign in carries the new name
  const fresh = await signIn(p.user);
  const text = stripTags(await dashboardOf(fresh.jar));
  assert.match(text, new RegExp(`Hello, ${newFirst} ${p.user.lastName}`), "the new name");
  assert.doesNotMatch(text, new RegExp(`Hello, ${p.user.firstName}`), "not the old one");
});
