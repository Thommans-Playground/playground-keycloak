# Task P1.8: The page `/projects/new` and its form

**Task ID:** TSK-P1.8 · **Use Case:** UC-P1 · **Criteria:** AC-9, AC-10, AC-11, AC-12, AC-13, AC-32 · **Code matched at:** `7481263`

What this does and why: [summary, task P1.8](summary.md#p18-the-page-projectsnew-and-its-form).

Run from `apps/web/`: `node --test src/domain/project-name.test.ts`

Work test first in each step: write the test, run it, see it fail, then write the code.

---

## Step 1: the name hint (AC-12)

**Test** (Unit):

Each title ends `(Verifies AC-12)`: 1 to 100 characters after trimming looks fine; empty, blank (`"   \t "`) or 101 characters does not.

```ts
// apps/web/src/domain/project-name.test.ts
import test from "node:test";
import assert from "node:assert/strict";
import { looksLikeAName } from "./project-name.ts";

test("a name of 1 to 100 characters after trimming looks fine (Verifies AC-12)", () => {
  assert.equal(looksLikeAName("Apollo"), true);
  assert.equal(looksLikeAName("  Apollo  "), true);
  assert.equal(looksLikeAName("a".repeat(100)), true);
});

test("an empty or blank name, or one over 100 characters, does not (Verifies AC-12)", () => {
  assert.equal(looksLikeAName(""), false);
  assert.equal(looksLikeAName("   \t "), false);
  assert.equal(looksLikeAName("a".repeat(101)), false);
});
```

**Code**:

```ts
// apps/web/src/domain/project-name.ts
/** A client side hint only: the trimmed name has 1 to 100 characters. The server stays the judge of the rest. */
export function looksLikeAName(name: string): boolean {
  const length = name.trim().length;
  return length >= 1 && length <= 100;
}
```

**Logic.** Trim, then count: 1 to 100 characters. It only turns the Create button off. The server stays the judge of the rest (control
characters, AC-91), so the function does not try to.

---

## Step 2: the stack tests for the page (AC-9, AC-10, AC-11, AC-12, AC-13, AC-32)

**Test** (Integration):

At the end of `src/acceptance/projects.it.ts`, under the heading "UC-P1: create a project", a helper `newPage(jar)` fetches
`/projects/new` and returns the status, the HTML and the `Location`. Each title ends `(Verifies AC-n)`.

```ts
// apps/web/src/acceptance/projects.it.ts
async function newPage(jar: CookieJar) {
  const res = await http(`${config.appUrl}/projects/new`, { jar });
  return { status: res.status, html: await res.text(), location: res.headers.get("location") ?? "" };
}
```

```ts
// apps/web/src/acceptance/projects.it.ts
itest("an administrator opens /projects/new and sees the form with the active people (Verifies AC-9)", async () => {
  const admin = await adminSignIn();
  const a = await activePerson(admin);
  const page = await newPage(admin);
  assert.equal(page.status, 200);
  assert.match(page.html, /Create project/);
  assert.match(page.html, /name="name"|aria-label="Project name"|Project name/);
  assert.ok(page.html.includes(await nameOf(a.jar)), "an active person is offered");
  assert.ok(page.html.includes(a.id), "by their id as the value");
});
```

```ts
// apps/web/src/acceptance/projects.it.ts
itest("a member opening /projects/new is sent to /projects (Verifies AC-11, AC-32)", async () => {
  const admin = await adminSignIn();
  const a = await activePerson(admin);
  const page = await newPage(a.jar);
  assert.ok(page.status >= 300 && page.status < 400, `redirected, got ${page.status}`);
  assert.match(page.location, /\/projects$/);
});
```

```ts
// apps/web/src/acceptance/projects.it.ts
itest("the list shows the Create project link to an administrator and not to a member (Verifies AC-11)", async () => {
  const admin = await adminSignIn();
  const a = await activePerson(admin);
  assert.match((await projectsPage(admin)).html, /href="\/projects\/new"/);
  assert.ok(!/href="\/projects\/new"/.test((await projectsPage(a.jar)).html), "no link for a member");
});
```

```ts
// apps/web/src/acceptance/projects.it.ts
itest(
  "an administrator creates a project with the form's request, and it lists with names (Verifies AC-9, AC-10)",
  async () => {
    const admin = await adminSignIn();
    const a = await activePerson(admin);
    const name = unique("Created");
    const res = await backend(admin, "POST", "projects", { name: `  ${name}  `, members: [a.id] });
    assert.equal(res.status, 201, res.text);
    assert.equal(res.json.name, name, "the name is trimmed");
    const page = await projectsPage(admin);
    assert.ok(page.html.includes(name), "the administrator's list shows it");
    const open = await projectPage(admin, res.json.id);
    assert.ok(open.html.includes(await nameOf(a.jar)), "its member is shown by name");
    const none = await backend(admin, "POST", "projects", { name: unique("Nobody"), members: [] });
    assert.equal(none.status, 201, "an administrator may name nobody");
  },
);
```

```ts
// apps/web/src/acceptance/projects.it.ts
itest("an invalid name, with a control character, is refused and creates nothing (Verifies AC-12, AC-91)", async () => {
  const admin = await adminSignIn();
  const before = (await backend(admin, "GET", "projects")).json.length;
  for (const name of ["", "   ", "a".repeat(101), `Bad\u0007${unique("Name")}`]) {
    const res = await backend(admin, "POST", "projects", { name, members: [] });
    assert.equal(res.status, 422, `refused: ${JSON.stringify(name)}`);
    assert.equal(res.code, "invalid_project_name");
  }
  assert.equal((await backend(admin, "GET", "projects")).json.length, before, "nothing was created");
});
```

```ts
// apps/web/src/acceptance/projects.it.ts
itest("a pending person named as a first member is refused and creates nothing (Verifies AC-13)", async () => {
  const admin = await adminSignIn();
  const { jar } = await signIn(await throwaway()); // never approved: pending
  const pendingId = (await backend(jar, "GET", "me")).json.id as string;
  const before = (await backend(admin, "GET", "projects")).json.length;
  const res = await backend(admin, "POST", "projects", { name: unique("Pending"), members: [pendingId] });
  assert.ok(res.status >= 400 && res.status < 500, `refused, got ${res.status}`);
  assert.equal(res.code, "member_not_eligible");
  assert.equal((await backend(admin, "GET", "projects")).json.length, before, "nothing was created");
});
```

**Code**:

```tsx
// apps/web/src/app/(app)/projects/new/page.tsx
import Link from "next/link";
import { redirect } from "next/navigation";
import { CreateProjectForm } from "@/components/create-project-form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { memberCandidates } from "@/domain/member-candidates";
import { api, getMe, type Account } from "@/lib/api";

export default async function NewProjectPage() {
  const back = "/auth/login?returnTo=/projects/new";
  const me = await getMe();
  if (!me.ok) redirect(me.status === 401 ? back : "/dashboard");
  if (me.data.status !== "active") redirect("/dashboard"); // the dashboard says why
  if (me.data.role !== "administrator") redirect("/projects"); // the server refuses anyway (AC-11)

  const accounts = await api<Account[]>("/accounts?status=active");
  if (!accounts.ok) redirect(accounts.status === 401 ? back : "/projects");

  return (
    <div className="space-y-4">
      <Link href="/projects" className="text-sm underline-offset-4 hover:underline">
        Back to projects
      </Link>
      <Card>
        <CardHeader>
          <CardTitle>Create project</CardTitle>
        </CardHeader>
        <CardContent>
          <CreateProjectForm choices={memberCandidates(accounts.data, []).map((a) => ({ id: a.id, name: a.name }))} />
        </CardContent>
      </Card>
    </div>
  );
}
```

```tsx
// apps/web/src/components/create-project-form.tsx
"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { looksLikeAName } from "@/domain/project-name";
import { projectRefusalMessage } from "@/domain/project-messages";

export function CreateProjectForm({ choices }: { choices: { id: string; name: string }[] }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [members, setMembers] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function toggle(id: string) {
    setMembers((current) => (current.includes(id) ? current.filter((m) => m !== id) : [...current, id]));
  }

  async function create() {
    setBusy(true);
    setError(null);
    const res = await fetch("/api/backend/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, members }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setBusy(false);
      setError(projectRefusalMessage(body?.code ?? body?.detail?.code ?? ""));
      return;
    }
    const created = await res.json().catch(() => null);
    if (typeof created?.id !== "string") {
      setBusy(false);
      router.push("/projects");
      router.refresh();
      return;
    }
    router.push(`/projects/${encodeURIComponent(created.id)}`);
    router.refresh();
  }

  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (!busy && looksLikeAName(name)) void create();
      }}
    >
      <div className="space-y-1">
        <label htmlFor="project-name" className="text-sm font-medium">
          Project name
        </label>
        <input
          id="project-name"
          name="name"
          maxLength={100}
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="h-8 w-full max-w-md rounded-lg border border-border bg-background px-2 text-sm"
        />
      </div>
      <fieldset className="space-y-2">
        <legend className="text-sm font-medium">First members (optional, at most 50)</legend>
        {choices.length === 0 ? (
          <p className="text-sm text-muted-foreground">No active people to add yet.</p>
        ) : (
          <ul className="max-h-64 space-y-1 overflow-y-auto">
            {choices.map((c) => (
              <li key={c.id}>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    name="members"
                    value={c.id}
                    checked={members.includes(c.id)}
                    disabled={!members.includes(c.id) && members.length >= 50}
                    onChange={() => toggle(c.id)}
                  />
                  {c.name}
                </label>
              </li>
            ))}
          </ul>
        )}
      </fieldset>
      <Button type="submit" disabled={busy || !looksLikeAName(name)}>
        Create
      </Button>
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </form>
  );
}
```

In `src/app/(app)/projects/page.tsx` the list takes `isAdmin` once, shows the button only to an administrator, and passes the
same value to the table. The page is shown whole; the lines this task adds or changes are the `Button` and `Link` imports, the
`isAdmin` line, the `flex flex-row items-center justify-between` header class, the button line and the `isAdmin` prop of the
table (the rest of the page is UC-P3):

```tsx
// apps/web/src/app/(app)/projects/page.tsx
import Link from "next/link";
import { redirect } from "next/navigation";
import { ProjectsTable } from "@/components/projects-table";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, getMe, type Project } from "@/lib/api";

export default async function ProjectsPage() {
  const me = await getMe();
  if (!me.ok) redirect(me.status === 401 ? "/auth/login?returnTo=/projects" : "/dashboard");
  if (me.data.status !== "active") redirect("/dashboard"); // the dashboard says why

  const projects = await api<Project[]>("/projects");
  if (!projects.ok) redirect(projects.status === 401 ? "/auth/login?returnTo=/projects" : "/dashboard");

  const isAdmin = me.data.role === "administrator";
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Projects</CardTitle>
        {isAdmin && <Button render={<Link href="/projects/new" />}>Create project</Button>}
      </CardHeader>
      <CardContent>
        <ProjectsTable projects={projects.data} isAdmin={isAdmin} />
      </CardContent>
    </Card>
  );
}
```

**Logic.** The page is what the first two stack tests ask for. It reads `/me` and the active accounts and renders the form. It needs the
form component from stage 4 to compile, so write stage 4 right after and run the checks once both exist.

The logic is in three pure pieces already tested (`looksLikeAName`, `projectRefusalMessage`, `memberCandidates`). The component
itself has no unit test and was not tried in a browser: the stack tests prove the request it sends (they send the same body
through the proxy), not the clicks.

The button is a `Button` rendered as a `Link` (Base UI `render`, not `asChild`). It is shown only to an administrator. A
member who opens `/projects/new` by hand is sent back to `/projects` by the page of stage 3.
