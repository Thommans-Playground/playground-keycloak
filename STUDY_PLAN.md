# Keycloak Study Plan

A hands-on, follow-along plan for this playground repo. Work through it in order — each stage builds on the Keycloak instance/realm from the previous one. Check items off as you go.

## Stage 0 — Prerequisites

- [ ] Docker installed and running
- [ ] `curl` or `httpie` for poking the Admin REST API
- [ ] A throwaway sample app to authenticate (pick one: tiny Express app, or just use `oidc-debugger`/Postman as the client)

## Stage 1 — Core concepts (read + run, ~1-2 sessions)

- [ ] Start Keycloak locally:
  ```bash
  docker run -p 8080:8080 -e KC_BOOTSTRAP_ADMIN_USERNAME=admin -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
    quay.io/keycloak/keycloak:latest start-dev
  ```
- [ ] Log into the admin console at `http://localhost:8080` and look around the `master` realm
- [ ] Learn the vocabulary by creating one of each, by hand, in the console:
  - [ ] A new **realm** (not `master`) — this is your isolated tenant
  - [ ] A **client** (confidential, then try a public one) — represents an app
  - [ ] A **user** with a password
  - [ ] A **realm role** and a **client role**, assign one to the user
  - [ ] A **group**, add the user to it
- [ ] Understand the difference between realm roles, client roles, and groups before moving on

## Stage 2 — OIDC login flow end-to-end

- [ ] Read up on the Authorization Code flow + PKCE (why PKCE matters for public clients)
- [ ] Configure your test client's valid redirect URIs
- [ ] Walk the flow manually with curl/browser: hit the authorization endpoint, capture the code, exchange it at the token endpoint
- [ ] Decode the resulting access token and ID token (jwt.io or `jwt-cli`) — identify `iss`, `aud`, `exp`, `realm_access.roles`
- [ ] Wire a real sample app (Express + a library like `openid-client`, or any stack you prefer) to log a user in and print the decoded token
- [ ] Try a refresh token exchange
- [ ] Try token introspection and the logout endpoint

## Stage 3 — Realm-as-code (export/import)

- [ ] Export your realm: `kc.sh export --realm <name> --file realm-export.json` (or via Admin REST API `/admin/realms/{realm}/partial-export`)
- [ ] Delete the realm, re-import it from the JSON, confirm clients/users/roles come back
- [ ] Commit the exported JSON into this repo under `realm-config/` and treat it as the source of truth from now on — stop hand-editing in the console
- [ ] Learn `kcadm.sh` basics (`kcadm.sh create/get/update` against clients, roles, users) as the scriptable alternative to the console

## Stage 4 — Themes & SPIs

- [ ] Create a minimal custom login theme (override just the login page CSS/freemarker template), mount it, select it on the realm
- [ ] Read about the SPI model (authenticators, event listeners, user storage providers) — pick ONE small SPI to build (an event listener that logs login events is a good first one)
- [ ] Package the SPI as a jar, drop it in `providers/`, confirm it loads (`docker logs` should show it registered)

## Stage 5 — Authorization services (optional deep-dive)

- [ ] Enable fine-grained authorization on a client
- [ ] Define a resource, a policy, and a permission; test a UMA-style authorization request
- [ ] Decide whether this is overkill for your company's actual use case (often RBAC via roles/groups from Stage 1-2 is enough)

## Stage 6 — Distribution via Google's `repo` tool

This is the "ship it to other company projects" phase — only start once Stage 3 (realm-as-code) is solid.

- [ ] Create a standalone `keycloak-config` repo containing `realm-export.json`, the theme, and any SPI jars from Stages 3-4
- [ ] Create a manifest repo (`repo init -u <manifest-repo-url>`) listing `keycloak-config` as one `<project>` alongside the company's actual product repos
- [ ] Pin a revision/tag of `keycloak-config` in the manifest; confirm `repo sync` pulls it into a consistent path in a test checkout
- [ ] Write a small bootstrap script (run in CI/deploy) that takes the synced `realm-export.json` and applies it via `kcadm.sh` or the partial-import REST endpoint
- [ ] Decide on an update strategy: who bumps the pinned revision when the realm config changes, and how a project opts into a new version

## Notes

- Keep realm exports out of `master` realm — always work in a dedicated realm so you can delete/recreate freely while learning.
- Re-run `docker run` with a mounted volume once you want state to survive restarts (`-v keycloak-data:/opt/keycloak/data`), or switch to `docker compose` once you're past Stage 2.
