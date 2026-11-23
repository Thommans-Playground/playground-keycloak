---
term: Open redirect
say: An open redirect lets an attacker use your own sign in to send a person to a site of theirs.
aliases: [open redirect, returnTo, return address]
code:
  - apps/web/src/domain/return-to.ts :: safeReturnTo
prereq: [openid-connect]
guide: 1.13 Open redirect
check: Why must safeReturnTo refuse `//evil.example` even though it starts with a slash?
---

## In one line

After sign in we send the person back to where they were headed, named in `returnTo`. If we sent them wherever `returnTo` says, a link could carry them to a fake site that looks like ours.

## Why we need it

We accept only a path on our own site. Four forms are replaced by the default page (AC-40): no leading `/`, a leading `//`, a leading `/\`, and any control character. `//evil.example` looks like a path but a browser reads it as another site, `/\` is read the same way by some browsers, and control characters can hide a different address from the check.

## In our code

`safeReturnTo` in `domain/return-to.ts`, called by `startLogin` before the value is saved with the login attempt.

## Look for yourself

Start a sign in with `returnTo=//evil.example`, finish it, and see that you land on a page of ours.
