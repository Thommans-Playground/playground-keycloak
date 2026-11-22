---
term: BFF
say: A BFF (backend for frontend) is a small server that belongs to the website, does the sign in, and keeps the tokens so the browser never has to.
aliases: [BFF, backend for frontend, backend-for-frontend]
code:
  - apps/web/src/lib/auth/session.ts :: cookieOptions
  - apps/web/src/proxy.ts :: playground_session
guide: 1.11 The BFF pattern
check: Where is the access token while you are signed in?
---

## In one line

Our Next.js server is the backend of our own website. It does the sign in, holds the tokens in a server-side session, and calls the API for the browser.

## Why we need it

Anything a browser holds can be reached by a script injected into the page. If the tokens live on our server, there is nothing for such a script to steal. The browser holds only an opaque session id in a cookie, and the server looks the tokens up with it.

## In our code

`cookieOptions` in `lib/auth/session.ts` sets the one cookie we give the browser. `proxy.ts` sends a person with no `playground_session` cookie to sign in.

## Look for yourself

Study guide experiment 5: look at what the browser can and cannot see, and search the page for a token.
