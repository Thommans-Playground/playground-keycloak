---
term: Authentication and authorisation
say: Keycloak says who you are. Our API says what you may do. They are two answers from two systems.
aliases: [authentication, authorisation, authorization, authn, authz, deny by default]
code:
  - apps/api/app/access/adapters/inbound/http.py :: Principal
guide: 1.1 Authentication and authorization
check: Why does deactivating a person work at once, even though their token is still valid?
---

## In one line

Authentication is proving who someone is. Authorisation is deciding what they may do. A valid token answers only the first.

## Why we need it

On every request the API verifies the token, then reads the person's account from its own database: their role and their status. A deactivated person is refused straight away even though their token has not expired (AC-6). The browser's role switch is for show; the server decides, and refuses by default.

## In our code

`Principal` in the inbound `http.py` is the verified caller the routes receive. The account lookup follows in the service.

## Look for yourself

Study guide experiment 7: deactivate someone who is signed in and watch their next request be refused.
