# TSK-P1.8: the page `/projects/new` and its form

AC-9, AC-10, AC-11, AC-12, AC-13, AC-32 (the stack tests also name AC-10 and AC-91; cells marked *by hand only* or *proved elsewhere* below have no test in this task) · plan status: **draft, not reviewed** · matches the code at `7481263`

Ground rules, the layout and the commands are in the [chapter summary](summary.md). This task works in `apps/web/`, so run
the commands from there. The Next.js version has breaking changes: `apps/web/AGENTS.md` says to read
`node_modules/next/dist/docs/` before changing Next code (`proxy.ts` not `middleware.ts`; Base UI, so `render` not `asChild`).

This is the plan someone follows to build this task, written by working backwards from the code that exists: each block
marked `# file` is a copy of that file at the commit above. It was built as web slice W4 in commit `3ba329d`.

## 1. What we are building, and why

| AC | Given | Then | Why |
|---|---|---|---|
| AC-9 | an administrator and an active person | the form creates a project naming them as a first member | The API route exists (TSK-P1.3); a person has to be able to use it from a screen. Stack test: the form's request, then the list and the member's name. The form clicks are *by hand only*. |
| AC-10 | an administrator | the AC text: they create a project naming themselves as a first member and are a member | First members are optional, and an administrator may be one. The stack test sends the request with one member and with none. An administrator naming themselves is *proved elsewhere* (API, TSK-P1.3), not by a web test here. |
| AC-11 | a user who is not an administrator | the AC text: creating is refused. This task's UI behaviour from the use case: opening `/projects/new` sends them to `/projects`, and the list shows no Create link | The screen is a convenience; the API refuses anyway (TSK-P1.4). Stack tests: the redirect and the link. |
| AC-32 | a caller who may not create | the page is opened, or the proxy is called | the server decides. Stack test here: the redirect of a member. A non administrator posting through the proxy is *proved elsewhere* (API, TSK-P1.4). |
| AC-12 | a name empty, blank or over 100 characters | the form is submitted | the API answers 422 `invalid_project_name` (stack test) and `looksLikeAName` is unit tested. That the Create button stays off (the `disabled` wiring) and that the refusal reads as a sentence are *by hand only*: the sentence comes from `projectRefusalMessage` (TSK-P3.5) and no test here asserts it on the page. |
| AC-13 | a first member who is not active | the form is submitted | the API answers `member_not_eligible` (stack test). That the page shows one message for it is *by hand only*. The picker lists only active people, so this happens only with a stale page. |

## 2. The logic

1. **A thin server page, a client component only for the action** (ADR 0016). The page reads `/me` and the active accounts
   with `api()`; the form calls the BFF proxy `/api/backend/projects`, so the browser never holds a token.
2. **Redirects, in this order:** no session goes to sign in with `returnTo`; a person who is not active goes to the
   dashboard, which says why; an active person who is not an administrator goes to `/projects`. The API still refuses a
   non administrator (AC-11, AC-32).
3. **The picker is the same pure function as UC-P2.** `memberCandidates(accounts, [])` keeps the active accounts, sorted by
   name; with no members yet, the second argument is empty. At most 50 are checked: past that the unchecked boxes are disabled (AC-92 on the screen).
4. **Name hint.** `looksLikeAName` says whether the trimmed name has 1 to 100 characters. It only turns the button off; the server
   stays the judge of the rest (control characters, AC-91), so the function does not try to.
5. **A refusal is a sentence, and what was typed stays.** The form maps the API's code with `projectRefusalMessage`
   (never the API's own text, never the input). The state is kept in the component, so nothing typed is lost.
6. **Success opens the new project**, `/projects/[id]`; if the answer has no id, it goes back to the list.
7. **The list gets a Create project button for administrators only.** A `Button` rendered as a `Link` (Base UI `render`).

**Reused, not rebuilt** (TSK-P3.5, and the answer with names, D15): `src/domain/member-candidates.ts`
(`memberCandidates`), `src/domain/project-messages.ts` (`projectRefusalMessage`), the types `Account` and `getMe`/`api` in
`src/lib/api.ts`, and the proxy `src/app/api/backend/[...path]/route.ts`. Nothing in them changes in this task.

**Where it lives:** the one new rule, `looksLikeAName`, in `src/domain/` (pure, with a `node --test` file); the page in
`src/app/(app)/projects/new/page.tsx` (thin); the form in `src/components/create-project-form.tsx` (the only client code).

## 3. The plan

Five stages. The web test runner is `node --test`; the stack tests need the running stack.

### Stage 1: the name hint (AC-12)

**1a. Write the tests** in `src/domain/project-name.test.ts`, each title ending `(Verifies AC-12)`: 1 to 100 characters
after trimming looks fine; empty, blank (`"   \t "`) or 101 characters does not.

Run `node --test src/domain/project-name.test.ts`. **Expect** a failure, `ERR_MODULE_NOT_FOUND` for `project-name.ts`
(checked).

**1b. Write the function.** This is the final file:

```ts
// src/domain/project-name.ts
/** A client side hint only: the trimmed name has 1 to 100 characters. The server stays the judge of the rest. */
export function looksLikeAName(name: string): boolean {
  const length = name.trim().length;
  return length >= 1 && length <= 100;
}
```

**Expect** `tests 2, pass 2`, and the whole `npm test` going from 93 to 95 (checked).

### Stage 2: the stack tests for the page (AC-9, AC-10, AC-11, AC-12, AC-13, AC-32)

**2a. Write the tests** at the end of `src/acceptance/projects.it.ts`, under the heading "UC-P1: create a project", with a
helper `newPage(jar)` that fetches `/projects/new` and returns the status, the HTML and the `Location`. Each title ends `(Verifies AC-n)`:

- an administrator opens `/projects/new`: 200, the text "Create project", "Project name", an active person offered by name and by id as the value (AC-9)
- a member opening it gets a redirect to `/projects` (AC-11, AC-32)
- the list page has `href="/projects/new"` for an administrator and not for a member (AC-11)
- with the form's own request (`POST` through the proxy): the name is trimmed, the project lists, its member shows by name, and an empty member list is accepted (AC-9, AC-10)
- an empty, blank, 101 character and control character name each answer 422 `invalid_project_name`, and nothing is created (AC-12, AC-91)
- a pending person named as a first member answers `member_not_eligible`, and nothing is created (AC-13)

Run `INTEGRATION=1 npm run test:integration` against the stack (it creates throwaway people and projects). **Expect**
tests 1 to 3 (the page, the member's redirect, the list link) to fail, because the page and the button do not exist;
tests 4 to 6 already hold, because the API exists (inferred from the code). **Not run**: the stack (Keycloak,
API, web) is not up here. The commit reports six new tests, 19 in the file, passing on the rebuilt web container.

### Stage 3: the page (AC-9, AC-11, AC-32)

The page is what the first two tests ask for. It reads `/me` and the active accounts and renders the form; it needs the
form component from stage 4 to compile, so write stage 4 right after and run the checks once both exist.

```tsx
// src/app/(app)/projects/new/page.tsx
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

### Stage 4: the form (AC-9, AC-10, AC-12, AC-13)

Write `CreateProjectForm`. Its logic is in the three pure pieces above (`looksLikeAName`, `projectRefusalMessage`,
`memberCandidates`), each already tested. The component itself has **no unit test** and was not tried in a browser: the
stack tests prove the request it sends (they send the same body through the proxy), not the clicks.

```tsx
// src/components/create-project-form.tsx
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

With stages 3 and 4 in place run `npm run typecheck`, `npx eslint src/components "src/app/(app)/projects" src/domain` and
`npx prettier --check` on the new files. **Expect** all clean (checked at the build commit: typecheck, eslint and prettier pass).

### Stage 5: the Create project button on the list (AC-11)

In `src/app/(app)/projects/page.tsx` the list takes `isAdmin` once, shows the button only to an administrator, and passes
the same value to the table. This is the change this task makes (the rest of the page is UC-P3):

```tsx
// src/app/(app)/projects/page.tsx, the lines this task adds or changes
import Link from "next/link";
import { Button } from "@/components/ui/button";
  const isAdmin = me.data.role === "administrator";
      <CardHeader className="flex flex-row items-center justify-between">
        {isAdmin && <Button render={<Link href="/projects/new" />}>Create project</Button>}
        <ProjectsTable projects={projects.data} isAdmin={isAdmin} />
```

Every line above exists in that file at `7481263`; they are listed separately here, in file order, and are not a block that compiles on its own.

Then run `INTEGRATION=1 npm run test:integration` on the rebuilt stack. **Expect** the six new tests to pass (the
commit reports 19 in `projects.it.ts` passing); **not run** here, no stack.

## 4. Check it yourself

```
npm test                       # unit tests: 95 pass at the build commit (93 before this task); more now
npm run typecheck && npm run lint && npm run build
docker compose up -d --build   # at the repo root, then:
INTEGRATION=1 npm run test:integration    # the stack tests, 19 in projects.it.ts at the build commit
```

By hand, signed in as an administrator: open `/projects`, press Create project, type a name, tick people, press Create,
and you land on the new project. Type 101 characters or nothing and the button stays off. Open `/projects/new` as a member
and you are sent to `/projects`.

## 5. Where this leaves things

- Source: `src/app/(app)/projects/new/page.tsx`, `src/components/create-project-form.tsx`, `src/domain/project-name.ts`, `src/app/(app)/projects/page.tsx`
- Tests: `src/domain/project-name.test.ts` (unit), `src/acceptance/projects.it.ts` (stack)
- Reused: `src/domain/member-candidates.ts`, `src/domain/project-messages.ts` (TSK-P3.5), `src/lib/api.ts`
- ADR: 0016.
- Not covered: the form's behaviour in a browser (checked boxes, the 50 cap, the message on refusal, the redirect after a
  success). A component test or a browser test would close it.

## Where the real build differs

- The commit follows UC-P2 (`8539ba0`), not TSK-P1.7, in the history. The task needs nothing from UC-P2.
- One commit holds all five stages; the order here is made afterwards. Stage 1 and the checks of stage 4 were run at the
  build commit's parent, with that commit's files added; the stack tests of stages 2 and 5 were not.
- The stack tests also name AC-91 and AC-10, which the summary row does not list for this task.

## Review

Not reviewed. Write `Reviewed by <name> at <hash>` here when the plan has been read against the code.
