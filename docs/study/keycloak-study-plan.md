# Keycloak study plan

A hands-on, follow-along plan for this playground. Work through it in order: each stage builds on the Keycloak instance and realm from the one before. Tick the boxes as you go. The boxes are **your** progress, so they start empty. Under each stage, "Already in this repo" says what you do not have to build.

## How this plan fits with the rest of the study material

| Material | Use it for |
|---|---|
| This plan | the order to learn Keycloak in |
| [Auth study guide](../AUTH-STUDY-GUIDE.md) | how sign in works in this app: theory, the code flow by flow, ten experiments, the pre-deploy checklist. Read it during Stage 2 |
| [Getting started](../GETTING-STARTED.md) | running the stack and a tour of the code |
| [Web hexagon concepts](web-hexagon-concepts.md) and the build lessons ([sign in](UC-A10-sign-in-test-first.md), [sign out](UC-A11-sign-out-test-first.md)) | after Stage 2: rebuild the web side with ports and adapters, test first (decision 26) |

## Stage 0: Prerequisites

- [ ] Docker installed and running
- [ ] `curl` or `httpie` for poking the Admin REST API
- [ ] A client to authenticate: this repo's Next.js app (`apps/web`) is one, so you do not need a throwaway app

## Stage 1: Core concepts (read and run, 1 to 2 sessions)

**Already in this repo:** Keycloak 26.4 and its PostgreSQL in [keycloak-config/docker-compose.yml](../../keycloak-config/docker-compose.yml), with the `playground` realm imported from [playground-realm.json](../../keycloak-config/realm/playground-realm.json).

- [ ] Start Keycloak locally. In this repo: `docker compose up -d` in `keycloak-config/` (Keycloak alone), or at the root for the whole stack. Both pin the version, unlike `:latest`
- [ ] Log into the admin console at `http://localhost:8080` (`admin` / `admin`) and look around the `master` realm, then the `playground` realm
- [ ] Learn the vocabulary by creating one of each, by hand, in the console, in a **scratch realm** (not `playground`):
  - [ ] A new **realm** (not `master`): this is your isolated tenant
  - [ ] A **client** (confidential, then try a public one): represents an app
  - [ ] A **user** with a password
  - [ ] A **realm role** and a **client role**, assign one to the user
  - [ ] A **group**, add the user to it
- [ ] Understand the difference between realm roles, client roles, and groups before moving on

**Worth knowing for this app:** it uses **none** of roles or groups for what a person may do. Roles and status live in the API's database (decision 23, amended). The only client roles in the realm are the three `realm-management` rights on the backend's service account.

## Stage 2: OIDC login flow end to end

**Already in this repo:** a working authorization code flow with PKCE (`apps/web`), a confidential client, a refresh, a logout, and a token check in the API. The [auth study guide](../AUTH-STUDY-GUIDE.md) walks all of it.

- [ ] Read up on the Authorization Code flow and PKCE (why PKCE matters, even for a confidential client): the guide, Part 1
- [ ] Configure your test client's valid redirect URIs (compare with the `playground-web` client in the realm file)
- [ ] Walk the flow manually with curl and a browser: hit the authorization endpoint, capture the code, exchange it at the token endpoint (the guide, Part 3 Flow A and the experiments)
- [ ] Decode the resulting access token and ID token. Identify `iss`, `aud`, `exp`, `sub`. Tokens can carry role claims (`realm_access`, `resource_access`; the service account token in experiment 3 has `resource_access`), which this app deliberately ignores
- [ ] Wire a real app to log a user in and read the decoded token: do it by reading `apps/web/src/adapters/keycloak-identity-provider.ts` and `application/sign-in.ts`, then compare with the [sign in lesson](UC-A10-sign-in-test-first.md)
- [ ] Try a refresh token exchange (`accessTokenFor` in `application/access-token.ts`, and the guide's Flow B)
- [ ] Try token introspection and the logout endpoint (the logout route is in the guide's Flow D)

## Stage 3: Realm as code (export and import)

**Already in this repo:** the realm is a file, imported once at first start (`--import-realm`), and kept in git. It is **not** re-read if the realm already exists: wipe with `docker compose down -v` to re-import.

- [ ] Export your realm: `kc.sh export --realm <name> --file realm-export.json` (or via the Admin REST API `/admin/realms/{realm}/partial-export`)
- [ ] Delete a scratch realm, re-import it from the JSON, confirm clients, users and roles come back
- [ ] Treat the exported JSON as the source of truth and stop hand-editing in the console. In this repo it lives in `keycloak-config/realm/`, the folder that becomes the `keycloak-config` repo in Stage 6
- [ ] Learn `kcadm.sh` basics (`kcadm.sh create/get/update` against clients, roles, users) as the scriptable alternative to the console

## Stage 4: Themes and SPIs

- [ ] Create a minimal custom login theme (override just the login page CSS or template), mount it, select it on the realm
- [ ] Read about the SPI model (authenticators, event listeners, user storage providers) and pick ONE small SPI to build (an event listener that logs login events is a good first one)
- [ ] Package the SPI as a jar, drop it in `providers/`, confirm it loads (`docker logs` should show it registered)

## Stage 5: Authorization services (optional deep dive)

- [ ] Enable fine-grained authorization on a client
- [ ] Define a resource, a policy, and a permission, and test a UMA-style authorization request
- [ ] Decide whether this is overkill for your company's actual use case. In this app it is not used: authorization is the API's own rules over its own database (accounts today, projects and membership next)

## Stage 6: Distribution via Google's `repo` tool

This is the "ship it to other company projects" phase. Only start once Stage 3 (realm as code) is solid. It is Phase 2 in [CLAUDE.md](../../CLAUDE.md).

- [ ] Create a standalone `keycloak-config` repo containing `realm-export.json`, the theme, and any SPI jars from Stages 3 and 4 (start from the `keycloak-config/` folder)
- [ ] Create a manifest repo (`repo init -u <manifest-repo-url>`) listing `keycloak-config` as one `<project>` alongside the company's actual product repos
- [ ] Pin a revision or tag of `keycloak-config` in the manifest, and confirm `repo sync` pulls it into a consistent path in a test checkout
- [ ] Write a small bootstrap script (run in CI or deploy) that takes the synced `realm-export.json` and applies it via `kcadm.sh` or the partial-import REST endpoint
- [ ] Decide on an update strategy: who bumps the pinned revision when the realm config changes, and how a project opts into a new version

## Stage 7: Running it on AWS

The final application always runs on AWS ([decision 26](../domain/decisions.md)). Keycloak stays the identity provider and runs on ECS Fargate with RDS. The [auth study guide](../AUTH-STUDY-GUIDE.md), Part 8, is the checklist.

- [ ] Run Keycloak in production mode (`start`, not `start-dev`) behind a load balancer, with the right hostname and proxy settings
- [ ] Point Keycloak at Amazon RDS for PostgreSQL, and the API's own database too (a `DATABASE_URL` change: it is already PostgreSQL)
- [ ] Move every secret (client secrets, database passwords, the bootstrap admin) to AWS Secrets Manager and rotate the dev values
- [ ] Replace the web server's in-memory session store with ElastiCache (one adapter behind the `SessionStore` port, and `composition.ts`)
- [ ] Turn on HTTPS, `Secure` cookies, email verification, and a second factor for administrators

## Notes

- Keep realm exports out of the `master` realm: always work in a dedicated realm so you can delete and recreate freely while learning.
- State survives restarts through Docker volumes (`keycloak-db` and `api-db`). `docker compose down -v` wipes them and re-imports the realm.
- Stage 1 asks you to create things by hand. Do that in a scratch realm, so the `playground` realm file stays the source of truth.
