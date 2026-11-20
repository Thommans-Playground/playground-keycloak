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

// ---------------------------------------------------------------- UC-P3 and UC-P2: one project page

async function projectPage(jar: CookieJar, id: string) {
  const res = await http(`${config.appUrl}/projects/${id}`, { jar });
  return { status: res.status, html: await res.text() };
}

/** The signed in person's name, as the API shows it. */
async function nameOf(jar: CookieJar) {
  return (await backend(jar, "GET", "me")).json.name as string;
}

itest("a member opens the project and sees the members by name (Verifies AC-26)", async () => {
  const admin = await adminSignIn();
  const a = await activePerson(admin);
  const name = unique("Seen");
  const id = await projectFor(admin, name, [a.id]);
  const page = await projectPage(a.jar, id);
  assert.equal(page.status, 200);
  assert.ok(page.html.includes(name), "the project name is shown");
  assert.ok(page.html.includes(await nameOf(a.jar)), "the member is shown by name");
  assert.ok(!page.html.includes(`>${a.id}<`), "not by id");
  assert.match(page.html, /href="\/projects"/, "a link back to the list");
});

itest("a hidden, a missing and a malformed project read exactly the same (Verifies AC-27, AC-84)", async () => {
  const admin = await adminSignIn();
  const a = await activePerson(admin);
  const b = await activePerson(admin);
  const hidden = await projectFor(admin, unique("Hidden"), [b.id]);
  const missing = await projectPage(a.jar, "00000000-0000-4000-8000-000000000000");
  const bad = await projectPage(a.jar, "not-an-id");
  const notMine = await projectPage(a.jar, hidden);
  assert.equal(notMine.status, 404);
  assert.match(notMine.html, /This project is not available\./);
  assert.ok(!notMine.html.includes("Hidden"), "no hint of the hidden project");
  // The framework's own payload (the __next_f scripts) echoes the address the person typed: that is their own input.
  const visible = (html: string) => html.replace(/<script>self\.__next_f[^]*?<\/script>/g, "");
  for (const other of [missing, bad]) {
    assert.equal(other.status, notMine.status);
    assert.equal(visible(other.html), visible(notMine.html));
  }
});

itest(
  "a member sees no add form and no Remove button, an administrator sees both (Verifies AC-60, AC-32)",
  async () => {
    const admin = await adminSignIn();
    const a = await activePerson(admin);
    const id = await projectFor(admin, unique("Controls"), [a.id]);
    const member = await projectPage(a.jar, id);
    assert.ok(!/Add member/.test(member.html), "no add form for a member");
    assert.ok(!/Remove/.test(member.html), "no Remove for a member");
    const adminPage = await projectPage(admin, id);
    assert.equal(adminPage.status, 200);
    assert.match(adminPage.html, /Add member/);
    assert.match(adminPage.html, /Remove/);
  },
);

itest(
  "an administrator adds a person, adding again changes nothing, the page lists them (Verifies AC-17, AC-88)",
  async () => {
    const admin = await adminSignIn();
    const a = await activePerson(admin);
    const id = await projectFor(admin, unique("Adds"), []);
    const first = await backend(admin, "POST", `projects/${id}/members`, { account_id: a.id });
    assert.equal(first.status, 200, first.text);
    assert.deepEqual(
      first.json.members.map((m: { id: string }) => m.id),
      [a.id],
    );
    const again = await backend(admin, "POST", `projects/${id}/members`, { account_id: a.id });
    assert.equal(again.status, 200, "adding a member again is not an error");
    assert.deepEqual(again.json.members, first.json.members);
    const page = await projectPage(admin, id);
    assert.ok(page.html.includes(await nameOf(a.jar)), "the page lists the new member");
  },
);

itest(
  "an administrator removes a member, and a person who is not one gets the refusal (Verifies AC-20, AC-87)",
  async () => {
    const admin = await adminSignIn();
    const a = await activePerson(admin);
    const id = await projectFor(admin, unique("Removes"), [a.id]);
    const removed = await backend(admin, "DELETE", `projects/${id}/members/${a.id}`);
    assert.equal(removed.status, 200, removed.text);
    assert.deepEqual(removed.json.members, []);
    const again = await backend(admin, "DELETE", `projects/${id}/members/${a.id}`);
    assert.ok(again.status >= 400 && again.status < 500, `refused, got ${again.status}`);
    assert.equal(again.code, "member_not_eligible");
  },
);

itest("PUT and PATCH through the proxy answer 405 (Verifies AC-32)", async () => {
  const admin = await adminSignIn();
  const id = await projectFor(admin, unique("Methods"), []);
  for (const method of ["PUT", "PATCH"]) {
    const res = await backend(admin, method, `projects/${id}/members`, { account_id: "x" });
    assert.equal(res.status, 405, method);
  }
});

itest("a person who cannot be a member (pending account) is refused (Verifies AC-18)", async () => {
  const admin = await adminSignIn();
  const { jar } = await signIn(await throwaway()); // never approved: pending
  const pendingId = (await backend(jar, "GET", "me")).json.id as string;
  const id = await projectFor(admin, unique("Eligible"), []);
  const res = await backend(admin, "POST", `projects/${id}/members`, { account_id: pendingId });
  assert.ok(res.status >= 400 && res.status < 500, `refused, got ${res.status}`);
  assert.equal(res.code, "member_not_eligible");
  const after = await backend(admin, "GET", `projects/${id}`);
  assert.deepEqual(after.json.members, []);
});
