# Web security checks (after the OWASP Web Security Testing Guide)

The checks the security tester can run against the live stack, as data. One row is one check: what to try, what
"held" looks like, how it is seen, and the reviewer item and standard it comes from. Add a row to add a check; the agent
reads this file and invents nothing it does not list (it may add a finding "outside the list", marked as such).

**Written from memory.** The category codes (CONF, IDNT, ATHN, ATHZ, SESS, INPV, ERRH, CRYP, BUSL, CLNT) follow the
WSTG's own groups, but section numbers are left out because they were not checked. Before you rely on a row, fetch
the current guide from owasp.org and write the edition here. The WEB- ids point at
`.claude/skills/_vbench/standards/security/web.md`, the API- ids at `api.md`.

**How** is `live` (a request to the running stack), `code` (read the source) or `both`.

| ID | Try | Held when | How | Reviewer item |
|---|---|---|---|---|
| SEC-CONF-1 | Read the response headers of a page and of the API. | A `Content-Security-Policy`, `X-Frame-Options` or `frame-ancestors`, `X-Content-Type-Options: nosniff` and a `Referrer-Policy` are present. | live | WEB-7; ASVS config |
| SEC-CONF-2 | Look for `X-Powered-By`, `Server` and version strings. | None names the framework or its version. | live | ASVS config |
| SEC-CONF-3 | Ask for `/docs`, `/openapi.json`, `/health` and common debug paths without signing in. | Anything that lists routes or internals is off or needs a sign in in a deployed setting; say which are open in development. | live | API-8 |
| SEC-CONF-4 | Send a cross-origin request with an `Origin` header and read the CORS answer. | No wildcard with credentials; only the known origin is allowed. | live | API-8 |
| SEC-IDNT-1 | Ask for something that exists and something that does not, as a person who may not see it. | Both answers are the same. | live | WEB-2 |
| SEC-ATHN-1 | Sign in with a wrong password and with an unknown email. | The same generic failure for both; no hint which one was wrong. | live | WEB-10 |
| SEC-ATHN-2 | Call a protected route with no token, an expired one, one signed with another key and one with `alg: none`. | Each is 401 and nothing is created. | live | WEB-4 |
| SEC-ATHN-3 | Start a sign in, then replay the `state` and `code` after they were used, and with a different browser. | The second use is refused and no session is made. | live | WEB-5 |
| SEC-ATHN-4 | Give the sign in a return address on another site, a protocol-relative one and a `javascript:` one. | The person lands on a page of ours every time. | live | WEB-8 |
| SEC-ATHZ-1 | As an ordinary person, call every administrator route. | Each is 403 and nothing changes. | live | WEB-1 |
| SEC-ATHZ-2 | As person A, ask for person B's project or account by id. | The answer is the same as for something that does not exist. | live | WEB-2 |
| SEC-ATHZ-3 | Use a valid token of a deactivated account. | Refused at once, because the account is read on every request. | live | WEB-14 |
| SEC-ATHZ-4 | Ask an admin route to change the role to a value outside the list, or to a person that does not exist. | Refused with a clear, generic answer; no partial change. | live | WEB-12 |
| SEC-SESS-1 | Read the `Set-Cookie` of the session cookie. | `HttpOnly`, `SameSite`, and `Secure` whenever the site is served over HTTPS; the value is not a token. | live | WEB-6, WEB-7 |
| SEC-SESS-2 | Sign out, then reuse the old cookie. | The old cookie no longer works. | live | WEB-6 |
| SEC-SESS-3 | Sign in twice; reuse the first session id. | A new id is issued at sign in and the earlier session ends where the use case says so. | live | WEB-6 |
| SEC-SESS-4 | Make a state-changing request without the cookie's site context (a forged cross-site POST). | Refused, by `SameSite`, an origin check or a token. | live | WEB-1 |
| SEC-INPV-1 | Put markup (`<script>`) in every free-text field (name, reason, project title) and read it back. | It is shown as text, never run, and stored as typed. | live | ASVS validation |
| SEC-INPV-2 | Send an oversized body, a wrong content type and malformed JSON. | A clean 4xx, no stack trace, no crash. | live | API-4 |
| SEC-INPV-3 | Put quotes and SQL fragments in ids and search fields. | The answer is the same as for a plain value; no database error. | live | ASVS validation |
| SEC-ERRH-1 | Provoke a 404, a 405, a 422 and a 500 (a bad id, a wrong method). | No stack trace, path, query or version appears in the body. | live | WEB-9 |
| SEC-ERRH-2 | Read the API and web logs after a sign in and a refusal. | The event is logged with who and what, and no token, password or code is in the line. | both | WEB-11 |
| SEC-ERRH-3 | Search the web source for `console.*` and the API for `print` and logs that name a secret. | Nothing writes a token, a cookie or a person's data; server errors name the event, not the payload. | code | WEB-11 |
| SEC-CRYP-1 | Check the token's signing algorithm and key source. | An allowed list; no `none`; keys come from the issuer's published set. | both | WEB-4 |
| SEC-CRYP-2 | Check how the site is served in the deployed setting. | TLS only, HSTS, and the `Secure` cookie flag on. (In plain-HTTP development, report it as "not testable here".) | both | WEB-7 |
| SEC-BUSL-1 | Approve an already approved account; reinstate an active one; deactivate the last administrator. | Each is refused or does nothing, and nothing is half done. | live | WEB-14 |
| SEC-BUSL-2 | Send the same change twice at once. | One wins, the other is refused; no duplicate audit entry. | live | WEB-14 |
| SEC-CLNT-1 | Search the web source for `localStorage`, `sessionStorage`, `document.cookie` and `dangerouslySetInnerHTML`. | None holds a token or secret; none renders unescaped input. | code | WEB-7 |
| SEC-CLNT-2 | Check what reaches the browser: page source, `__NEXT_DATA__`, API responses. | No token, no secret, no field the person should not see. | live | WEB-7 |

## Boundaries

Everything here is a request to the local stack with the development accounts. No flooding and no password
guessing beyond a few tries: rate limiting is a decision about accepted risk, not something to test by force.
