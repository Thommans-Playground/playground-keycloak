## 1. Keycloak is the identity provider (12 Nov 2026)

**Decided.** Playground does not write sign-in. **Keycloak** proves who a person is, through OpenID Connect. Sign in,
sign out, refreshing the session, the profile, sign up and single sign-on are Keycloak's, so they are not use cases of
ours. Playground keeps the things Keycloak cannot know: its own **account record** (pending, active or deactivated),
**project roles and membership**, **time-limited access**, the **audit trail** and every permission rule.

Two choices, made by the owner:
- **Accounts are managed from a Playground screen.** An administrator approves, deactivates (with a reason) or reinstates
  a person there. The backend calls Keycloak's admin API to enable or disable the person, and records the reason and
  the audit entry itself. FR-1 to FR-4 stay as requirements.
- **Account roles are Keycloak roles carried in the token.** Project roles and membership stay in our database. Code
  still checks a permission, never a role name. **Amended 16 Nov 2026:** the owner chose to keep account roles in
  Playground's own database, and not in Keycloak or the token. The token carries who the person is. Roles are managed
  from our application and are changed only with our rules and an audit entry.

The server checks the token on every request (signature, expiry, issuer) and then checks project membership (NFR-1).
Access gets one port, `IdentityProvider`, with a stub adapter (a fixed set of people) for the early slices and a
Keycloak adapter later.

**Why.** Passwords, sessions, refresh, multi-factor and single sign-on are a product of their own, and getting them
wrong is a security risk for a governance product. Keeping the reason and the audit entry for account changes in
Playground keeps the audit trail whole.

**Changes.** The context map (an outside system and a port), the vocabulary (Account, identity provider), the notes of
FR-1 to FR-5, FR-24 and NFR-1, the Access use case diagram, and the question about how a test signs in. The Access
context page `docs/domain/contexts/BC-ACCESS.md`, the three Access use cases (UC-A2, UC-A3, UC-A4), and the list of
retired use case ids in `docs/usecases/retired-ids.csv`.

**Still open.**
- How a new person arrives as pending: decided in decision 2.
- How acceptance tests sign in: a Keycloak container with an imported realm, or tokens signed with a test key.
- Where Keycloak runs, and its database (it can share the Postgres server). The realm configuration belongs in the repo.
- Whether the sign-in page is Keycloak's own login theme (one can be built from React parts) or something else.
- FR-24, single sign-on, is Release 2. It is now configuration, so the release may move.
- New requirements to write with vbench-req: identify the person from the token, and link a person to a Playground
  account on first sign in.
- UC-A1 and UC-A5 to UC-A9 were MK3's sign-in items. They are retired (see `docs/usecases/retired-ids.csv`) and never reused.

## 2. Pending accounts, membership and time-limited access (16 Nov 2026)

**Decided.** Three answers by the owner, which refine decision 1.
- **A new person arrives pending, and our API holds them.** The person registers in Keycloak and can sign in there.
  Playground creates a pending account the first time it sees them (FR-123). It refuses every request except one that
  shows the person's own status (FR-2), until an administrator approves. So **approving is a status change in
  Playground only** and Keycloak is not called. **Deactivating** disables the person in Keycloak and ends their
  sessions. **Reinstating** enables them again.
- **Projects owns membership.** A project holds its members and their project roles, so "never lower or remove the
  last project manager" is a rule of the Project itself. Access keeps the account and the account role, and asks
  Projects for a person's project role through a port. UC-A3 is retired, and the membership use case becomes UC-P4.
  Member and Project role move to Projects in the vocabulary.
- **Time-limited access stays open** (FR-20, FR-21, UC-A4): whether it starts at once or needs a project manager to
  agree, and for how long, is not decided.

**Why.** Keeping the pending state in our API needs no Keycloak extension, and the person sees a clear "waiting for
approval" page. Membership is an invariant of the project, so it belongs with the project. Time-limited access has
no text that settles it, and a guess here would be a security decision made by accident.

**Changes.** Six new requirements (FR-123 to FR-128) and twelve new criteria (AC-75 to AC-86). FR-2 and AC-3 are
reworded. FR-6, FR-7, FR-10, FR-11, FR-12 and FR-13 move to area P. The notes of FR-1, FR-3 and FR-4 are corrected.

**Still open.**
- The use cases are not yet reworked: UC-A2 (approval does not call Keycloak), UC-A3 to UC-P4, and sign in, sign out,
  SSO, sign up and profile as "provided by Keycloak".
- The Access context page, the context map and the vocabulary still describe membership in Access.
- Criteria for FR-6 to FR-19 (membership, visibility, administrator, auditor) are a second batch.
- What the request "show my own status" looks like in the API, since a pending person gets a token.
- The id letters in the requirements `area` column still collide with the use case area letters (P covers files, X and H
  have no context).


## 3. Projects and who may see inside them (16 Nov 2026)

**Decided.** A first cut of projects, by the owner.
- **A project holds files, endpoints and evaluations, and only its members see inside it.** Access follows
  membership and nothing else. A person who is not a member cannot tell whether a project exists.
- **Two project roles, names only for now:** project manager and engineer. They do the same things in a project,
  except that only a manager adds, changes or removes its members. The roles can be pushed apart later.
- **An administrator has high level access, not a god mode.** An administrator can create a project, by naming its
  manager, and can see every project's name and members. They do not join a project they create, cannot add
  themselves to one, and see no contents. Their one power over members is to add a project manager to a project
  that has no active manager, so that a project is never stuck.
- **A project manager can create a project and becomes its manager.** A person who manages at least one project
  may create more. A project always has a manager, so the last one cannot be removed or demoted.
- Only an **active** account can be added to a project. A member whose account is deactivated stays on the
  project and is refused at the account check.

**Why.** Membership is an invariant of the project, so Projects owns it (decision 2). Keeping administrators out
of the contents keeps the governance boundary real: the person who keeps accounts cannot read the work. The one
administrator power is the smallest that stops a project being locked.

**Changes.** New context BC-PROJECTS, objects OBJ-P1 and OBJ-P2, value set SET-8, rules RULE-P1 to RULE-P4,
requirements FR-129 to FR-143 and criteria AC-87 to AC-110, use cases UC-P1 and UC-P4. SET-6 and OBJ-A1 now
include the pending status that decision 2 introduced. BC-ACCESS no longer describes membership or the account
request queue.

**Still open.**
- Whether a project name must be unique, and within what.
- Whether a manager can name a second manager at creation.
- Whether removing a member needs a reason.
- Files, endpoints and evaluations are not ontology objects here yet.
- FR-5 still says account roles are member, administrator or auditor.
- UC-A4 (time-limited access) is still undecided.
- OBJ-A2, OBJ-A3, SET-7, RULE-A4 and RULE-A5 are linked from the Access pages but have no files here.

## 4. AWS is the target, and the code follows DDD, TDD and hexagonal (17 Nov 2026)

**Decided.** Two standing constraints, by the owner.
- **The final application always runs on AWS.** The organisation is AWS native. The playground may use open source
  engines locally, but each has an AWS equivalent, and the move is configuration, not a rewrite: PostgreSQL becomes
  Amazon RDS (or Aurora) for PostgreSQL, for Playground's own database and for Keycloak's. **Keycloak stays the identity
  provider and runs on ECS Fargate with RDS**, as in the prototype, so decision 1 is unchanged. Other pieces map as
  follows: the web session store (in memory today) to ElastiCache, secrets to Secrets Manager, project files to S3 and
  logs to CloudWatch.
- **The application, frontend and backend, follows domain driven design, test driven development and hexagonal
  architecture (ports and adapters).** The domain is pure rules. Everything outside it (database, Keycloak, session
  store, AWS services) sits behind a port with an adapter. A rule or a use case gets its failing test first.

**Why.** A prototype that uses an engine the target does not have hides problems until the move. SQLite hides
differences in types, locking and migrations, so the API's database is now PostgreSQL, the engine behind RDS. Ports
and adapters are what make the swap cheap: an adapter changes and the domain does not.

**Changes.** The API's database is PostgreSQL (`api-db` in Docker Compose). The API tests run on SQLite for speed, and on
PostgreSQL when `TEST_DATABASE_URL` is set. `CLAUDE.md` records both constraints. **Amended 18 Nov 2026:** the PostgreSQL run must use the separate `playground_test` database. An earlier run pointed at the app's own database dropped its tables, so the tests now refuse any database whose name does not end in `_test`.

**Still open.**
- Schema changes: the API creates its tables at start-up. On AWS they need migrations (for example Alembic), run as a
  deploy step.
- Whether Playground's database is RDS PostgreSQL or Aurora PostgreSQL.
- How the web side applies hexagonal: decided in decision 5.
- Keycloak on ECS needs a production setup (not `start-dev`), its own sizing, and a decision on high availability.

## 5. The frontend follows ports and adapters where they pay (18 Nov 2026)

**Decided.** This narrows decision 4 for the frontend, by the owner after discussion.
- **The frontend's server side (the BFF) follows ports and adapters, test first.** It has a pure `domain/`
  (`safeReturnTo`, when a login attempt expires, when a token needs a refresh), `application/` use cases (sign in,
  sign out, the access token with a one-at-a-time refresh, calling the API) and four ports: `IdentityProvider`,
  `LoginAttemptStore`, `SessionStore` and `BackendApi`. Keycloak, the in-memory stores and `fetch` are adapters,
  and `composition.ts` is the one place that picks them. The stores are asynchronous, so ElastiCache fits.
- **The UI stays thin.** Pages and components have no ports and no use cases of their own. They are tested with
  component or end to end tests when that earns its cost.
- **DDD stays in the API.** The rules that matter (roles, status, membership, who may do what) are in the API's
  domain. The frontend keeps only a few small rules of its own.
- **The API is organised by bounded context** (`app/access/`, later `app/projects/`). Its domain errors carry no
  HTTP status (the web layer maps them), its use cases take an injectable clock, and an architecture test fails if
  a domain, a port file or a use case imports an adapter or a framework, or if one context imports another.

**Why.** The BFF is a backend in disguise: it runs the sign-in flow, holds tokens and refreshes them, so it has
real failure modes that were only checked by hand. Ports let a strict fake Keycloak test them in milliseconds and
make the session store a one-file change for AWS. Putting ports around React components would add files and
indirection for no gain in testing or swapping.

**Changes.** API: `app/access/` package, `tests/test_architecture.py`, `tests/test_service.py` with in-memory
ports, HTTP statuses moved to `main.py`. Web: `domain/`, `application/`, `adapters/`, `composition.ts`, 36 tests
including `architecture.test.ts`, no new dependency (Node runs TypeScript directly). A real sign in, a page load,
an API call, a failed callback, sign out and a replayed cookie were checked end to end against Keycloak.

**Still open.**
- The in-memory refresh lock is per process. With more than one web server it needs a shared lock.
- Schema migrations for the API (for example Alembic) before the first AWS deploy.
- Where `app/projects/` gets account status from: a port answered by Access (see BC-PROJECTS).
- Tagging the web and API tests with the acceptance criteria they prove (`Verifies AC-n`), then the criteria that
  have no test yet.

## 6. The requirements are cut to a core and renumbered (18 Nov 2026)

**Decided.** By the owner. The requirements had sprawled to 43 requirements and 72 criteria, most of them added
in two days. They are cut to a **core of 17 requirements (13 functional, 4 non-functional) and 37 criteria**, and
renumbered from 1 so the numbers mean something.

**One-time exception to "ids are append only".** Nothing had been released, and the old numbers were full of gaps
and merged items. Ids are append only again from now on: the next are FR-14, NFR-5 and AC-38. Older decision texts and
the git history cite the old requirement numbers, and the lists below translate them.

**Settled with the cut**, after an independent review of the two project use cases (the eight decisions):
- An administrator cannot name themselves as a project's manager at creation, and a person who manages a project
  creates as a manager even if they are also an administrator (FR-7, FR-8).
- An administrator restoring a manager needs a reason, and cannot name an administrator or an inactive account
  (FR-11). A refused administrator attempt on a project's members is audited (FR-13).
- The last-manager rule counts active managers (FR-10).
- A non-member gets the same answer as for a project that does not exist, for every request, and a manager adding
  an account that cannot be added gets one answer whatever the reason (FR-12, FR-9).
- Deactivation removes nothing, including project memberships, so reinstating an account gives them back (FR-4).
- Adding someone who is already a member changes nothing, and changing or removing a non-member is refused (FR-9).
- A project name is 1 to 100 characters once spaces at both ends are removed, and need not be unique (FR-7).
- Every member can see the member list (FR-12).

**Requirements, old to new.**
- **FR-1** was FR-124
- **FR-2** was FR-125
- **FR-3** was FR-123, with FR-2 merged in
- **FR-4** was FR-1, with FR-3, FR-4, FR-147 merged in
- **FR-5** was FR-126
- **FR-6** was FR-24
- **FR-7** was FR-129, with FR-130, FR-132, FR-152 merged in
- **FR-8** was FR-131, with FR-136, FR-138, FR-141, FR-144 merged in
- **FR-9** was FR-133, with FR-134, FR-148, FR-149, FR-150 merged in
- **FR-10** was FR-135
- **FR-11** was FR-137, with FR-145, FR-146 merged in
- **FR-12** was FR-140, with FR-139, FR-142, FR-153 merged in
- **FR-13** was FR-143, with FR-151 merged in
- **NFR-1** was NFR-1, with FR-127 merged in
- **NFR-2** was NFR-2, with NFR-3 merged in
- **NFR-3** was NFR-4, with NFR-6 merged in
- **NFR-4** was NFR-5
- Retired with no survivor: FR-5, FR-128 (FR-5 is covered by the account ontology, FR-128 was stale).

**Criteria, old to new** (after a second cut the same day, to 37 criteria: one for what a person gets, the rule details live in the RULE files). AC-1 was AC-78; AC-2 was AC-79; AC-3 was AC-76, AC-77; AC-4 was AC-3, AC-75; AC-5 was AC-1; AC-6 was AC-4, AC-84; AC-7 was AC-7, AC-85; AC-8 was AC-80; AC-9 was AC-87; AC-10 was AC-88; AC-11 was AC-89; AC-12 was AC-90; AC-13 was AC-91, AC-92; AC-14 was AC-93; AC-15 was AC-101, AC-118; AC-16 was AC-107; AC-17 was AC-94; AC-18 was AC-95; AC-19 was AC-97; AC-20 was AC-98; AC-21 was AC-99, AC-125; AC-22 was AC-126; AC-23 was AC-102; AC-24 was AC-122; AC-25 was AC-103, AC-123, AC-124; AC-26 was AC-106; AC-27 was AC-108, AC-127; AC-28 was AC-137; AC-29 was AC-109; AC-30 was AC-131, AC-132; AC-31 was AC-133; AC-32 was AC-8, AC-9; AC-33 was AC-81; AC-34 was AC-111; AC-35 was AC-112, AC-113; AC-36 was AC-114, AC-115; AC-37 was AC-116.
- Dropped, no survivor (21): AC-2, AC-5, AC-6, AC-82, AC-83, AC-86, AC-96, AC-100, AC-104, AC-105, AC-110, AC-117, AC-119, AC-120, AC-121, AC-128, AC-129, AC-130, AC-134, AC-135, AC-136. Rule details moved to the RULE files and their unit tests, and the rest into the notes.

**Changes.** `docs/requirements/` rewritten. Use cases, the ontology and context files, the build spec, the study
lessons and the test comments that cite ids were remapped. Tests tagged `Verifies AC-n` kept their meaning. The
Access requirements are marked built.

**Still open.** The use case for listing and opening a project is not written, so FR-12 is only partly covered by UC-P2. The review hashes are still unstamped.

## 7. Use cases, ontology items and decisions are renumbered (18 Nov 2026)

**Decided.** By the owner: "clean up everything, including renumbering", for the same reasons as decision 6 (gaps,
reading fatigue). Ids are append only again from now on. The next are UC-A8, UC-P3, SET-4, RULE-A5 and decision 8.

**Use cases**, numbered in the order of the requirements they serve. Tasks follow (TSK-A10.1 is now TSK-A1.1).
- UC-A10 is now **UC-A1** (sign in), UC-A11 is **UC-A2** (sign out), UC-A12 is **UC-A3** (register and wait for
  approval), UC-A2 is **UC-A4** (approve, deactivate and reinstate), UC-A13 is **UC-A5** (view my name and role),
  UC-A14 is **UC-A6** (keep the session alive) and UC-A15 is **UC-A7** (company single sign-on).
- UC-P1 keeps its number (create a project). UC-P4 is now **UC-P2** (manage project members). **UC-P3** is kept for
  the use case that lists and opens a project, which is not written yet.
- "MK3 UC-A1" and the like are the earlier prototype's own ids and are unchanged.

**Ontology.** SET-5 is now **SET-1** (account roles), SET-6 is **SET-2** (account statuses), SET-8 is **SET-3**
(project roles) and RULE-A6 is **RULE-A4** (deactivation removes nothing). OBJ-A1, OBJ-P1, OBJ-P2, RULE-A1 to RULE-A3
and RULE-P1 to RULE-P4 keep their numbers.

**Decisions.** Decision 23 is now **1**, 24 is **2**, 25 is **3**, 26 is **4**, 27 is **5** and 28 is **6**. Their
texts above keep the use case, ontology and requirement ids of the time, and the lists here and in decision 6
translate them.

**Cleanup.** File names carry their ids and were renamed. BC-ACCESS was rewritten to describe only what exists, and
the account request queue, shares and evaluations of the earlier model were taken out of it and out of OBJ-A1, SET-1,
RULE-A4 and the build spec, so there are no links to files that do not exist.

**Still open.** UC-P3 is not written. UC-A6 serves no requirement yet. The review hashes are still unstamped.
