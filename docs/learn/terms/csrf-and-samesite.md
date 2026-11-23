---
term: CSRF and SameSite
say: CSRF is another site making your browser send a request you never meant. SameSite tells the browser not to attach our cookie to such requests.
aliases: [CSRF, cross-site request forgery, cross site request forgery, login CSRF, Sec-Fetch-Site]
prereq: [session-cookie]
code:
  - apps/web/src/lib/auth/session.ts :: sameSite
  - apps/web/src/domain/proxy-methods.ts :: PROXY_METHODS
  - apps/web/src/app/auth/logout/route.ts :: POST
check: A page on another site posts a form to our sign out address. Today, what stops it and what does not?
---

## In one line

A browser attaches your cookie to any request to our site, even one a hidden form on another site sent. That is the forgery.

## Why we need it

Three things help us today. The session cookie is `SameSite=Lax`, so the browser does not send it on another site's background posts. Sign out is POST only, so a link or an image cannot trigger it. The proxy forwards only GET, POST and DELETE. What we do not have yet is the CSRF check itself, the `Sec-Fetch-Site` or `Origin` test on every state changing request. It is accepted for the alpha and listed under "Before beta" in `docs/standards/security-checklist.md`. Until then a cross site POST to sign out clears only the cookie.

## In our code

`sameSite: "lax"` in `cookieOptions`, `PROXY_METHODS` in `domain/proxy-methods.ts`, and the `POST` only handler in `app/auth/logout/route.ts`. Login CSRF is a different attack, stopped by `state` (see State and nonce).

## Look for yourself

Read the "Before beta" list in `docs/standards/security-checklist.md` and find the CSRF line. Then try `curl -i http://localhost:3000/auth/logout` and see that a GET is refused (405).
