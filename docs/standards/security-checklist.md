# Security checklist

The list `vbench-security-reviewer` checks a use case and its diagrams against. It is a **starting list written from
memory** of OWASP ASVS, the OWASP Top 10, the OAuth 2.0 Security Best Current Practice and the OWASP cheat sheets.
Section numbers are left out on purpose, because they were not checked. Before you rely on an item, look up the
source named in its last column and add the exact reference here. Add an item when a decision adopts a rule, and
say which decision.

Each item is a question the reviewer asks of a use case. "Where" says which level of the spec should answer it.

| ID | Question | Where | Source |
|---|---|---|---|
| SEC-1 | Is every request checked on the server, deny by default, whatever the screen hides? | criteria, flow | Top 10 A01 Broken Access Control; ASVS access control |
| SEC-2 | Does a person who may not see something get the same answer as for something that does not exist? | criteria | ASVS access control; Authorization cheat sheet |
| SEC-3 | Is the identity the issuer plus the subject, and never an email or a name? | ontology, flow | OpenID Connect Core |
| SEC-4 | Is the token checked for signature, expiry, issuer and audience, with an allowed list of algorithms? | flow, criteria | OAuth 2.0 Security BCP; JWT cheat sheet |
| SEC-5 | Does the sign in bind state to the browser that started it, make it single use and short lived, and use PKCE and a nonce? | flow, design | OAuth 2.0 Security BCP |
| SEC-6 | Is a new session id issued at sign in, the old one ended, and the id never put where a script or a link can read it? | flow, design | ASVS session management; Session Management cheat sheet |
| SEC-7 | Does the browser never hold a token, a secret or a role it could change? | design | OAuth for browser-based apps BCP; ASVS |
| SEC-8 | Is every redirect target checked against an allowed list or a relative path? | flow, criteria | Unvalidated Redirects cheat sheet |
| SEC-9 | Does a failure give a generic message, log the detail on the server, and never fall back to a weaker path? | flow, criteria | Error Handling cheat sheet; ASVS error handling |
| SEC-10 | Before sign in, does the answer not reveal whether an account exists? | flow | Authentication cheat sheet |
| SEC-11 | Is every security relevant event written to an audit trail with who, what and why, and no secret in it? | flow, criteria | Top 10 A09; Logging cheat sheet |
| SEC-12 | Does an account change that grants power need a reason, an authorised actor and an audit entry? | flow, criteria | Top 10 A01; ASVS |
| SEC-13 | Is a privilege never granted from an unverified claim (for example an unverified email)? | flow, rules | OAuth BCP; "nOAuth" class of attack |
| SEC-14 | Where two systems hold the same fact (Keycloak and our database), is the order of changes and the failure case defined, and does it fail closed? | flow, design | Fail securely; ASVS |
| SEC-15 | Is anything that is accepted for now (a skipped check, a missing rate limit) written down as an accepted risk with the reason? | decisions | Risk acceptance |

## Accepted for now

- **Email verification is off** (decision 10): the product is deployed inside the corporate network. This accepts a
  risk under SEC-13 and SEC-10. Revisit it with UC-A7 or before the product is reachable from outside the network.
