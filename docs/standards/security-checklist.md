# Security checklist: this project's overlay

The generic checklists live with the skills, in `.claude/skills/_vbench/standards/security/`:
[web.md](../../.claude/skills/_vbench/standards/security/web.md) (WEB-1 to WEB-15),
[api.md](../../.claude/skills/_vbench/standards/security/api.md) (API-1 to API-10) and
[genai.md](../../.claude/skills/_vbench/standards/security/genai.md) (GEN-1 to GEN-10).
`vbench-security-reviewer` reads them, then this file. This file holds only what is **ours**: which lenses apply, the
items we adopt or set aside, and the risks we accept for now. Cite items by id, and a decision for each deviation.

## Which lenses apply

| Lens | Applies to | Notes |
|---|---|---|
| Web (`web.md`) | every use case | sign in, sessions, accounts, audit |
| API (`api.md`) | every use case that adds or changes an API route | the API in `apps/api` |
| GenAI (`genai.md`) | a use case that sends data to a model, uses its output or lets it call tools | none yet. Evaluations (BC-EVALUATIONS) will probably need it |

## Items we adopt or set aside

None set aside yet. Add a line here, with the decision, when an item does not apply.

## Accepted for now

- **Email verification is off** (decision 10): the product is deployed inside the corporate network. This accepts a
  risk under WEB-13 and WEB-10. Revisit it with UC-A7 or before the product is reachable from outside the network.
- **Registration is not rate limited**: anyone who can reach Keycloak can create pending accounts without limit (API-4
  and API-6 in `.claude/skills/_vbench/standards/security/api.md`). Reason: the product is deployed inside the
  corporate network (as decision 10). Revisit it before the product is reachable from outside, or with UC-A3.
- **First request race** (UC-A3): two first requests of one new person at the same moment are not handled in code; the
  database's unique identity keeps it to one account. Reason: alpha, inside the corporate network. Revisit it with
  UC-A3's build, or before the product is reachable from outside.
- **One web container** (decision 20): the refresh lock of UC-A6 is a map inside one web process. With a second web container two requests of one session could refresh at once, and Keycloak would end the session. Reason: the alpha runs as one set of containers on one EC2 instance, with only the data on RDS. Revisit it before a second web container runs (a lock in Redis, test first), or when the web tier moves to ECS Fargate.
- **The database owner can edit audit rows** (decision 22, ADR 0011): the API role can only add and read, but the owner role (the RDS master user, which also runs the migrations) can still change or delete rows. Reason: the alpha runs inside the corporate network and few people hold the owner secret. Revisit it before the beta, with a hash chain or an immutable copy (S3 Object Lock, CloudWatch), and keep the owner secret to the migration step.
- **Personal data is kept in the audit trail** (decision 22): names, emails and free text reasons stay in the entries, with no retention limit. Reason: the trail has to say who did what, and the alpha has few people. Revisit it before the beta, when retention is decided (BC-AUDIT open question 2).
- **Before beta (decision 13). Deferred hardening, accepted for the alpha because the product runs inside the corporate
  network (as decisions 10 and 13). Revisit all of it at beta, or before the product is reachable from outside the
  corporate network, whichever comes first:
  - the CSRF check (`Sec-Fetch-Site` or `Origin`) on state changing requests;
  - the algorithm allow list as a criterion (part of AC-33);
  - the cookie prefix (`__Host-`) and attributes beyond `HttpOnly`, `Secure` and `SameSite=Lax`;
  - the two tab rule (AC-46);
  - ending this browser's earlier session when the person signs in again (AC-43);
  - the deactivated loop: both sessions end when a deactivated person gets through (AC-45);
  - a 503 when the API cannot check tokens (UC-A1's open question);
  - the registration rate limit (also listed above);
  - the access token kept from before sign out, which passes the API's checks until it expires (UC-A2);
  - sign out during a token refresh can write the session back: the session store needs a "replace only if present"
    write (UC-A2, decision 15);
  - server sessions have no lifetime of their own: the store needs a TTL, native in ElastiCache (UC-A2, decision 15);
  - a cross site POST to the sign out address clears only the cookie, until the CSRF check above (UC-A2, decision 15);
  - Keycloak down after the first call leaves a browser error page on sign out, because the end session address is
    built locally; our side is signed out either way (UC-A2, decision 15). Accepted because the product runs inside
    the corporate network; revisit at beta.
  - FastAPI `/docs` and the default backend client secret outside dev;
  - the RDS PostgreSQL version must be 15 or later, and pgAudit on the owner role is not set up (ADR 0011 amendments, decision 22).
