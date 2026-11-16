## 23. Keycloak is the identity provider (12 Nov 2026)

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
- How a new person arrives as pending: decided in decision 24.
- How acceptance tests sign in: a Keycloak container with an imported realm, or tokens signed with a test key.
- Where Keycloak runs, and its database (it can share the Postgres server). The realm configuration belongs in the repo.
- Whether the sign-in page is Keycloak's own login theme (one can be built from React parts) or something else.
- FR-24, single sign-on, is Release 2. It is now configuration, so the release may move.
- New requirements to write with vbench-req: identify the person from the token, and link a person to a Playground
  account on first sign in.
- UC-A1 and UC-A5 to UC-A9 were MK3's sign-in items. They are retired (see `docs/usecases/retired-ids.csv`) and never reused.

## 24. Pending accounts, membership and time-limited access (16 Nov 2026)

**Decided.** Three answers by the owner, which refine decision 23.
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


## 25. Projects and who may see inside them (16 Nov 2026)

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

**Why.** Membership is an invariant of the project, so Projects owns it (decision 24). Keeping administrators out
of the contents keeps the governance boundary real: the person who keeps accounts cannot read the work. The one
administrator power is the smallest that stops a project being locked.

**Changes.** New context BC-PROJECTS, objects OBJ-P1 and OBJ-P2, value set SET-8, rules RULE-P1 to RULE-P4,
requirements FR-129 to FR-143 and criteria AC-87 to AC-110, use cases UC-P1 and UC-P4. SET-6 and OBJ-A1 now
include the pending status that decision 24 introduced. BC-ACCESS no longer describes membership or the account
request queue.

**Still open.**
- Whether a project name must be unique, and within what.
- Whether a manager can name a second manager at creation.
- Whether removing a member needs a reason.
- Files, endpoints and evaluations are not ontology objects here yet.
- FR-5 still says account roles are member, administrator or auditor.
- UC-A4 (time-limited access) is still undecided.
- OBJ-A2, OBJ-A3, SET-7, RULE-A4 and RULE-A5 are linked from the Access pages but have no files here.

## 26. AWS is the target, and the code follows DDD, TDD and hexagonal (17 Nov 2026)

**Decided.** Two standing constraints, by the owner.
- **The final application always runs on AWS.** The organisation is AWS native. The playground may use open source
  engines locally, but each has an AWS equivalent, and the move is configuration, not a rewrite: PostgreSQL becomes
  Amazon RDS (or Aurora) for PostgreSQL, for Playground's own database and for Keycloak's. **Keycloak stays the identity
  provider and runs on ECS Fargate with RDS**, as in the prototype, so decision 23 is unchanged. Other pieces map as
  follows: the web session store (in memory today) to ElastiCache, secrets to Secrets Manager, project files to S3 and
  logs to CloudWatch.
- **The application, frontend and backend, follows domain driven design, test driven development and hexagonal
  architecture (ports and adapters).** The domain is pure rules. Everything outside it (database, Keycloak, session
  store, AWS services) sits behind a port with an adapter. A rule or a use case gets its failing test first.

**Why.** A prototype that uses an engine the target does not have hides problems until the move. SQLite hides
differences in types, locking and migrations, so the API's database is now PostgreSQL, the engine behind RDS. Ports
and adapters are what make the swap cheap: an adapter changes and the domain does not.

**Changes.** The API's database is PostgreSQL (`api-db` in Docker Compose). The API tests run on SQLite for speed, and on
PostgreSQL when `TEST_DATABASE_URL` is set. `CLAUDE.md` records both constraints.

**Still open.**
- Schema changes: the API creates its tables at start-up. On AWS they need migrations (for example Alembic), run as a
  deploy step.
- Whether Playground's database is RDS PostgreSQL or Aurora PostgreSQL.
- How the web side applies hexagonal: its session store is behind a few functions today, and the other adapters
  (the API client, the OpenID Connect calls) are not yet ports.
- Keycloak on ECS needs a production setup (not `start-dev`), its own sizing, and a decision on high availability.
