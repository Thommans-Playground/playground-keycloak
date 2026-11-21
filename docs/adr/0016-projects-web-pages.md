# 0016 The Projects web pages: routes, the proxy, pure messages and tests

- Status: accepted
- Date: 2026-11-20
- Decided by: the agent (technical), after decisions 13, 14 and 23 (owner)

## Context
UC-P1, UC-P2 and UC-P3 give the API its routes. The web side must show them: a list of projects, one project with its members, and a form to create one. The existing pages show the pattern (a server page, a small client component for actions, the BFF proxy for the browser, ADR 0001). The web must show people by name, but the project answers carry member ids only, and the owner decided that the Projects pages use the same look as the existing pages (SGDS design tokens, the current shadcn and Base UI components, no new UI dependency).

## Decision
- **Routes.** `/projects` (the list), `/projects/new` (the create form, administrators only) and `/projects/[id]` (one project, its members, and add and remove for administrators). All are under `app/(app)/`, so the cookie gate of `proxy.ts` and the account check apply as for the other pages.
- **Server components read, client components act.** A page fetches through `api()` of `lib/api.ts` (server side, GET only, as today) and stays thin. A client component exists only for an action (the create form, add a member, remove a member). It calls the BFF proxy `/api/backend/...` with the cookie, shows the refusal as a message and refreshes the page with `router.refresh()`. The browser never sees a token. Client components follow `accounts-table.tsx` (a dialog, the `render` prop of Base UI and not `asChild`).
- **The proxy allows DELETE.** `app/api/backend/[...path]/route.ts` exports `GET`, `POST` and now `DELETE`, because removing a member is `DELETE /projects/{id}/members/{account_id}`. `PUT` and `PATCH` are NOT added: no use case needs them, and each method the proxy forwards is a method a browser script could send. DELETE has no body, like GET. `callBackend` and `FetchBackendApi` already pass the method through, so nothing else changes.
- **The API answers members with names (an agent decision, not the owner's).** The project answers (create, list, open, add a member, remove a member) return `members` as a list of `{id, name}`. The name comes through the existing `People` port, answered by Access in `composition/` (ADR 0015), at the moment of the read. An id that People does not know keeps its id and has `name: null`; the web then shows the id. Why: the web must show names, and one extra call from the browser for each member would cost more and leak more than one lookup in the API. The request bodies are unchanged (they still take ids). This changes the answer shape, so UC-P1, UC-P2 and UC-P3 say so. It is not an owner decision, so it has no number in `decisions.md`.
- **The member picker.** The add member form lists accounts from `GET /accounts?status=active` (administrators only, so only an administrator's page asks for it) and removes the people who are already members of the project (a pure function, `memberCandidates`). The create form uses the same list for the first members, at most 50. The server still refuses a bad choice (not active: `member_not_eligible`), so the picker is a convenience and not a check.
- **A pure function layer in `apps/web/src/domain/`**, each with a `node --test` file:
  - `project-messages.ts`: `projectMessage(code)` turns an API refusal code into a sentence for a person: `forbidden` (you may not do this), `member_not_eligible` (that person cannot be a member: they need an active account, or are not a member), `invalid_project_name` (the name must have 1 to 100 characters), `invalid_request` (the request was not valid), `project_not_found` (this project is not available), and a default for any other code. It never repeats text from the API.
  - `member-candidates.ts`: `memberCandidates(accounts, members)` keeps the active accounts that are not members, sorted by name.
  - `project-summary.ts`: `projectSummary(project)` gives the line shown on the list ("3 members", "1 member", "No members yet") and `memberLabel(member)` gives the name, or the id when the name is null.
- **Not found reads the same.** A project that is hidden from the person and one that does not exist both show the same `not-found` page (`notFound()` of Next on a 404 from the API), with no hint which it is. The API already answers both the same (AC-27); the page must not break that.
- **Navigation.** `app-nav.tsx` gets a "Projects" item for every signed in, active person (not administrator only). Pending and deactivated people never reach the nav (the layout redirects them, as today).
- **Empty states.** The list says there are no projects (and, for an administrator, offers "Create a project"); a project with no members says so. An empty list is not an error (AC-86).
- **No paging in the alpha** (decision 23): the pages show everything the API returns.
- **Placeholders.** `files`, `endpoints` and `evaluations` are in the API answer but are NOT shown yet: no requirement stands behind them.
- **Look.** The same approach as the existing pages: Card, Table, Dialog, Button and Input from `components/ui`, with the SGDS tokens in `src/styles/sgds`. No new UI dependency. Dummy data for looking at the pages comes from a dev only seed script, which is not part of this ADR.
- **Tests the web slices must have.**
  - Unit tests for the pure functions, each title ending in `(Verifies AC-n)` for the criterion it serves (ADR 0005): the messages (AC-11, AC-13, AC-18, AC-60, AC-87, AC-27), the candidates (AC-18, AC-17) and the summary (AC-28, AC-86).
  - Stack acceptance tests in `src/acceptance/projects.it.ts` (no browser; `fetch` with a cookie jar and throwaway Keycloak users, as `account-decisions.it.ts`, run with `INTEGRATION=1`). The page HTML of `/projects` lists a member's project and not another's (AC-55); shows the empty state for a person with no project (AC-86); a non member opening a project and a missing id show the same page (AC-27); an administrator sees the create form and a member does not (AC-11, AC-32); adding and removing a member through the proxy works, and a refusal shows its message (AC-17, AC-20, AC-18, AC-87, AC-60); and `DELETE` through the proxy reaches the API, while `PUT` and `PATCH` do not (they answer 405).
  - The existing architecture test for the web side still holds: pages call `api()` and the proxy, never an adapter.

## Consequences
The browser can now send DELETE through the proxy, and the proxy forwards what the API refuses, so the API stays the one place that decides. The member answer is a little larger, and the web of a version before this change would break on `members` (the web and the API ship together). A person with a stale page can try to remove a person already removed and sees `member_not_eligible`: the message must make sense for both cases. Without paging, a large list is slow: revisit before the beta (decision 23). The messages are English only, as the rest of the web.

## Links
Decisions 5, 13, 14, 23; ADR 0001, 0005, 0010, 0013, 0015; UC-P1, UC-P2, UC-P3; AC-9 to AC-20, AC-26 to AC-28, AC-32, AC-55, AC-60, AC-84, AC-86, AC-87; bff-design.puml.

## Amendments (21 Nov 2026)
Added to match what was built. They correct names and one behaviour above and do not change the decision.

- The refusal function is `projectRefusalMessage(code)` in `project-messages.ts`, not `projectMessage`. Its default sentence is "Something went wrong. Try again."
- A member whose name is unknown (`name: null`) is shown as **"Unknown person"**, never the id, so an id is not shown to a reader (`memberLabel` in `project-summary.ts`). The text above that says the web then shows the id is replaced by this.
- The API's own refusal text for `member_not_eligible` is now neutral ("That person cannot be added to or removed from this project."), because the same code answers a removal of a person who is not a member. The web still never repeats API text.
