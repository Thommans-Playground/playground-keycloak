---
term: Session cookie
say: The session cookie is a random id that stands for a signed-in person. It is not a token and it holds no data.
aliases: [session cookie, HttpOnly, SameSite, Secure flag, playground_session]
code:
  - apps/web/src/lib/auth/session.ts :: httpOnly
  - apps/web/src/lib/auth/session.ts :: sameSite
  - apps/web/src/lib/auth/session.ts :: secure
guide: 1.10 Sessions and cookies
check: Why is a session id safer in an HttpOnly cookie than in the page?
---

## In one line

`playground_session` holds a 43 character random id. The server looks up the person's session by it.

## Why we need it

Three flags protect it. HttpOnly means scripts in the page cannot read it. SameSite=Lax means the browser sends it when the person comes back from Keycloak, but not on a cross-site form post. Secure means it is only sent over HTTPS. We set Secure when the app address starts with https, so it is off on plain http://localhost.

## In our code

`cookieOptions` in `lib/auth/session.ts`: `httpOnly: true`, `sameSite: "lax"` and `secure: secure()`.

## Look for yourself

Sign in, open the browser's developer tools, and look at the cookie. Confirm HttpOnly is ticked and no token is in storage.
