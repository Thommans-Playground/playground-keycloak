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

