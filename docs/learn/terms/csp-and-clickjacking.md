---
term: CSP and clickjacking
say: A content security policy tells the browser what a page may do. We use it first to stop other sites framing ours.
aliases: [CSP, Content-Security-Policy, clickjacking, frame-ancestors, X-Frame-Options]
code:
  - apps/web/next.config.ts :: frame-ancestors
  - apps/api/app/infrastructure/security_headers.py :: frame-ancestors
check: What could an attacker do with our admin page if another site could frame it?
---

## In one line

A response header, `Content-Security-Policy`, lists what the browser may allow. Ours says `frame-ancestors 'none'`: no other site may put our pages in a frame.

## Why we need it

Clickjacking hides our real page in an invisible frame on a fake page and tricks a signed-in person into clicking a button they cannot see, for example "approve". Forbidding frames stops it. We also forbid other base addresses and plugins, and set `X-Frame-Options: DENY`, the older header for the same job. `frame-ancestors` only controls framing: it does not stop XSS (injected script). We do not yet restrict scripts: that needs a fresh random value (a CSP nonce, not the OIDC nonce of sign in) on every request and care with Next's own scripts, so it is the next step (NFR-6, AC-96).

## In our code

The web app sets it in `next.config.ts` for every path, and the API in `security_headers.py` for every answer, refusals included.

## Look for yourself

Run `curl -I http://localhost:3000/` and find the `content-security-policy` line.
