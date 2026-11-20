// UC-P3 the Projects list page, read through the running web app (INTEGRATION=1).
// Throwaway people and projects only. admin@ is used to create projects and never changed.
import assert from "node:assert/strict";
import {
  adminSignIn,
  backend,
  config,
  CookieJar,
  guardStack,
  http,
  itest,
  signIn,
  throwaway,
} from "../testing/stack.ts";

guardStack();

/** An active person: signs in (pending), then an administrator approves them. */
async function activePerson(admin: CookieJar) {
  const user = await throwaway();
  const { jar } = await signIn(user);
  const me = await backend(jar, "GET", "me");
  assert.equal((await backend(admin, "POST", `accounts/${me.json.id}/approve`)).status, 200);
  return { jar, id: me.json.id as string };
}

async function projectFor(admin: CookieJar, name: string, members: string[]) {
  const res = await backend(admin, "POST", "projects", { name, members });
  assert.equal(res.status, 201, `create ${name}: ${res.text}`);
  return res.json.id as string;
}

const unique = (word: string) => `${word}${Date.now().toString(36)}${Math.floor(Math.random() * 1e6).toString(36)}`;

async function projectsPage(jar: CookieJar) {
  const res = await http(`${config.appUrl}/projects`, { jar });
  return { status: res.status, html: await res.text() };
}

itest("a member's /projects page lists their project and not another one (Verifies AC-55)", async () => {
  const admin = await adminSignIn();
  const a = await activePerson(admin);
  const b = await activePerson(admin);
  const mine = unique("Mine");
  const theirs = unique("Theirs");
  const mineId = await projectFor(admin, mine, [a.id]);
  await projectFor(admin, theirs, [b.id]);

  const page = await projectsPage(a.jar);
  assert.equal(page.status, 200);
  assert.ok(page.html.includes(mine), "their project is listed");
  assert.ok(page.html.includes(`href="/projects/${mineId}"`), "and links to it");
  assert.ok(!page.html.includes(theirs), "another person's project is not listed");
  assert.match(page.html, /1 member/);
});

itest("a person with no project sees the empty state, not an error (Verifies AC-86)", async () => {
  const admin = await adminSignIn();
  await projectFor(admin, unique("Elsewhere"), []);
  const p = await activePerson(admin);
  const page = await projectsPage(p.jar);
  assert.equal(page.status, 200);
  assert.match(page.html, /You are not in any project yet/);
});

itest("an administrator's page lists every project (Verifies AC-28)", async () => {
  const admin = await adminSignIn();
  const a = await activePerson(admin);
  const one = unique("AdminOne");
  const two = unique("AdminTwo");
  await projectFor(admin, one, [a.id]);
  await projectFor(admin, two, []);
  const page = await projectsPage(admin);
  assert.equal(page.status, 200);
  assert.ok(page.html.includes(one) && page.html.includes(two), "both projects are listed");
  assert.match(page.html, /No members yet/);
});

itest("a person without a session is sent to sign in (Verifies AC-94)", async () => {
  const res = await http(`${config.appUrl}/projects`, { jar: new CookieJar() });
  assert.ok(res.status >= 300 && res.status < 400, `redirected, got ${res.status}`);
  assert.match(res.headers.get("location") ?? "", /\/auth\/login|\/login/);
});

itest("a pending person is sent to the dashboard, which waits for approval (Verifies AC-94)", async () => {
  const { jar } = await signIn(await throwaway());
  const res = await http(`${config.appUrl}/projects`, { jar });
  assert.ok(res.status >= 300 && res.status < 400, `redirected, got ${res.status}`);
  assert.match(res.headers.get("location") ?? "", /\/dashboard$/);
});

itest("the navigation of the dashboard has a Projects item (Verifies AC-55)", async () => {
  const admin = await adminSignIn();
  const p = await activePerson(admin);
  const res = await http(`${config.appUrl}/dashboard`, { jar: p.jar });
  const html = await res.text();
  assert.match(html, /<a[^>]*href="\/projects"[^>]*>(?:(?!<\/a>)[^])*Projects/);
});
