// UC-A5 view my name and role, through the running web app (INTEGRATION=1). Only throwaway accounts change state.
import assert from "node:assert/strict";
import {
  adminSignIn,
  backend,
  config,
  CookieJar,
  guardStack,
  http,
  itest,
  kcAdmin,
  signIn,
  throwaway,
  type ThrowawayUser,
} from "../testing/stack.ts";

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

itest(
  "an approved person opens the dashboard and sees their name, the role user and their email (Verifies AC-8)",
  async () => {
    const p = await approvedPerson();
    const text = stripTags(await dashboardOf(p.jar));
    assert.match(text, new RegExp(`Hello, ${fullName(p.user)}`), "the greeting carries the name");
    assert.match(text, new RegExp(`Role\\s*user\\b`), "the role badge says user");
    assert.ok(text.includes(p.user.email), "the email row shows their email");
    assert.doesNotMatch(text, /Waiting for approval/);
  },
);

itest("an administrator opens the dashboard and sees the role administrator (Verifies AC-8)", async () => {
  const p = await approvedPerson();
  const res = await backend(p.admin, "POST", `accounts/${p.id}/promote`, { reason: REASON });
  assert.equal(res.status, 200);
  assert.equal(res.json.role, "administrator");
  const text = stripTags(await dashboardOf(p.jar)); // the same session: the role is read on every request
  assert.match(text, new RegExp(`Hello, ${fullName(p.user)}`));
  assert.match(text, /Role\s*administrator\b/, "the role badge says administrator");
});

itest(
  "the name shown follows Keycloak: after the name changes there, the next sign in shows the new name (Verifies AC-8)",
  async () => {
    const p = await approvedPerson();
    const newFirst = "Renamed";
    const put = await kcAdmin("PUT", `/users/${p.user.id}`, {
      username: p.user.email,
      email: p.user.email,
      firstName: newFirst,
      lastName: p.user.lastName,
    });
    assert.equal(put.status, 204, `Keycloak accepted the new name: ${put.status}`);
    // the name is copied from the token, and the open session still holds the old token: a new sign in carries the new name
    const fresh = await signIn(p.user);
    const text = stripTags(await dashboardOf(fresh.jar));
    assert.match(text, new RegExp(`Hello, ${newFirst} ${p.user.lastName}`), "the new name");
    assert.doesNotMatch(text, new RegExp(`Hello, ${p.user.firstName}`), "not the old one");
  },
);

const ACCOUNT_PAGE = `${config.issuer}/account`;
const anchorHrefs = (html: string) =>
  [...html.matchAll(/<a\b[^>]*\bhref="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi)].map((m) => ({
    href: m[1].replace(/&amp;/g, "&"),
    text: stripTags(m[2]).trim(),
  }));

itest(
  "the dashboard links to the person's Keycloak account page and offers no way to edit the name or email (Verifies AC-78)",
  async () => {
    const p = await approvedPerson();
    const html = await dashboardOf(p.jar);
    const link = anchorHrefs(html).find((a) => a.href === ACCOUNT_PAGE);
    assert.ok(link, `a link to ${ACCOUNT_PAGE}`);
    assert.match(link.text, /Change your name, email or password in Keycloak/);
    // the header's sign out button is a form of the layout; the dashboard itself (inside <main>) has none
    const main = html.match(/<main\b[\s\S]*<\/main>/i)?.[0];
    assert.ok(main, "the page has a main area");
    assert.doesNotMatch(main, /<form\b/i, "no form on the dashboard");
    assert.doesNotMatch(main, /<(input|textarea|select)\b/i, "no field on the dashboard");
    assert.doesNotMatch(
      html,
      /<(input|textarea)\b[^>]*\bname="(name|email|firstName|lastName|password)"/i,
      "no field that edits name, email or password anywhere on the page",
    );
    const forms = [...html.matchAll(/<form\b[^>]*\baction="([^"]*)"/gi)].map((m) => m[1]);
    assert.deepEqual(forms, ["/auth/logout"], "the only form is sign out");
  },
);

itest("the address the dashboard links to is served by Keycloak (Verifies AC-78)", async () => {
  const res = await http(ACCOUNT_PAGE);
  await res.body?.cancel();
  assert.ok(res.status === 200 || (res.status >= 300 && res.status < 400), `the account page answered ${res.status}`);
});
