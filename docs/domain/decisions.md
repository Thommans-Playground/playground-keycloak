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

The server checks the token on every request (signature, expiry, issuer) and then checks project membership (NFR-1). **Amended 18 Nov 2026:** the check also requires the audience, so a token issued for another client is refused (decision 10). A token with a missing, expired, wrong issuer or wrong audience gets 401.
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

**Footnote (decision 13), to be implemented in the beta version.** For the alpha, project roles (manager and
engineer), "a project always has a manager", the administrator who never joins or sees inside a project, and the
administrator's one narrow power to restore a manager are **parked**: FR-8, FR-10, FR-11 and RULE-P1 to RULE-P3 are
kept, with release `parked`, and come back with role based access in the beta version. The alpha has two account
roles, and the administrator is a superuser.

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

## 8. The API decides, Keycloak authenticates, and deactivation disables both (18 Nov 2026)

**Decided.** By the owner, while challenging UC-A1 (sign in). It confirms decision 2 and settles the rest.
- **The API decides what a person may do, and Keycloak only proves who they are.** A pending person can sign in and
  holds a token, and the API refuses everything except their own status. Approval changes our account only and does not
  call Keycloak.
- **Deactivation disables the account in both places.** Playground sets the account to deactivated, and the backend
  disables the person in Keycloak and ends their sessions. Reinstating enables both again. The API still refuses a
  deactivated person on every request, so a token that has not yet expired, or a Keycloak that was changed by hand,
  cannot open the door.

**Why.** Two layers that agree keep a deactivated person out even when one of them is wrong (deny by default,
enforced on the server). Keeping pending in our API needs no Keycloak extension.

**Changes.** UC-A4 (step 5, effects, postconditions, TSK-A4.2) and the criteria AC-5, AC-6 and AC-7 now say this.

**Still open.**
- Which change comes first, and what happens when the Keycloak call fails: decided in decision 10.
- UC-A1 does not yet say what a deactivated person sees: Keycloak's own refusal page, or a refusal from our API for a
  person whose Keycloak account was re-enabled by hand. The criteria of UC-A1 (AC-1 is untestable as written), the
  audience check in decision 1, where the pending account is created, identity by `sub` and not by email, and
  replacing the old session on a second sign in are the other findings still to settle.

## 9. A use case has an analysis sequence diagram and a design sequence diagram (18 Nov 2026)

**Decided.** By the owner. The sequence diagram of a use case used to be "the analysis", but UC-A1's named web routes,
a session store, token verification and cookies, which is the design. Two diagrams now, one for each level.
- **Analysis: a system sequence diagram.** It shows the person, Playground as one box, and any outside system
  (for example Keycloak), with the messages between them and the failure branches. It names no route, store, port,
  adapter, token, cookie or algorithm. It is the diagram reviewed with the owner, and it is frozen with the Analysis
  section.
- **Design: a design sequence diagram, and the class diagram.** The sequence diagram shows the parts that do the work:
  routes, use cases, ports and adapters. It is the old detailed diagram. The class diagram (aggregates, ports and
  adapters) is the one that follows the architecture: one for each context under `docs/domain/diagrams/`, plus one
  for the web server (BFF) where a use case runs there. Every step of the design sequence lands on a class, and
  every port or adapter carries a step.
- **The link is the change log.** Each analysis element says what became of it in the design (`A3 became -> D3`),
  as the tool already checks.
- **Not every use case needs both.** A use case with one system and no security flow (for example sign out) keeps a
  single sequence diagram and says so. Both are drawn when more than one system takes part or a security rule
  shapes the steps.

Footnote (decision 15): sign out was given as the example of a use case with one diagram, and turned out to need both an analysis and a design diagram, because two systems take part and a security rule (POST only) shapes its steps. A use case with one system and no security rule is the example that fits, for example a read only page.

**Why.** One diagram cannot serve the owner, who asks what the person sees, and the builder, who asks which port does
it. Mixing them hid a real disagreement: the state check sat in a different step in the flow and in the diagram.

**Changes.** The standard `.claude/skills/_vbench/standards/usecases.md`, the use case, diagram and PlantUML skills, the
spec-challenger agent, and the use case files and diagrams, starting with UC-A1.

**Still open.**
- The web server (BFF) class diagram is not drawn yet.
- UC-A1's analysis is a first revision and is not frozen: freeze it after its open gaps are settled.

## 10. UC-A1 sign in: what a person sees, and what is proven (18 Nov 2026)

**Decided.** By the owner, answering the twelve gaps that vbench-spec-challenger found in UC-A1. They build on decision 8.
- **"Signed in" is testable (AC-1).** The person has a session, and one protected API call (for example `/me`) answers
  200 with their account. Pending and deactivated people are tested in UC-A3 and UC-A4, not here.
- **A pending person** lands on the waiting page, built from their own status.
- **A deactivated person** is normally refused on Keycloak's own page. If they still get through (for example a
  person re-enabled in Keycloak by hand), they land on our own "your account is deactivated" page, and the session
  ends.
- **Order of a deactivation.** Our database changes first, so the API refuses the person at once. Then Keycloak is
  disabled. If that call fails, the deactivation stands, the administrator is told, and the call can be retried.
  The spec and BC-ACCESS, which say Keycloak first, are corrected.
- **Criteria of FR-1.** Four person-visible ones are added: a replayed or expired sign in is refused, a cancelled or
  failed sign in makes no session, a hostile `returnTo` is replaced by a local page, and the browser never holds a
  token. State, nonce and PKCE stay unit tests.
- **AC-32** (any role, a non-member is refused) moves to the Projects use cases (UC-P1, UC-P2). UC-A1 keeps NFR-1
  only through AC-33.
- **The token check.** The audience is required: it is added to AC-33 and to decision 1. A missing, expired,
  wrong-issuer or wrong-audience token gets 401, and no account or audit entry is created.
- **Sessions.** A callback must come from the browser that started the sign in, or it is refused. A second sign in
  ends the person's old session. With two tabs, the later sign in wins, and that is written down.
- **The pending account** is still created at the first API call. UC-A1 ends at the session, and step 9 hands
  over to UC-A3. The postcondition is corrected.
- **Identity is the `sub`, and email is an attribute.** "One account for each email" is dropped as a rule. A new
  `sub` with a known email becomes a second pending account and the administrators are told. A role is never given
  from an unverified email.
- **Keycloak unreachable** when a person starts to sign in is a refusal of UC-A1, with its own criterion: the person
  sees "sign in is not available, try again" and no session is made.

**Why.** The criteria were untestable and the failure paths had none, so a change could break the security
properties of sign in and every test would still pass. Two layers that agree (decision 8) need a defined answer for
every case where they do not.

**Changes.** To be made with vbench-req and vbench-uc: AC-1 rewritten and new criteria added, AC-32 moved, AC-33
and decision 1 amended, the flows, both diagrams, the postcondition and the open questions of UC-A1, UC-A4's order
of steps, the spec and BC-ACCESS, and a note in OBJ-A1 (identity).

**Still open.**
- Email verification is not required for now, and sign in stays simple authentication, by the owner: the product is
  deployed inside the corporate network. A person's name and email are therefore as Keycloak holds them, unverified,
  and an administrator approving a pending account relies on the network boundary and their own knowledge of the
  person. Revisit it with UC-A7 (single sign-on), or before the product is reachable from outside the corporate
  network. It stays one question, held here.
- The web server (BFF) class diagram is not drawn yet (decision 9).
- Lifetimes of a login attempt (10 minutes) and of a session (30 minutes idle, 8 hours) are in the code and the spec,
  and BC-ACCESS still calls them a proposal.

**Footnote (decision 13), to be implemented in the beta version.** For the alpha, keep the sign in answers that
cost nothing (state, nonce and PKCE, no token in the browser, the API checking the token on every request). The
rest is **beta hardening**: the criteria AC-43 (a new sign in ends this browser's earlier session), AC-45 (a
deactivated person who gets through), AC-46 (two sign ins at once) and AC-48 (logging, with NFR-5, now release R2)
are marked R2 in the requirements. Email verification stays off until single sign on or until the product is
reachable from outside the corporate network.

## 11. Three review agents run after a spec change, and teach (18 Nov 2026)

**Decided.** By the owner. Specs are reviewed by three read-only agents, from three lenses, after a use case, its
diagrams, a requirement or a decision is written or changed, and before it is built.
- `vbench-spec-challenger`: does the spec agree with itself (criteria, flows, diagrams, ids).
- `vbench-security-reviewer`: is it sound by OWASP ASVS, the Top 10, the OAuth 2.0 Security BCP and the cheat sheets,
  using generic checklists that travel with the skills (`.claude/skills/_vbench/standards/security/`: web, API and
  GenAI) and this project's overlay (`docs/standards/security-checklist.md`: which lenses apply, what is set aside,
  what is accepted).
- `vbench-design-reviewer`: does the design fit domain driven design, ports and adapters and the AWS target.
- Each finding teaches: what is wrong, why it matters in a concrete case, and up to three options with one marked as
  leaning. They never edit and never decide.
- The skills run them: `vbench-uc` after a use case is written or changed, `vbench-req` after a security related
  criterion changes. `CLAUDE.md` says so for decisions. The agents' descriptions also say "use proactively".

**Why.** The first review of UC-A1 found sixteen gaps by a single lens. Security and architecture are separate
questions from consistency, and a model reciting OWASP from memory can be wrong, so the checklist is kept in the
repo and each finding says whether it is from the checklist or from memory.

**Changes.** Two new agents, the checklist, the challenger's report (a "why it matters" line), the skills `vbench-uc`
and `vbench-req`, the agent table in `_vbench/README.md` and `CLAUDE.md`.

**Still open.**
- The generic checklists are from memory and have no section numbers or editions: look each item up in the current
  OWASP source before relying on it. The GenAI lens has no use case yet. OWASP's broader AI guidance (AI Exchange,
  machine learning security) has no file.
- A hook that nudges the model after an edit under `docs/usecases/` or to `decisions.md` was not added. It would run
  on every edit, so it needs a decision on noise and cost.
- The agents load at session start: restart to use them.

## 12. UC-A1 sign in after the first three reviews (18 Nov 2026)

**Decided.** By the owner, answering the findings of vbench-spec-challenger, vbench-security-reviewer and
vbench-design-reviewer on the rewritten UC-A1. They refine decision 10.
- **A new sign in ends this browser's earlier session only.** It replaces the session the browser already holds.
  Other devices stay signed in. This is the session-fixation defence and needs no find-by-person lookup in the
  session store.
- **UC-A1 ends at the first page the person sees**: their own page, the waiting page, or the deactivated page. This
  amends decision 10's sentence that step 9 hands over to UC-A3 (UC-A3 still creates the pending account).
- **The state is checked before the code is exchanged.** A forged callback never spends a code at Keycloak. The design
  diagram is redrawn to match the flow.
- **The web server (BFF) class diagram is drawn now**, before UC-A1's design is reviewed again, and the design
  sequence is redrawn against it. This closes decision 9's open item.
- **Two sign-ins started at once in one browser: only the latest start can finish.** The older tab is asked to
  sign in again, and a refused older callback does not use up the newer attempt. Signed-in tabs are unaffected: the
  session is shared by every tab of the browser, and signing out in one signs out all of them.
- **A deactivated person who still gets through (AC-45)**: both sessions end, ours and Keycloak's, by reusing
  sign out (UC-A2), so the person is not signed straight back in. AC-45 stays in UC-A1, and FR-4 joins its
  requirements.
- **A pending person landing on the waiting page gets its own criterion**, under FR-3, run by UC-A3.
- **Refusals and session events are logged**: each refused callback, each 401, each session that starts or ends and
  each AC-45 case writes a server log line (event, result, the `sub` when known, a hash of the session id, never a
  token or a code). On AWS this is CloudWatch. A new requirement, NFR-5, carries it.

**Why.** The three reviews agreed on four things: the design diagram showed an older flow, the two-tab text did not
match the built behaviour, "ends the earlier session" was ambiguous, and the web server had no class diagram. These
answers close those and leave the smaller findings (cookie attributes, the algorithm allow list, `returnTo` bypass
cases, lifetimes, the spec and BC-ACCESS lines, UC-A4's role line) as plain corrections.

**Changes.** Criteria AC-43 and AC-45 reworded, AC-46 (two sign ins), AC-47 (waiting page) and NFR-5 with AC-48
(logging) added. UC-A1, UC-A3, both diagrams, a new web server class diagram, the build spec, BC-ACCESS and UC-A4.

**Still open.**
- Where a person's session is kept for a second device (not needed now).
- A rate limit for registration (account flooding): the security reviewer asked for it to be accepted, with a reason
  and a revisit point.
- The status gate in `main.py` belongs in the Access domain, and the token verifier is an edge adapter: both for the
  design review of the code, not the use case.
- The tests for AC-38 to AC-48 and the code (D12, D13) are not built.

**Footnote (decision 13), to be implemented in the beta version.** Everything decided here that is hardening, not
the alpha's login, is **deferred to beta**: ending this browser's earlier session (D13), the planned lookup of an
attempt by the login cookie with a compare and delete step (D4, D14), the deactivated page that ends both sessions
(D12, D15), the security log (D16, NFR-5, AC-48), the cookie prefix and attributes beyond `HttpOnly`, `Secure` and
`SameSite=Lax`, the CSRF check on state changing requests (`Sec-Fetch-Site` or `Origin`), the algorithm allow list
as a criterion, a 503 when the API cannot check tokens, and the registration rate limit. The three reviewers'
remaining findings on UC-A1 are the beta list. Nothing is deleted: the use case, the criteria (notes "R2") and the
diagrams keep the plan.

## 13. Alpha scope: simple sign in, two roles, the administrator is a superuser (19 Nov 2026)

**Decided.** By the owner, on the supervisor's brief for the alpha. It narrows decisions 3, 8, 10 and 12 and
supersedes decision 3 where they differ.
- **Sign in is simple.** Keycloak does the login, and sessions are kept. The product runs inside the corporate
  network.
- **Two account roles: user and administrator.** There is no other role based access control. Everyone who is
  approved is a user and can run evaluations in the projects they belong to.
- **An administrator is a superuser.** They do everything a project manager used to do, and more: create projects,
  add and remove project members, approve signups, and promote other users to administrator. They can also see
  inside every project.
- **Project roles are gone.** A project has members, and every member has the same rights in it: they can run
  evaluations. Only an administrator adds or removes members. Only members and administrators see inside a project,
  and a person who is neither gets the same answer as for a project that does not exist.
- **Accounts arrive in two ways.** A person signs up and waits as pending until an administrator approves. Or an
  administrator creates the account in Keycloak with a temporary password and the "update password" action, and the
  person changes it at first sign in. The second way needs no code of ours.
- **Administrators can promote a user to administrator and demote another administrator.** The last administrator
  is protected (RULE-A1: there is always one), and an administrator does not change themselves (RULE-A2).
- **Projects, endpoints and evaluations stay as the structure of the product.**

**Superseded from decision 3.** Two project roles (manager and engineer), "a project always has a manager",
the administrator who never joins or sees inside, and the project manager's own powers. They are not deleted: the
requirements and criteria move to release R2, and the rules (RULE-P1 to RULE-P3) are marked parked, so a later
release can bring role based access back.

**Deferred to R2.** The review findings that are beta hardening rather than alpha: the CSRF check, the extra
logging (NFR-5), the algorithm allow list, the cookie prefix, the two tab rule, the loop after a deactivated sign in
and the registration rate limit. They stay in the checklist's "Accepted for now" list as one "before beta" set.
**Kept, because it costs nothing:** state, nonce and PKCE, no token in the browser, the API checking the token on every
request, and the ports and adapters structure.

**Why.** The specs had grown to 12 decisions and 48 criteria for a login, an approval and a project list. The
alpha needs a working login with sessions, accounts that can be approved or created, and projects with members
who can run evaluations. A superuser role is the smallest way to give someone all the powers without building the
role model.

**Changes.** To make, with vbench-req and vbench-uc: set the release of the dropped and deferred requirements and
criteria to R2, rework UC-P1 and UC-P2 (create a project, manage members) for the administrator only, add
"promote to administrator" to UC-A4 or a new use case, and update OBJ-P1, OBJ-P2, SET-3, RULE-P4 and BC-PROJECTS.

**Also decided.**
- Promoting or demoting an administrator needs a reason and an audit entry, as RULE-A3 asks for every account change.
- A project does not have to keep a member. An administrator can remove anyone, and an empty project is fine.
- The administrator superuser does everything a member does, in every project: they see inside and run evaluations.

**Still open.** Nothing about roles. The R2 move of the dropped rows and the rework of UC-P1 and UC-P2 are to do.

## 14. Making the alpha ready for code (19 Nov 2026)

**Decided.** By the owner, answering the findings of the three reviewers across all nine use cases. They build on
decision 13.
- **Projects learns who the caller is through a `Caller` value object.** The API resolves the token, the active
  account and the role once, and passes a `Caller` (account id, is administrator) into every Projects use case.
  Projects never looks a role up. Every project route goes through the same full check as the account routes (token,
  account found, not deactivated, not pending) before the role is looked at.
- **What each Projects refusal answers.** A person who is neither a member nor an administrator gets the same 404 as
  for a missing project. A member who is not an administrator changing members, or a user creating a project, gets
  403. A bad name or an inactive first member gets 422. Authorisation is checked before the input is validated.
- **A new use case, UC-P3: list and open a project.** A user lists only the projects they are a member of, and an
  administrator lists all. Opening one follows RULE-P4. For the alpha, a project's "contents" are its detail read
  (name, members, and empty lists for files, endpoints and evaluations).
- **Deactivation order is in the alpha.** Our database changes first and the API refuses the person at once, then
  Keycloak is disabled. If Keycloak fails, the deactivation stands, the administrator is told and the call can be
  repeated. A reinstatement is the reverse and fails closed. Criteria prove both.
- **Reinstating an account needs a reason**, like a deactivation. FR-4 and AC-7 are reworded.
- **Keeping the session alive is a requirement** with three criteria: a refresh before expiry, two requests at once
  send one refresh, and a refused refresh ends the session.
- **An account an administrator creates in Keycloak lands pending**, like a signup, and is approved in Playground
  (UC-A4). Keycloak never decides what a person may do (decision 8).
- **The first-administrator setup rule applies only while no active administrator exists.**
- **The audit trail becomes its own bounded context, Audit (BC-AUDIT).** It owns the audit table and the read of
  it for administrators. Access and Projects each keep an `AuditLog` port and write to it through an adapter that
  the composition root wires to Audit, so no context imports another. An entry holds the actor, the action, what
  kind of thing and which one it was done to, the people involved, the reason and the time, so AC-29 and AC-30 can
  be proven. The existing Access audit moves to it, with a migration.
- **Alembic comes in now**, with a baseline of today's schema and one migration for Audit and Projects. A shared
  database module that belongs to no context holds the declarative base. This closes decision 4's open item.
- **The last-administrator check is one step.** The count and the change cannot be split by a second administrator
  acting at the same moment. A test runs two changes at once. RULE-A1's "repair it by hand in Keycloak" is corrected:
  roles live in our database.
- **Adding a project member needs only an audit entry**, no reason.

**Why.** The reviews agreed that UC-A1 to UC-A6 are built or nearly, and that UC-P1 and UC-P2 cannot be coded until
the caller, the refusals, a way in to the projects, and the audit and tables are decided. A separate Audit context
keeps account and project changes in one trail without one context reaching into another.

**Changes.** To make, with vbench-req and vbench-uc: new requirement rows and criteria (sessions, listing projects,
the audit trail, deactivation failure, reinstating with a reason, refusals, setup rule, last administrator), UC-P3,
the Caller and the refusal table in UC-P1 and UC-P2, a Projects class diagram, the Audit context page and class
diagram, the beta entries in "Accepted for now", and the stale lines the reviewers listed.

**Still open.**
- A project's real contents (files, endpoints, evaluations) come with their own use cases.
- Whether a project name must be unique: not in the alpha.

## 15. UC-A2 sign out after its review (19 Nov 2026)

**Decided.** By the owner, answering the findings of the three reviewers and the break-it check on UC-A2.
- **A person with no session of ours goes home and Keycloak is not asked.** That covers no cookie, a second sign out
  (a double click or a second tab) and an expired session. The use case already said so, and it avoids a Keycloak
  "do you want to log out?" page. The cost: if only our session expired, Keycloak's own session stays until its own
  timeout.
- **Two new criteria.** AC-71: a GET to the sign out address does nothing and the session still works. AC-72: sign out
  ends on our home page, not on an identity provider error page, and the end session address carries the person's ID
  token as the hint and exactly our home page as the return address.
- **Sign out never throws.** A session store that fails is the same as no session: the person goes home, and the route
  clears the cookie on every path.
- **Deferred to the beta list**, with the reason that the alpha is one process inside a corporate network:
  sign out during a token refresh can write the session back (the store needs a "replace only if present" write),
  server sessions have no lifetime of their own (a TTL in the store, native in ElastiCache), and a cross site POST
  clears only the cookie (the deferred CSRF check).

**Why.** The review showed that the use case promised things the code did not do (home page for no session, home page
when Keycloak is down later), and that three security-relevant behaviours (the hint, the return address, GET) were not
tested at all.

**Changes.** `signOut` (test first), AC-71 and AC-72 with integration tests, UC-A2's text and diagrams, the beta list
in the security overlay, and a note on UC-A1's beta reuse of sign out (it will need a return address parameter).

**Still open.** Nothing for the alpha.

## 16. UC-A3 sign up and wait, and the approve handover (20 Nov 2026)

**Decided.** By the owner, answering the reviews of UC-A3 and the approve part of UC-A4.
- **The setup administrator only exists while there is none (AC-61).** An account made from the setup email, verified, is
  an active administrator only while no active administrator exists. Otherwise it is pending. An unverified setup email
  is pending too (AC-75).
- **The setup list defaults to empty, so it fails closed.** No setup administrator is made unless someone configures one.
  Docker compose and `.env.example` keep the example address for local work. The seeded demo users in the realm file
  (`admin@example.test` and `maya@example.test`, with known passwords) are dev only: accepted for now, until the first
  deployment that is not local.
- **A written precondition and recovery.** The setup user is created and verified in Keycloak before the product opens.
  If that was missed (a stranger registered the setup email first), the recovery is a short, written step, in UC-A3 and
  RULE-A5.
- **What proves an approval worked (AC-5):** on their next request the person's account is active and the dashboard
  shows their own page, not "Waiting for approval", and Keycloak was not changed.
- **A duplicate email is a warning, and the administrator decides (AC-73).** When a pending account has an email that
  another account already has (a new `sub` with a known email, or a deactivated person who registers again), the
  administrator's list marks it with a warning that shows the other account. Nothing is blocked and nothing is decided
  by the system. This narrows decision 10's "the administrators are told" to a warning in the list, and nothing
  more, with no notification.
- **AC-4 means every declared route** except `/me` and `/health`: a test walks the route table, so a new route that
  forgets its guard fails it. AC-63 covers a pending and a deactivated actor as well as an ordinary user. Approving an
  account that does not exist, or is not pending, is refused with a clear answer (AC-76).

**Why.** The review found the setup rule open (any verified setup email became an administrator at any time, with a
public default), an approval criterion that could not show the approval worked, and a promise (administrators are told)
that nothing kept.

**Changes.** AC-4, AC-5 and AC-63 reworded, AC-73 to AC-76 added; the setup rule built test first; the list marks
duplicate emails; the diagrams, RULE-A5 and UC-A3 corrected; the config default emptied.

**Known debt, not in this change.** The pending, deactivated and administrator gates still live in `main.py` route
guards, not in the domain. They move when Projects needs the Caller (ADR 0002). The loser of a first request race gets
a 500 (accepted, beta list). Two administrators approving at once leave two audit entries (accepted).

## 17. Basic audit trail and basic logging are part of the alpha (20 Nov 2026)

**Decided.** By the owner.
- **The audit trail is in the alpha** (FR-13, FR-17, UC-L1). It was already release R1. This confirms it: account
  changes and project changes are written to one trail that an administrator reads. Recording stays the last step of
  UC-A4, UC-P1 and UC-P2 (no use case of its own), through each context's `AuditLog` port and a bridge (decision 14).
- **Basic logging is in the alpha.** NFR-5 and AC-48 move from R2 to R1: a log line for every refused sign in, every
  refused request and every session that starts or ends, with no token or code in it. This reverses the deferral in
  decision 13 for this one item.
- **Logs go to stdout as JSON lines**, so that on AWS the ECS `awslogs` driver sends them to CloudWatch with no code
  change. The technical choices (formatter, request id, the `SecurityLog` port) go in an ADR.

**Why.** Without a trail and logs, nobody can say who changed what or why a request was refused, and moving to AWS
would mean adding them under pressure.

**Changes.** NFR-5 and AC-48 release R1; the note on NFR-5 and the security overlay's beta list must follow.

**Still open.** Should UC-A3 (register) write an audit entry? Should a refused change or a read be recorded?
Metrics and tracing stay out of the alpha.


## 18. UC-A4 deactivation when Keycloak is down (20 Nov 2026)

**Decided.** By the owner.
- **A failed Keycloak disable is retried by repeating deactivate (AC-77).** Deactivating an account that is already
  deactivated, with a reason, only sends the Keycloak calls again. It changes nothing in our database. This is the one
  exception to "only an active account can be deactivated" (AC-66).
- **When Keycloak was not updated, the administrator gets a success with a warning:** "Deactivated here. Keycloak was
  not updated. Press again to retry." The change did happen, so it is not an error (AC-58).
- **One audit entry for each change, with an outcome:** done, or Keycloak not updated. Refused attempts go to the
  log (decision 17), not the audit trail. This answers decision 17's open question on refused changes, for UC-A4.

**Why.** The review found that "the call can be repeated" was false: a second deactivate was refused as wrong state,
so a person could stay enabled in Keycloak with no way to fix it. It matters once other products share the realm.

**Changes.** AC-58 and AC-62 reworded, AC-77 added, AC-66 notes the exception, UC-A4 text and diagrams. ADR 0009
records the technical side (commit order, locking).

**Still open.** Whether UC-A3 (register) writes an audit entry (decision 17).

## 19. Keycloak owns the name; the application does not edit it (20 Nov 2026)

**Decided.** By the owner, after weighing three options (Keycloak owns it and we link to it; our own display name; writing the name back to Keycloak).
- **Name, email and password are changed in Keycloak's account page.** The dashboard links to it (AC-78). The application has no way to edit them.
- A name changed in Keycloak shows from the next token renewal or sign in, not at once (UC-A5).

**Why.** One owner for the name avoids edits that the next token overwrites, avoids giving our API power over every user's profile, and fits the company single sign-on in the beta (UC-A7), where names come from the company directory.

**Changes.** AC-78 added, UC-A5 text corrected (when a changed name shows), the dashboard link built test first.

**Still open.** Nothing for the alpha.

## 20. The alpha runs as one set of containers on one EC2 instance (20 Nov 2026)

**Decided.** By the owner.
- **The alpha has no scalability.** Everything (the web app, the API, Keycloak and Redis) runs as containers on one EC2 instance. Only the data is on RDS (the API database and Keycloak's database).
- **So there is one web container, and UC-A6's refresh lock needs no shared lock.** The risk of two web containers refreshing one session at once is accepted for the alpha and listed in the security overlay's "Accepted for now".

**Why.** The alpha goes to people inside the corporate network, and scaling out is not an alpha need.

**Changes.** UC-A6's open question 2 is decided; the overlay lists the accepted risk with when to revisit it (before a second web container, or the move to ECS Fargate).

**Still open.** Nothing for the alpha.

## 21. The audit trail is append only and read only (20 Nov 2026)

**Decided.** By the owner.
- **No entry is ever changed or deleted**, by anyone, through the application. The trail only grows (AC-79). A mistake is corrected by adding an entry.
- **The database enforces it.** The database user the API uses may add and read audit rows, and may not update or delete them (AC-80). A bug or stolen API credentials cannot rewrite history. Tamper evidence (a hash chain) and a copy in storage that cannot be changed are left for later.
- **The Audit trail is its own bounded context (BC-AUDIT)**, with the same folder layout as every context (ADR 0010). Access and Projects each keep a small `AuditLog` port, wired to Audit in the composition root.
- **A failed Keycloak call after a deactivation adds a second entry** that says Keycloak was not updated. The first entry is not edited. This changes decision 18's "one audit entry with an outcome" to "one entry for each fact".

**Why.** An audit trail that can be edited proves nothing. Enforcing it in the database is the guarantee; the code alone is only good manners.

**Changes.** AC-79 and AC-80 added; AC-58 and UC-A4 reworded; UC-L1's design gains the permission step; ADR 0011 records the technical choices (and supersedes the audit part of ADR 0009); `set_outcome` goes away when the Audit context is built.

**Still open.** Retention (how long entries are kept) is not decided. Whether UC-A3 (register) writes an audit entry is still open from decision 17.
