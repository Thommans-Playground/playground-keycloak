---
term: Identity is the sub
say: A person is identified by the `sub` Keycloak gives them, never by their email.
aliases: [sub claim, Keycloak sub, identity is the sub, never the email]
code:
  - apps/api/app/access/domain/account.py :: identity
guide: 0.5 Two records, one person
check: Why would using the email as the key be dangerous?
---

## In one line

Every Keycloak user has a permanent id, the `sub`. Our account row is linked to it.

## Why we need it

An email can change, be reused, or be unverified. If we trusted the email, someone who obtained a matching address could be treated as an existing person. The `sub` is issued by Keycloak and does not change, so nothing is merged or taken over by accident. The account also holds the role and status that Keycloak does not know.

## In our code

`identity` in `domain/account.py` is documented as the Keycloak `sub`, never the email.

## Look for yourself

Open `account.py` and read the comment on `identity`, then the warning for duplicate emails.
