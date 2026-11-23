---
term: Service account and client credentials
say: A service account is a login for a program, not a person. The program signs in with its own id and secret, the client credentials grant.
aliases: [service account, client credentials, client_credentials, playground-backend]
prereq: [openid-connect]
code:
  - apps/api/app/access/adapters/outbound/keycloak_admin.py :: client_credentials
  - apps/api/app/access/adapters/outbound/keycloak_admin.py :: KeycloakAdmin
guide: 1.12 Service accounts
check: The backend's secret leaks. Why is it still worth giving that client only view-users, query-users and manage-users?
---

## In one line

When a program and not a person needs a token, it sends its own client id and secret to Keycloak and gets an access token back. No browser, no code, no person.

## Why we need it

The API must disable a person in Keycloak and end their sessions. Only Keycloak's admin API can do that, and it wants a token. The `playground-backend` client has a service account with three rights and no more, so a leak of its secret reaches only those. The secret lives in the API's settings, never in the browser.

## In our code

`KeycloakAdmin._bearer` posts `grant_type: client_credentials` with the client id and secret to the realm's token address, and keeps the token until just before it expires. `enable_user`, `disable_user` and `end_sessions` use it.

## Look for yourself

Open `keycloak_admin.py` and find `_bearer`. Then read study guide section 1.12 and find `playground-backend` in the realm import.
