# Web and sign in checklist

Generic questions for a web application and its sign in, drawn from **OWASP ASVS**, the **OWASP Top 10**, the
**OAuth 2.0 Security Best Current Practice**, **OAuth for browser based apps** and the **OWASP cheat sheets**
(Authentication, Session Management, Authorization, Error Handling, Logging, Unvalidated Redirects, JWT).

**Written from memory.** Section numbers and edition years are left out on purpose because they were not checked.
Before you rely on an item, fetch the current source from owasp.org (or the RFC), and write the edition and the
exact reference here.

This file is generic: it says nothing about one project. A project records which items it adopts, and what it accepts
for now, in its own overlay (`docs/standards/security-checklist.md` in this repo).

Each item is a question put to a use case. "Where" says which level of the spec should answer it.

| ID | Question | Where | Source |
|---|---|---|---|
| WEB-1 | Is every request checked on the server, deny by default, whatever the screen hides? | criteria, flow | Top 10 A01 Broken Access Control; ASVS access control |
| WEB-2 | Does a person who may not see something get the same answer as for something that does not exist? | criteria | ASVS access control; Authorization cheat sheet |
| WEB-3 | Is the identity the issuer plus the subject, and never an email or a name? | ontology, flow | OpenID Connect Core |
| WEB-4 | Is the token checked for signature, expiry, issuer and audience, with an allowed list of algorithms? | flow, criteria | OAuth 2.0 Security BCP; JWT cheat sheet |
| WEB-5 | Does the sign in bind state to the browser that started it, make it single use and short lived, and use PKCE and a nonce? | flow, design | OAuth 2.0 Security BCP |
| WEB-6 | Is a new session id issued at sign in, the old one ended, and the id never put where a script or a link can read it? | flow, design | ASVS session management; Session Management cheat sheet |
| WEB-7 | Does the browser never hold a token, a secret or a role it could change? | design | OAuth for browser-based apps BCP; ASVS |
| WEB-8 | Is every redirect target checked against an allowed list or a relative path? | flow, criteria | Unvalidated Redirects cheat sheet |
| WEB-9 | Does a failure give a generic message, log the detail on the server, and never fall back to a weaker path? | flow, criteria | Error Handling cheat sheet; ASVS error handling |
| WEB-10 | Before sign in, does the answer not reveal whether an account exists? | flow | Authentication cheat sheet |
| WEB-11 | Is every security relevant event written to an audit trail with who, what and why, and no secret in it? | flow, criteria | Top 10 A09; Logging cheat sheet |
| WEB-12 | Does an account change that grants power need a reason, an authorised actor and an audit entry? | flow, criteria | Top 10 A01; ASVS |
| WEB-13 | Is a privilege never granted from an unverified claim (for example an unverified email)? | flow, rules | OAuth BCP; "nOAuth" class of attack |
| WEB-14 | Where two systems hold the same fact (Keycloak and our database), is the order of changes and the failure case defined, and does it fail closed? | flow, design | Fail securely; ASVS |
| WEB-15 | Is anything that is accepted for now (a skipped check, a missing rate limit) written down as an accepted risk with the reason? | decisions | Risk acceptance |
