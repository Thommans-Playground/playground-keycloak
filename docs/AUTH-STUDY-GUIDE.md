# How sign-in works here: a study guide

Read this with the app running. Every claim points at a file you can open or a command you can run. By the end you should be able to explain the whole mechanism without notes, and know what to check before you deploy it.

**How to use it.** Start with [0.0](#00-the-short-version-and-the-words-you-need): the whole story in four steps and the words it uses. Then read the rest of Part 0 for the picture, with every value shown, and Part 1 once for the ideas. Then run the app (Part 2) and follow Part 3 with the code open next to it. Part 6 is a set of experiments: do them, because seeing the real values is what makes this stick. Part 8 is the pre-deploy checklist. For `state`, `nonce` and PKCE on their own, with the attack each one stops drawn out, see [state, nonce and PKCE](study/state-nonce-pkce.md).

**You will know:** what each of code, access token, ID token, refresh token, session cookie, `state`, `nonce` and PKCE is for, who creates it, who holds it, and what breaks without it.

**One numbering.** The sign in is numbered once, in [0.3](#03-one-sign-in-numbered), steps 1 to 18. Everywhere else, "step 10" means that step.

---

## Contents

0. [The map](#0-the-map), with [the short version](#00-the-short-version-and-the-words-you-need) and [one sign in in 18 numbered steps](#03-one-sign-in-numbered) with the data at each
1. [The theory, in small pieces](#1-the-theory-in-small-pieces)
2. [Run it and look around](#2-run-it-and-look-around)
3. [The code, one flow at a time](#3-the-code-one-flow-at-a-time), ending with [Flow F: the data after sign in](#flow-f-the-data-after-sign-in)
4. [Keycloak, the other half](#4-keycloak-the-other-half)
5. [What lives where, and what an attacker gets](#5-what-lives-where-and-what-an-attacker-gets)
6. [Experiments](#6-experiments)
7. [When it breaks](#7-when-it-breaks)
8. [Before you deploy](#8-before-you-deploy)
9. [Test yourself](#9-test-yourself)
10. [Glossary](#10-glossary)

---

## 0. The map

This part gives you the whole picture: the short version and its words (0.0), who the parties are (0.1), which of them talk and what each line may carry (0.2), one sign in as numbered steps with the data at every step (0.3), where the data ends up (0.4), and how two systems agree on one person (0.5). Part 3 walks the same steps through the code.

### 0.0 The short version, and the words you need

Sign in, in four steps:

1. Next.js sends Maya's browser to **Keycloak** to type her password, because Next.js should never handle passwords.
2. Keycloak sends the browser back with a **code**: a one-use ticket. It does not send the tokens this way, because the trip back is through the browser's address bar, which is public.
3. Next.js hands the code to Keycloak directly, server to server, and gets the **tokens**.
4. Next.js keeps the tokens itself and gives the browser only a **cookie** holding a random id.

Three random values, made at step 1, each add one check to that story:

- **`state`** proves the trip back belongs to the trip out. Checked at step 2.
- **PKCE** proves whoever hands in the code is whoever started the sign in. Checked at step 3.
- **`nonce`** proves the tokens were made for this sign in. Checked after step 3.

Everything else in this guide is one of those four steps in close-up. The words you meet first, each explained properly later:

| Word | In one line | More in |
|---|---|---|
| Keycloak | the server that checks passwords and signs tokens. Our *identity provider* | 0.1, Part 4 |
| BFF | "backend for frontend": the Next.js server, which holds the tokens so the browser never does | 1.11 |
| code (authorization code) | a one-use ticket, valid about a minute, swapped for tokens | 1.4 |
| front channel, back channel | the browser's address bar (public), and a direct server to server call (private) | 1.4 |
| access token | proof of who you are, sent to the API. Lives 5 minutes | 1.9 |
| ID token | Keycloak's note to Next.js: who just signed in | 1.9 |
| refresh token | used to get a new access token without the password | 1.9 |
| JWT | the format of a token: readable by anyone, signed so nobody can forge it | 1.9 |
| `sub` | Keycloak's id for a person, the same forever. Our link to their account | 0.5 |
| login attempt | the server's record of one sign in in progress, holding `state`, `nonce` and the PKCE verifier | 1.8 |
| session | the server's record of a signed-in person, holding the tokens. The cookie holds its id | 1.10 |
| redirect (`302`, `303`, `307`) | a reply that says "go to this other address". The browser follows it by itself | 0.3 |

### 0.1 Four parties, one rule

```mermaid
flowchart LR
    B["Browser<br/>the person"]
    W["Next.js server<br/>apps/web<br/>runs sign-in, holds tokens"]
    K["Keycloak<br/>checks passwords, signs tokens"]
    A["API<br/>apps/api<br/>decides what you may do"]
    D[("API database<br/>accounts, roles, audit")]

    B -->|"cookie only"| W
    B <-->|"sign-in page"| K
    W <-->|"code for tokens, refresh"| K
    W -->|"Bearer access token"| A
    A -->|"public keys"| K
    A --> D
```

The one rule that explains the design:

> **Keycloak says who you are. Our API says what you may do.**

| Party | Its job | What it never does |
|---|---|---|
| Browser | Shows pages, carries one cookie for `localhost:3000` | Never holds a token for our API |
| Next.js server (the BFF) | Runs the sign in, keeps the tokens in its memory, forwards calls to the API | Never sees the password |
| Keycloak | Checks the password, signs tokens that say who you are | Knows nothing about roles or status in this product |
| API and its database | Checks the token's signature, then reads your account for role and status | Never sees the password or the cookie |

The API trusts Keycloak's signature for *who*, then looks you up in its own database for *what*. Part 1.11 explains why the browser holds a cookie and not a token.

### 0.2 Three conversations

If you have used Singpass, you know this shape already: the government site sends you to Singpass, you log in on Singpass's page, and Singpass sends you back. The government site never sees your Singpass password. Here, Playground is the government site and Keycloak is Singpass.

```mermaid
flowchart LR
    B["Browser<br/>Maya's laptop"]
    N["Next.js server<br/>the BFF"]
    K["Keycloak<br/>the identity provider"]
    B <-->|"pages, one cookie"| N
    B <-->|"the sign in page only"| K
    N <-->|"server to server:<br/>code swapped for tokens"| K
```

How to read it: three conversations.
- **Browser and Keycloak** meet only on the sign in page. Maya types her password there, never on a Playground page.
- **Browser and Next.js server** exchange pages and one cookie. That is all.
- **Next.js server and Keycloak** talk directly. The browser never sees this line, and the **tokens travel only on it**.

Add the API and you have every line in the system. What each line may carry, and what it must never carry:

| Line | Carries | Never carries |
|---|---|---|
| Browser and Keycloak (`localhost:8080`) | the sign in page, the password, the code on its way back, Keycloak's own cookies | our tokens |
| Browser and Next.js (`localhost:3000`) | pages, the `playground_login` then `playground_session` cookie, the code passed through | the password, any token |
| Next.js and Keycloak (back channel) | the code, the PKCE verifier, the client secret, the tokens, refreshes | the password |
| Next.js to API | the access token, the request | the ID token, the refresh token, the cookie |
| API to Keycloak | requests for the public keys, and admin calls made with the API's own service account (1.12) | Maya's tokens |

The password crosses one line. The tokens cross two, and the browser is on neither of them.

### 0.3 One sign in, numbered

Maya opens the dashboard for the first time. Here is everything that happens until she sees "Waiting for approval": 18 numbered messages, and the three checks (`state`, PKCE, `nonce`) as notes.

```mermaid
sequenceDiagram
    autonumber
    actor B as Browser
    participant W as Next.js server
    participant K as Keycloak
    participant A as API
    participant D as API database
    B->>W: GET /dashboard, no cookie
    W-->>B: 307 to /auth/login
    B->>W: GET /auth/login
    W-->>B: 307 to Keycloak
    B->>K: GET /auth
    K-->>B: the sign in page
    B->>K: POST username and password
    K-->>B: 302 to /auth/callback with code
    B->>W: GET /auth/callback
    Note over W: CHECK state
    W->>K: POST /token with code and verifier
    Note over K: CHECK PKCE
    K-->>W: access, ID and refresh tokens
    Note over W: CHECK nonce
    W-->>B: 307 to /dashboard, session cookie
    B->>W: GET /dashboard with cookie
    W->>A: GET /me with access token
    A->>K: GET /certs, the public keys
    A->>D: find or create the account
    A-->>W: the account
    W-->>B: the page
```

A solid arrow is a request, a dashed arrow its answer. The steps fall into four phases:

| Steps | Phase | In one line |
|---|---|---|
| 1 to 4 | Prepare | Next.js makes `state`, `nonce` and a PKCE pair, saves them, and sends Maya to Keycloak |
| 5 to 8 | Prove who she is | Maya signs in at Keycloak and comes back with a one-time code |
| 9 to 12 | Swap | Next.js swaps the code for tokens and gives Maya a session cookie |
| 13 to 18 | First page | The API checks the token and finds (here, creates) her account |

Below, each step shows what is sent, in the shape it really has. `…` means cut short; URLs are split one parameter per line so you can read them.

**About the values.** The shapes are real: the Keycloak user, the token claims and the redirects were read from the running stack, and the records match the types in the code. The random values are made up but fit together: the same `state` appears everywhere it should, and the PKCE challenge really is the hash of the verifier shown. Times are UTC, on 17 Nov 2026. The cast, so you can follow the ids:

| Name | Value | Made by |
|---|---|---|
| Maya's Keycloak id (`sub`) | `64b93477-984d-439f-a60c-a61cc1489a93` | Keycloak, when her user was created |
| login attempt id | `BdDMr8vGftiANiN1aXnYHl2LXeOOV4c3B4WXrFQsiU8` | Next.js, at `/auth/login` |
| `state` | `LxS312w3QNd3pdlJ3YgJwJlf6B_w0-HNzzH8wjG6ZAM` | Next.js |
| `nonce` | `-byilA98fUxc1_dRkK6ytNB7SHjFrmarPpbcr1_4xEM` | Next.js |
| PKCE verifier | `V-QRS7wGCAooYIQhdabZYFyzGxcTqVpq9wtag334Lo4` | Next.js, kept until step 10 |
| PKCE challenge | `otVZCOO644o2mTBvbqW8Wew4tLsPEGsu1Arx_CsvGWY` | SHA-256 of the verifier, base64url |
| session id | `qzRp2pmHUgXwm6PKAT9Ohvm-2gv_J513URogcTDR1jA` | Next.js, at `/auth/callback` |
| Maya's account id | `0c1f6d2e-7a43-4b8e-9d51-2f6a8e3b9c07` | the API, at step 16 |

Every id Next.js makes is 32 random bytes in base64url (`newId` in [composition.ts](../apps/web/src/composition.ts)): 43 characters with no meaning inside.

#### Phase 1: Prepare (steps 1 to 4)

**1. Browser → Next.js: ask for the dashboard**

Maya has no cookie yet.

```http
GET /dashboard HTTP/1.1
Host: localhost:3000
```

**2. Next.js → browser: "sign in first"**

[proxy.ts](../apps/web/src/proxy.ts) sees no session cookie and sends her to the sign in route, remembering where she was going. `307` is a redirect: the browser goes to the `Location` address by itself.

```http
HTTP/1.1 307 Temporary Redirect
Location: http://localhost:3000/auth/login?returnTo=/dashboard
```

**3. Browser → Next.js: start the sign in**

Next.js makes three random values and saves them in memory, in a **login attempt** row ([login-attempt.ts](../apps/web/src/domain/login-attempt.ts), kept in a `Map` in [in-memory-stores.ts](../apps/web/src/adapters/in-memory-stores.ts)). The challenge is not saved; it is worked out from the verifier.

```http
GET /auth/login?returnTo=/dashboard HTTP/1.1
Host: localhost:3000
```

```text
attempt store (Next.js memory)
  "BdDMr8vG…" -> {
      state:        "LxS312w3…",
      nonce:        "-byilA98…",
      pkceVerifier: "V-QRS7wG…",      secret: never leaves Next.js until step 10
      returnTo:     "/dashboard",
      startedAt:    1794880401000     01:53:21 in ms since 1970. Dead 10 minutes later
  }

challenge = base64url(SHA-256(verifier)) = "otVZCOO6…"
```

**4. Next.js → browser: go to Keycloak**

`state`, `nonce` and the challenge ride in the URL. The cookie lets Next.js find the attempt row again at step 9.

```http
HTTP/1.1 307 Temporary Redirect
Location: http://localhost:8080/realms/playground/protocol/openid-connect/auth
    ?client_id=playground-web
    &response_type=code
    &redirect_uri=http://localhost:3000/auth/callback
    &scope=openid profile email
    &state=LxS312w3…
    &nonce=-byilA98…
    &code_challenge=otVZCOO6…
    &code_challenge_method=S256
Set-Cookie: playground_login=BdDMr8vG…; Path=/; Max-Age=600; HttpOnly; SameSite=lax
```

| Parameter | For |
|---|---|
| `client_id` | which app is asking |
| `response_type=code` | "send me back a code": the authorization code flow (1.5) |
| `redirect_uri` | where to send the code. Must match the client's setting in Keycloak exactly |
| `scope` | `openid` asks for an ID token. `profile email` put name and email in the tokens |
| `state` | comes back unchanged at step 8, checked by Next.js at step 9 |
| `nonce` | Keycloak copies it into the ID token, checked by Next.js at step 11 |
| `code_challenge` | the hash of the verifier. Keycloak keeps it with the code, checks it at step 10 |
| `code_challenge_method=S256` | how the hash was made: SHA-256 |

Compare the row in step 3 and this URL. `state` and `nonce` are in both. The **verifier is only in the row**, the challenge only in the URL. That is PKCE in two lines.

#### Phase 2: Prove who she is (steps 5 to 8)

**5. Browser → Keycloak: follow the redirect**

Keycloak keeps `state`, `nonce` and the challenge for later.

```http
GET /realms/playground/protocol/openid-connect/auth?client_id=playground-web&…&state=LxS312w3…&nonce=-byilA98…&code_challenge=otVZCOO6… HTTP/1.1
Host: localhost:8080
```

**6. Keycloak → browser: the sign in page**

An HTML form that posts back to Keycloak.

```http
HTTP/1.1 200 OK
Content-Type: text/html

<form method="post" action="http://localhost:8080/realms/playground/login-actions/authenticate?session_code=crEEdYtO…">
  <input name="username"> <input name="password" type="password">
</form>
```

**7. Browser → Keycloak: the password**

The only message in the whole system that carries the password. It goes to Keycloak, never to Next.js.

```http
POST /realms/playground/login-actions/authenticate?session_code=crEEdYtO…&… HTTP/1.1
Host: localhost:8080
Content-Type: application/x-www-form-urlencoded

username=maya%40example.test&password=Maya123%21
```

**8. Keycloak → browser: back to the app, with a code**

The same `state` comes back, plus a one-time `code`. Keycloak also sets its own cookies, so Maya need not type her password again for a while.

```http
HTTP/1.1 302 Found
Location: http://localhost:3000/auth/callback
    ?state=LxS312w3…
    &code=9e2b4c1a-…
    &session_state=6194819b-…
    &iss=http://localhost:8080/realms/playground
Set-Cookie: KEYCLOAK_IDENTITY=eyJhbGci…; …
Set-Cookie: KEYCLOAK_SESSION=AmVhjweV…; …
```

#### Phase 3: Swap (steps 9 to 12)

**9. Browser → Next.js: hand over the code**

The browser carries the attempt cookie along. `SameSite=Lax` allows that, though the redirect came from Keycloak's site (1.10).

```http
GET /auth/callback?state=LxS312w3…&code=9e2b4c1a-…&session_state=…&iss=… HTTP/1.1
Host: localhost:3000
Cookie: playground_login=BdDMr8vG…
```

> **CHECK `state`** (Next.js). The cookie finds the attempt row, which is taken out of memory so it can be used only once.
>
> ```text
> state in the URL = "LxS312w3…"
> state in the row = "LxS312w3…"   ✔ same sign in that left at step 4
> ```

**10. Next.js → Keycloak: swap the code for tokens**

Server to server: the browser never sees this. The **verifier** leaves Next.js for the first and only time.

```http
POST /realms/playground/protocol/openid-connect/token HTTP/1.1
Host: keycloak:8080
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=9e2b4c1a-…
&redirect_uri=http://localhost:3000/auth/callback
&code_verifier=V-QRS7wG…
&client_id=playground-web
&client_secret=playground-web-dev-secret
```

> **CHECK PKCE** (Keycloak).
>
> ```text
> base64url(SHA-256("V-QRS7wG…")) = "otVZCOO6…"
> challenge kept at step 5        = "otVZCOO6…"   ✔ the one swapping is the one who asked
> ```

**11. Keycloak → Next.js: three tokens**

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token":  "eyJhbGciOiJSUzI1NiIs…",
  "id_token":      "eyJhbGciOiJSUzI1NiIs…",
  "refresh_token": "eyJhbGciOiJIUzUxMiIs…",
  "token_type":    "Bearer",
  "expires_in":    300,
  "refresh_expires_in": 1800
}
```

`expires_in` is the access token's 5 minutes, `refresh_expires_in` the 30 minute idle limit of Keycloak's session (Part 4). Decoded, the middle of the access token says who Maya is (`sub`) and who the token is for (`aud`). It holds no role and no status: those are the API's. All three tokens are decoded in full in [1.9](#19-tokens).

```json
{
  "iss": "http://localhost:8080/realms/playground",
  "aud": "playground-api",
  "sub": "64b93477-984d-439f-a60c-a61cc1489a93",
  "exp": 1794880728,
  "name": "Maya Rao",
  "email": "maya@example.test"
}
```

> **CHECK `nonce`** (Next.js). The ID token carries the `nonce`, sealed by Keycloak's signature.
>
> ```text
> nonce in the ID token = "-byilA98…"
> nonce in the row      = "-byilA98…"   ✔ this token was made for this sign in
> ```

**12. Next.js → browser: the session cookie**

The tokens go into a **session** row in Next.js memory ([session.ts](../apps/web/src/domain/session.ts), filled in by `toSession` in [keycloak-identity-provider.ts](../apps/web/src/adapters/keycloak-identity-provider.ts)). The attempt row is already gone, taken at step 9. The browser gets only the session row's random id.

```text
session store (Next.js memory)
  "qzRp2pmH…" -> {
      idToken:         "eyJhbGci…",    kept for sign out (Flow D)
      accessToken:     "eyJhbGci…",    sent to the API
      refreshToken:    "eyJhbGci…",    sent to Keycloak only
      accessExpiresAt: 1794880728000   now + expires_in, in ms: 01:58:48
  }
```

```http
HTTP/1.1 307 Temporary Redirect
Location: http://localhost:3000/dashboard
Set-Cookie: playground_session=qzRp2pmH…; Path=/; HttpOnly; SameSite=lax
Set-Cookie: playground_login=; Expires=Thu, 01 Jan 1970 00:00:00 GMT
```

The second `Set-Cookie` deletes the attempt cookie: same name, a date in the past. The session cookie has no `Max-Age`, so it goes when the browser closes. Everything the browser now holds for `localhost:3000` is one line: `playground_session = qzRp2pmH…`.

#### Phase 4: First page (steps 13 to 18)

**13. Browser → Next.js: the dashboard again, now with the cookie**

```http
GET /dashboard HTTP/1.1
Host: localhost:3000
Cookie: playground_session=qzRp2pmH…
```

**14. Next.js → API: the access token**

Next.js finds the session row by the cookie and sends the access token on.

```http
GET /me HTTP/1.1
Host: api:8000
Authorization: Bearer eyJhbGciOiJSUzI1NiIs…
```

**15. API → Keycloak: the public keys**

Only the first time; then they are cached. The token's header names the key that signed it (`kid`, key id), so the API picks that key and checks the signature. Then it checks who issued the token (`iss`), who it is for (`aud`) and when it expires (`exp`). Any failure is a `401`. The checks are in [1.9](#19-tokens).

```http
GET /realms/playground/protocol/openid-connect/certs HTTP/1.1
Host: keycloak:8080
```

```json
{ "keys": [ { "kid": "CdLHpIsQ…", "kty": "RSA", "alg": "RS256", "use": "sig", "n": "vlAq2PODp6Qz…", "e": "AQAB" } ] }
```

**16. API → database: find the account by `sub`, or create it**

From the verified token the API keeps only what it needs, a `Principal` ([auth.py](../apps/api/app/auth.py)):

```text
Principal(identity="64b93477-984d-439f-a60c-a61cc1489a93",
          name="Maya Rao", email="maya@example.test", email_verified=True)
```

Maya is new, so `account_for` ([service.py](../apps/api/app/access/service.py)) creates a pending account and an audit entry. Her email is not in `BOOTSTRAP_ADMIN_EMAILS`, so she starts as a pending user. On every later request this is a read, and it is where role and status are checked.

```sql
SELECT * FROM accounts WHERE identity = '64b93477-…';     -- nothing found

INSERT INTO accounts (id, identity, name, email, role, status, created)
     VALUES ('0c1f6d2e-…', '64b93477-…', 'Maya Rao', 'maya@example.test', 'user', 'pending', '2026-11-17 01:53:49');
INSERT INTO audit_entries (at, actor_id, action, target_id)
     VALUES ('2026-11-17 01:53:49', NULL, 'register', '0c1f6d2e-…');
```

Two ids sit side by side in the account row. `id` is **ours**, made by the API, and is what other tables point at. `identity` is **Keycloak's** `sub`, the link back to the token. An empty `actor_id` means the system did it, not a person.

**17. API → Next.js: the account**

`AccountOut` in [main.py](../apps/api/app/main.py). `identity` is not sent out.

```http
HTTP/1.1 200 OK
Content-Type: application/json

{ "id": "0c1f6d2e-…", "name": "Maya Rao", "email": "maya@example.test", "role": "user", "status": "pending",
  "created": "2026-11-17T01:53:49", "created_by": null }
```

**18. Next.js → browser: the page**

HTML that says "Waiting for approval". No token reaches the browser.

*Hosts:* `keycloak:8080` and `api:8000` are the names inside Docker. With `npm run dev` on your machine they are `localhost:8080` and `localhost:8000`. The issuer in the tokens is always `http://localhost:8080/realms/playground`.

#### The 18 steps in one table

| # | From → to | What travels | Secret? |
|---|---|---|---|
| 1 | Browser → Next.js | `GET /dashboard` | |
| 2 | Next.js → browser | redirect to `/auth/login` | |
| 3 | Browser → Next.js | `GET /auth/login` | `state`, `nonce`, verifier made, kept in memory |
| 4 | Next.js → browser | redirect to Keycloak, attempt cookie | challenge only (a hash) |
| 5 | Browser → Keycloak | `GET /auth` | |
| 6 | Keycloak → browser | sign in page | |
| 7 | Browser → Keycloak | username and password | **the password** |
| 8 | Keycloak → browser | redirect with `code` and `state` | the code |
| 9 | Browser → Next.js | `code` and `state`, attempt cookie | the code. **CHECK `state`** |
| 10 | Next.js → Keycloak | code, verifier, client secret | **verifier, client secret.** **CHECK PKCE** |
| 11 | Keycloak → Next.js | three tokens | **the tokens.** **CHECK `nonce`** |
| 12 | Next.js → browser | session cookie | the session id |
| 13 | Browser → Next.js | `GET /dashboard` with cookie | the session id |
| 14 | Next.js → API | `Authorization: Bearer` | **the access token** |
| 15 | API → Keycloak | `GET /certs` | public keys, not secret |
| 16 | API → database | find or create by `sub` | |
| 17 | API → Next.js | the account | |
| 18 | Next.js → browser | HTML | |

Look at the bold rows: the password only goes browser → Keycloak, and every token stays between servers.

### 0.4 Where the data ends up

After step 18, this is what each place holds, and the ids that tie them together. A dotted line is "points at", not a call.

```mermaid
flowchart LR
    subgraph BR["Browser"]
        C1["localhost:3000<br/>playground_session"]
        C2["localhost:8080<br/>Keycloak's SSO cookies"]
    end
    subgraph NX["Next.js memory"]
        S["session row<br/>access, ID, refresh tokens"]
    end
    subgraph KC["Keycloak database"]
        U["user<br/>id = sub, password hash"]
        KS["Keycloak session<br/>sid"]
    end
    subgraph DB["API database"]
        AC["account<br/>identity = sub<br/>role, status"]
        AU["audit entry<br/>register"]
    end
    C1 -.->|"session id"| S
    C2 -.->|"session"| KS
    S -.->|"sub, sid in the tokens"| U
    AC -.->|"identity = sub"| U
    AU -.->|"target_id"| AC
```

How to read it: start at the browser. Its cookie is only a key to the session row; the tokens in that row carry `sub`, and the account row uses the same `sub` as its `identity`. That one id is how three systems agree they are talking about Maya.

| Place | Holds | Lost if it restarts? |
|---|---|---|
| Browser, `localhost:3000` | `playground_session` (random id) | it goes when the browser closes |
| Browser, `localhost:8080` | Keycloak's own cookies | no, kept by the browser |
| Next.js memory | session row with three tokens (attempt row already gone) | **yes**: everyone signs in again |
| Keycloak database | user, password hash, Keycloak session | no |
| API database | account (`pending`), one audit entry | no |

### 0.5 Two records, one person

Two records describe one person, linked by Keycloak's user id (`sub`), never by email:

| Record | Lives in | Holds |
|---|---|---|
| Keycloak user | Keycloak's database | password, name, email, sessions |
| API account | the API's PostgreSQL | role, status, audit trail |

Why not email? Maya can change her email in Keycloak; her `sub` never changes. Two systems that matched on email would split her in two the day she does.

Before her first sign in, Maya exists in Keycloak only. Her Keycloak user, from the admin API, trimmed (the `id` is her `sub`):

```json
{
  "id": "64b93477-984d-439f-a60c-a61cc1489a93",
  "username": "maya@example.test",
  "firstName": "Maya",
  "lastName": "Rao",
  "email": "maya@example.test",
  "emailVerified": true,
  "enabled": true
}
```

Her password is not in that record. Keycloak keeps a hash of it separately, and no API hands it out. The API's database has **no row for her yet** (step 16 makes it). Its two tables, as PostgreSQL shows them (`\d accounts`, and the model in [sql.py](../apps/api/app/access/adapters/sql.py)):

```text
accounts                                  audit_entries
  id          varchar  primary key          id         integer  primary key, counts up
  identity    varchar  unique  <- the sub   at         timestamp
  name        varchar                       actor_id   varchar  (null = the system)
  email       varchar                       action     varchar
  role        varchar  user | administrator target_id  varchar
  status      varchar  pending | active |   reason     text     (null when none is needed)
                       deactivated
  created     timestamp
  created_by  varchar
```

Notice what is **not** there: no password, no token, no session. Just who (`identity`) and what they may do (`role`, `status`).

> **Your turn.**
> 1. Which step numbers carry Maya's password, and which carry her access token?
> 2. An administrator deactivates Maya at 10:00. Her access token is valid until 10:03. At 10:01 she clicks a button that calls the API. Does she get in? Which step stops her, and with what data?

<details>
<summary>Answers</summary>

1. The password: step 7 only. The access token: step 11 (Keycloak to Next.js) and step 14 (Next.js to the API). Step 12 stores it, but it does not travel to the browser.
2. No. Steps 13 to 15 pass: the cookie finds her session, the token is validly signed, not expired, for `playground-api`. Step 16 stops her: the API reads her account row, `status` is `deactivated`, and it answers `403 account_deactivated`. The token carries no status (look at step 11), so it cannot be what stops her. See [F2](#f2-an-administrator-approves-then-deactivates-her).

</details>


---

## 1. The theory, in small pieces

Thirteen short ideas, each with deeper, drawn-out versions where an idea is easy to get wrong. Each says what the thing is, then why it exists.

### 1.1 Authentication and authorization

- **Authentication** answers *who are you?* A password, a fingerprint, a company login.
- **Authorization** answers *what may you do?* A role, a membership, a permission.

They are different problems, and this app keeps them in different places on purpose. Keycloak authenticates. The API authorizes. If you ever catch yourself putting a business rule in Keycloak, or a password check in the API, stop and re-read the rule above.

### 1.2 Why you do not write sign-in yourself

Passwords, hashing, brute-force limits, password reset, second factors, sessions and single sign-on are a product of their own, and getting them wrong is a security hole. An earlier prototype (MK3) built its own: about 1,500 lines for passwords, two token kinds and a Redis list of live refresh tokens. It also had a real bug: people were logged out when they switched windows, because replacing a refresh token raced with itself. Here Keycloak does all of that, and our code is about 580 lines.

### 1.3 OAuth 2.0 and OpenID Connect, in one paragraph

**OAuth 2.0** is a standard way for one program to be given limited access on behalf of a person, without ever seeing the person's password. **OpenID Connect (OIDC)** sits on top of it and adds *identity*: "this person just logged in, and here is who they are". When people say "sign in with X", they usually mean OIDC.

Four roles appear in the standards. Here is who plays each:

| OAuth role | Meaning | Here |
|---|---|---|
| Resource owner | the person | you |
| Authorization server | issues tokens after checking the person | Keycloak |
| Client | the app asking for tokens | the Next.js server (`playground-web`) |
| Resource server | the thing that accepts tokens | the API |

### 1.4 Two channels: why a "code" exists at all

This is the idea most people miss, so take your time.

- The **front channel** is the browser's address bar. Anything in a URL can be seen by the person, browser extensions, history and logs. It is public.
- The **back channel** is a direct call from our server to Keycloak. The person's browser is not involved. It can carry secrets.

If Keycloak put the tokens in the redirect URL (the front channel), they would leak. So it hands the browser a **code**: a short-lived, one-use ticket that is useless alone. Our server then takes the code to Keycloak over the back channel and swaps it for the tokens.

```mermaid
flowchart LR
    subgraph front["Front channel: visible to the browser"]
        direction TB
        F1["redirect to Keycloak<br/>with state, nonce, challenge"]
        F2["redirect back<br/>with code and state"]
    end
    subgraph back["Back channel: server to server, private"]
        direction TB
        B1["code + client secret + verifier"]
        B2["tokens"]
    end
    front --> back
```

#### Why a code and not the tokens: the details

Because the redirect back to `/auth/callback` is a URL, and URLs leak. So Keycloak puts the least valuable thing possible in it: a **code** that is

| Property | Why it matters |
|---|---|
| short lived (about 1 minute) | a code found in a log tomorrow is dead |
| single use | a code that was already swapped is dead |
| useless alone | swapping it needs the **client secret**, which only our server has (1.6), and the PKCE verifier (1.7) |

> **Your turn.**
> Someone copies the callback URL, `/auth/callback?code=xyz`, out of Maya's browser history an hour later and opens it. What happens, and which property in the table stops them?

<details>
<summary>Answer</summary>

Nothing useful. The code expired after about a minute, and it was already used once, by our server, when it swapped the code. Two properties stop it: **short lived** and **single use**. Even a fresh code would need the client secret, which never left the server.

</details>

### 1.5 The authorization code flow

This is the name of the flow you followed in [0.3](#03-one-sign-in-numbered), steps 3 to 12: the browser is sent to Keycloak (steps 3 to 7), comes back with a code (step 8), and the server swaps the code for tokens (steps 9 to 12). The name comes from the parameter `response_type=code` at step 4: "send me back an authorization code". The swap is called the *token exchange*, or the *authorization code grant*: a **grant** is any way of getting tokens, and here you get them by handing in a code (`grant_type=authorization_code` at step 10). Everything in this app hangs off this one flow.

### 1.6 Confidential and public clients, and the client secret

A **client** is an app registered in Keycloak. It is *confidential* if it can keep a secret (a server), and *public* if it cannot (a phone app, a browser app, where anyone can read the code). Our `playground-web` client is confidential (**Client authentication on** in the admin console), so at the token exchange it proves itself with a **client secret** as well as the PKCE verifier. The secret lives only in the Next.js server's environment, never in the browser. Being able to be confidential is one more reason the BFF is safer.

The API has its own client, `playground-backend`, with its own secret, for a different job (1.12). Neither server knows the other's secret.

### 1.7 PKCE (say "pixie")

PKCE protects the code. Suppose someone steals the code from the address bar. Without PKCE, they could swap it for tokens. With PKCE:

1. At the start, Next.js makes a random secret, the **verifier**, and keeps it on the server.
2. It sends Keycloak only the **challenge**, which is a hash of the verifier (method `S256`). A hash cannot be reversed.
3. At the exchange it sends the verifier. Keycloak hashes it and compares to the challenge it saw in step 2.

A thief with the code but without the verifier gets nothing. The realm enforces it with `pkce.code.challenge.method: S256`.

#### PKCE: "is the one swapping the code the one who asked?", drawn

```mermaid
flowchart LR
    V["verifier<br/>a long random secret<br/>STAYS on our server"] -->|"SHA-256, then base64url"| C["challenge<br/>its hash<br/>SENT to Keycloak at the start"]
    C --> K["Keycloak remembers<br/>the challenge with the code"]
    V2["at the swap, our server<br/>sends the verifier"] --> CHK{"Keycloak: does<br/>hash(verifier) equal<br/>the challenge?"}
    K --> CHK
    CHK -->|"yes"| OK["tokens"]
    CHK -->|"no"| NO["invalid_grant"]
```

How to read it: a hash works one way. Anyone can see the challenge, but nobody can work back from it to the verifier. Only the party that made the verifier can finish the swap.

> **Your turn.**
> Our server also has a client secret. If the secret already stops strangers from swapping a code, why bother with PKCE as well?

<details>
<summary>Answer</summary>

Defence in depth: two locks, so one mistake is not enough. A client secret is shared by every sign in and lives for months: if it ever leaks (a log, a config file in git), it protects nothing. A PKCE verifier is new for **each** sign in, lives about a minute, and never leaves the server. OAuth 2.1, the next version of the standard, makes PKCE required for every client for this reason.

</details>

### 1.8 `state` and `nonce`

Two more random values made at the start. They stop two different attacks.

- **`state`** ties the return trip to the outgoing trip. When the browser comes back to `/auth/callback`, Next.js checks that `state` matches an attempt *it* started. Otherwise an attacker could trick your browser into completing *their* login on your session (login CSRF).
- **`nonce`** is placed inside the **ID token** by Keycloak. Next.js checks that the token carries the nonce it sent. This proves the token was issued for this very attempt and is not a replay of an older one.

All three values (`state`, `nonce`, verifier) are stored together as a **login attempt** in the Next.js server's memory, under a random id kept in the `playground_login` cookie. The browser holds the id, the server holds the values. The attempt is taken (read and deleted in one go) at the callback, so it is used once, and it expires after 10 minutes.

#### `nonce`: "was this ID token made for this sign in?", drawn

```mermaid
sequenceDiagram
    participant N as Next.js server
    participant K as Keycloak
    N->>N: make nonce = n-NEW, keep it in the attempt
    N-->>K: (through the browser) nonce=n-NEW
    K->>K: person signs in, Keycloak writes<br/>nonce n-NEW into the ID token, then signs it
    K-->>N: ID token (at the swap, step 11)
    N->>N: nonce in the token = nonce in the attempt?<br/>yes: go on. no: refuse
```

How to read it: an old or stolen ID token carries some other nonce, and nobody can change it, because Keycloak's signature covers the whole token. The attacks that each of the three values stops are drawn in [state, nonce and PKCE](study/state-nonce-pkce.md).

#### `state`: "is this the sign in I started?", drawn

Without `state`, an attacker could start a sign in with **their own** account, stop before the callback, and trick Maya into opening their callback link. Maya would then be signed in to Playground **as the attacker**, and anything she uploads goes into the attacker's account. This is called **login CSRF** (cross-site request forgery).

```mermaid
sequenceDiagram
    autonumber
    participant N as Next.js server
    actor B as Browser
    participant K as Keycloak
    N->>N: make state = r4nd0m, remember it for this attempt
    N-->>B: go to Keycloak with state=r4nd0m
    B->>K: sign in
    K-->>B: back to /auth/callback?code=...&state=r4nd0m
    B->>N: callback with state=r4nd0m
    N->>N: same state as the attempt I started? yes: go on. no: refuse
```

How to read it: Keycloak hands `state` back unchanged. An attacker's link carries a `state` our server never made for this browser, so it is refused.

#### The three, side by side

| | `state` | `nonce` | PKCE |
|---|---|---|---|
| Stops | being signed in to someone else's account (login CSRF) | an old or stolen ID token being passed off as this one (replay) | a stolen code being swapped |
| Where it travels | to Keycloak and back, in the URL | out in the URL, back inside the signed ID token | the challenge goes out, the verifier only in the back channel |
| Checked at | step 9 | step 11 | step 10 |
| Who checks | our server | our server | Keycloak |
| In our code | `randomState()`, `expectedState` | `randomNonce()`, `expectedNonce` | `randomPKCECodeVerifier()`, `calculatePKCECodeChallenge()`, `pkceCodeVerifier` |

All three live in the **login attempt**, which our server stores until the browser comes back, and uses **once**. The code is in [keycloak-identity-provider.ts](../apps/web/src/adapters/keycloak-identity-provider.ts).


### 1.9 Tokens

Keycloak returns three tokens. They are different things.

| | Access token | ID token | Refresh token |
|---|---|---|---|
| Question it answers | what may the holder ask the API for? | who just logged in? | can I have a new access token? |
| Sent to | the API, on every request | nobody (kept for logout) | Keycloak only |
| Lifetime here | **5 minutes** | short | up to the Keycloak session: **30 min idle, 8 h max** |
| Format | JWT | JWT | opaque to us |

**What a JWT is.** Three base64 parts joined by dots: `header.payload.signature`.

```mermaid
flowchart LR
    H["header<br/>alg RS256, kid"] --- P["payload (claims)<br/>iss, sub, aud, exp, email, name"] --- S["signature<br/>made with Keycloak's PRIVATE key"]
```

The payload is **not secret**, anyone can decode it. What makes it trustworthy is the **signature**. Keycloak signs with a private key it never shares. The API fetches Keycloak's **public keys** (the JWKS, a list of keys at a known URL) and verifies the signature. If one byte of the payload changed, verification fails. Anyone can read a token, nobody can forge one.

**The claims the API checks** ([auth.py](../apps/api/app/auth.py)):

| Claim | Meaning | The API requires |
|---|---|---|
| `iss` | issuer: who signed it | exactly `http://localhost:8080/realms/playground` |
| `aud` | audience: who it is meant for | `playground-api` (a Keycloak mapper adds it) |
| `exp` | expiry time | not in the past |
| `sub` | subject: the user's id, stable forever | present. This becomes `identity`, the link to the account |
| `email` | the person's email | present (the API refuses tokens without one) |

**Maya's three tokens, decoded.** These are the tokens from step 11 of [0.3](#03-one-sign-in-numbered), generated by Keycloak for her (experiment 6 shows how).

Access token, for the API:

```jsonc
{
  "exp": 1794880728,                         // 01:58:48, five minutes after iat
  "iat": 1794880428,                         // 01:53:48, issued at
  "jti": "onrtna:ce74d9f9-f26d-9c5d-d7b6-b53f55d9671c",  // this token's own id
  "iss": "http://localhost:8080/realms/playground",
  "aud": "playground-api",                   // added by the audience mapper (Part 4)
  "sub": "64b93477-984d-439f-a60c-a61cc1489a93",
  "typ": "Bearer",
  "azp": "playground-web",                   // the client that asked for it
  "sid": "6194819b-7ca0-cc4b-9f59-47b2b88fedcc",  // Keycloak's session
  "acr": "1",                                // how strongly she signed in: 1 = password
  "scope": "openid email profile",
  "email_verified": true,
  "name": "Maya Rao",
  "preferred_username": "maya@example.test",
  "given_name": "Maya",
  "family_name": "Rao",
  "email": "maya@example.test"
}
```

ID token, for Next.js, about the sign in itself:

```jsonc
{
  "exp": 1794880728,
  "iat": 1794880428,
  "iss": "http://localhost:8080/realms/playground",
  "aud": "playground-web",                   // for our web app, not the API
  "sub": "64b93477-984d-439f-a60c-a61cc1489a93",
  "typ": "ID",
  "azp": "playground-web",
  "sid": "6194819b-7ca0-cc4b-9f59-47b2b88fedcc",
  "nonce": "-byilA98fUxc1_dRkK6ytNB7SHjFrmarPpbcr1_4xEM",  // the one from the attempt row
  "at_hash": "kT3m…",                        // ties it to the access token issued with it
  "email_verified": true,
  "name": "Maya Rao",
  "email": "maya@example.test"
}
```

Refresh token, for Keycloak only. Keycloak happens to make it a JWT too (signed `HS512` with a key only Keycloak has), but our code treats it as an opaque string and never decodes it. Its payload is short: `typ: "Refresh"`, `aud` is the realm itself, the same `sub` and `sid`, and an `exp` 30 minutes out.

Compare the access token and the ID token. Same person (`sub`), same Keycloak session (`sid`), but a **different `aud`**: each says who it is for. And look for what is missing from both: no role, no status. Those are the API's (1.1).

**Why the access token is so short.** A JWT cannot be recalled once issued: the API checks only the signature and expiry. A 5 minute life limits how long a stolen or stale one is useful. The refresh token is how the person stays signed in without typing the password every 5 minutes.

**Refresh tokens can rotate, and here they do not.** Keycloak has a realm setting, *Revoke Refresh Token*. When it is **on**, every refresh retires the old refresh token and issues a new one, and using an old one a second time looks like theft, so Keycloak can end the session. In this realm it is **off** (`revokeRefreshToken = false`, checked against the running realm), so the same refresh token keeps working until the Keycloak session ends. The code is written to be safe either way: it refreshes one at a time per session (Part 3, Flow B), so you can switch rotation on for production without a rewrite. Turning it on is a good hardening step (Part 8).

### 1.10 Sessions and cookies

#### Cookies, from the ground up

HTTP, the language browsers and servers speak, **forgets everything between requests**. Each request arrives as if from a stranger. A **cookie** fixes that: it's a small note the server asks the browser to keep and **show again on every later request** to that site.

```mermaid
sequenceDiagram
    participant B as Browser
    participant S as Server (localhost:3000)
    B->>S: GET /auth/callback?code=...
    S-->>B: response + Set-Cookie: playground_session=kq3Xv9, HttpOnly, SameSite=Lax
    Note over B: the browser stores the note for localhost:3000
    B->>S: GET /dashboard + Cookie: playground_session=kq3Xv9
    B->>S: GET /dashboard/reports + Cookie: playground_session=kq3Xv9
```

How to read it: the server sets the cookie once, with `Set-Cookie`. From then on the **browser attaches it by itself** to every request to that site, with `Cookie:`. Nobody's code has to remember to send it.

The settings on a cookie (`HttpOnly`, `SameSite` and the rest) are rules **the browser** enforces. They are listed at the end of this section.

#### Sessions: the cookie is a ticket, the server keeps the coat

A cookie is small (about 4 KB at most) and lives on someone else's computer. So you don't put valuable things in it. You put a **random ticket number** in the cookie and keep the valuables on the server, in a table:

```mermaid
flowchart LR
    C["cookie in the browser<br/>playground_session = kq3Xv9"] -->|"looked up in"| T["session store on the server<br/>kq3Xv9 -> Maya: her 3 tokens<br/>7Hd2pQ -> Ravi: his 3 tokens"]
```

That pair, a ticket in the browser and a row on the server, is a **session**. The **session id** is the ticket number. It's random, holds no information, and only means something to the server that made it.

#### Two sessions with similar names

- **Keycloak's session** (the SSO session). Keycloak sets its own cookies on `localhost:8080` after you type your password. That is why signing in a second time often skips the password: Keycloak still remembers you. This is *single sign-on* (SSO).
- **Our session.** The Next.js server keeps your tokens in memory under a random id, and sets that id as the `playground_session` cookie on `localhost:3000`.

Signing out has to end both (Flow D).

#### Two cookies, one after the other

```mermaid
stateDiagram-v2
    [*] --> Guest
    Guest --> Attempting: /auth/login sets playground_login (10 min)
    Attempting --> SignedIn: /auth/callback sets playground_session, deletes playground_login
    Attempting --> Guest: attempt expired, used, or failed
    SignedIn --> Guest: sign out (UC-A11) or refresh refused (UC-A14)
```

How to read it: the browser carries at most one small cookie at each moment. `playground_login` holds the id of the sign in attempt, for the trip to Keycloak and back. `playground_session` holds the id of the session afterwards. Both are random strings that mean nothing outside our server.

#### The cookie settings, and why `SameSite=Lax`

Both cookies get the same settings, from `cookieOptions` in [lib/auth/session.ts](../apps/web/src/lib/auth/session.ts):

| Setting | The browser's rule | Why we set it |
|---|---|---|
| `HttpOnly` | JavaScript in the page cannot read the cookie, but the browser still sends it | a malicious script (XSS) cannot steal it (1.11) |
| `Secure` | sent only over https | nobody on the network can read it. Turns on by itself when `APP_URL` starts with `https://`, so it is off on localhost |
| `SameSite=Lax` | sent when the person **navigates** to our site, even from another site. Not sent on another site's background requests (forms posted, images, frames) | the callback is a navigation **from Keycloak's site**, so it needs the cookie. Background requests from other sites, which cross-site request forgery (CSRF) uses, get no cookie |
| `Path=/` | sent for every page | the pages and the auth routes both need it |
| `Max-Age` | deleted after this many seconds. Without it, the cookie goes when the browser closes | `playground_login` has 600 (10 minutes). `playground_session` has none |

```mermaid
flowchart LR
    KC["Keycloak's page<br/>localhost:8080"] -->|"redirect: a top-level navigation<br/>to localhost:3000/auth/callback"| CB["our callback"]
    S{"SameSite?"}
    CB --- S
    S -->|"Strict: cookie NOT sent<br/>(it came from another site)"| F["no attempt found:<br/>every sign in fails"]
    S -->|"Lax: cookie sent<br/>(it is a navigation)"| W["attempt found:<br/>sign in works"]
```

> **Your turn.**
> `Strict` sounds safer than `Lax`. Explain in one sentence why it would break our sign in, and in another why `Lax` is still safe enough.

<details>
<summary>Answer</summary>

`Strict` never sends a cookie on a request that started on another site, and the callback starts on Keycloak's page, so `playground_login` would never arrive and every sign in would fail. `Lax` only adds plain navigations, where a person follows a link or redirect. It still refuses the background requests that cross-site attacks use, such as a hidden form posting to our server.

</details>

### 1.11 The BFF pattern: why the browser holds no token

You could let the browser's JavaScript hold the access token and call the API directly. Many single page apps do. In the **BFF** (backend for frontend) pattern, the website's own server does the OAuth work and keeps the tokens instead. The browser holds only an opaque `HttpOnly` cookie that means nothing on its own, and the server adds the token when it talks to the API. In Playground, the Next.js server is the BFF. Where it keeps the tokens (its memory today, ElastiCache on AWS) is a separate choice: it is a BFF either way, because the browser holds only the cookie.

Why bother? An access token is a **bearer token**: like a cinema ticket, whoever holds it gets in. No name check.

```mermaid
flowchart TB
    subgraph SPA["Tokens in the browser"]
        T1["access token in<br/>localStorage or JS memory"]
        X1["one bad script on the page<br/>(XSS, a bad npm package,<br/>a browser extension)"]
        X1 -->|"reads it, sends it away"| T1
        T1 --> L1["attacker calls the API as Maya<br/>until the token expires"]
    end
    subgraph BFF["Tokens on the server (our design)"]
        T2["browser holds only<br/>an opaque session id, HttpOnly"]
        X2["the same bad script"]
        X2 -.->|"cannot read an HttpOnly cookie"| T2
        T2 --> L2["no token to steal.<br/>The server can end the session at once"]
    end
```

How to read it: on the left, any script that runs in the page can read the token and carry it off. On the right, the browser holds an id that JavaScript cannot read, that means nothing outside Playground, and that the server can cancel in one line.

The trade-off: the server must remember sessions (here, in memory, which Part 8 returns to), and your frontend and its server are one deployable thing.

> **Your turn.**
> The session id cookie still lets someone in, if they get it. So what did we gain by not giving the browser the access token? Name two things.

<details>
<summary>Answer</summary>

1. **JavaScript cannot read it** (`HttpOnly`), so the most common theft, a malicious script, cannot take it.
2. **It is useless outside Playground and can be killed on the server.** An access token works against the API directly until it expires, and nobody can take it back. A session id only works through our Next.js server, which can forget it at once (sign out, Flow D) or refuse it.

A third: the access token never appears in browser history, developer tools or logs on the user's machine.

</details>

### 1.12 Service accounts: the API has its own login too

Sometimes a program, not a person, needs a token. The API calls Keycloak's admin API to disable a person. For that it signs in as a *machine*, using the **client credentials** grant: it sends its own client id and secret and receives an access token. No browser, no code, no person. The Keycloak client for this is `playground-backend`, and its service account has only three rights: `view-users`, `query-users`, `manage-users`.

### 1.13 Open redirect: where we send people after sign in

Maya opens `/dashboard/reports`. She has to sign in first, and afterwards she should land on `/dashboard/reports`, not the home page. So the address travels along as `returnTo`. That convenience is also a classic hole:

```mermaid
sequenceDiagram
    autonumber
    actor M as Maya
    participant A as Playground (no check)
    participant K as Keycloak
    participant E as evil.example
    Note over M: email: "your report is ready",<br/>link: playground.example/auth/login?returnTo=https://evil.example
    M->>A: opens the link: it really is Playground
    A-->>M: go to Keycloak
    M->>K: signs in on the real Keycloak page
    K-->>M: back to Playground
    A-->>M: redirect to returnTo = evil.example
    M->>E: a page that looks like Playground:<br/>"session expired, type your password again"
```

How to read it: every step looks real to Maya, because steps 1 to 4 **are** real. Only the last redirect is wrong, and by then she trusts it. This is an **open redirect**: a trusted site that forwards people to any address it is handed.

The rule, in `safeReturnTo` ([return-to.ts](../apps/web/src/domain/return-to.ts)): a return address must be a **local path**.

| `returnTo` | Result | Why |
|---|---|---|
| `/dashboard/reports?tab=2` | kept | starts with one `/` |
| `https://evil.example` | `/dashboard` | a full address |
| `//evil.example` | `/dashboard` | browsers read `//` as "same scheme, **other site**" |
| `/\evil.example` | `/dashboard` | some browsers treat `/\` like `//` |
| a path with a control character (a newline, a tab) | `/dashboard` | such characters can split or bend the redirect header |

---

## 2. Run it and look around

You need Docker. From the repo root:

```bash
docker compose up -d --build        # first build takes a few minutes
docker compose ps                   # five services should be Up
```

| URL | What |
|---|---|
| http://localhost:3000 | the app |
| http://localhost:8000/docs | the API's Swagger page (it needs a token to do much) |
| http://localhost:8080 | Keycloak admin console. `admin` / `admin`, then switch to the realm **playground** |

People you can sign in as:

| Email | Password | What they are |
|---|---|---|
| `admin@example.test` | `Admin123!` | the first administrator (the API makes the first account an administrator because this email is in `BOOTSTRAP_ADMIN_EMAILS` and Keycloak says it is verified) |
| `maya@example.test` | `Maya123!` | an ordinary person, who starts **pending** until approved |

Four things to keep open while you read:

1. **Browser DevTools, Network tab**, with **Preserve log** ticked. You will watch the redirects.
2. **DevTools, Application tab, Cookies.** You will watch the two cookies appear.
3. **The Keycloak admin console.** You will look at the client, the sessions and the tokens it would issue.
4. **A terminal** for `curl` and `docker compose logs -f web api keycloak`.

---

## 3. The code, one flow at a time

The web app is split the hexagonal way: `domain/` holds pure rules, `application/` the use cases and the ports they need, `adapters/` the code that talks to Keycloak and the stores, and `composition.ts` wires one to the other. The Next.js routes are thin: they read a cookie, call a use case, set a cookie.

| Piece | File | Job |
|---|---|---|
| Gate | [proxy.ts](../apps/web/src/proxy.ts) | no cookie, no protected page |
| Start and finish a login (routes) | [auth/login/route.ts](../apps/web/src/app/auth/login/route.ts), [auth/callback/route.ts](../apps/web/src/app/auth/callback/route.ts) | set and delete the two cookies, call the use cases |
| Sign in (use cases) | [application/sign-in.ts](../apps/web/src/application/sign-in.ts) | `startLogin`, `finishLogin` |
| Login attempt, session, return address (rules) | [domain/login-attempt.ts](../apps/web/src/domain/login-attempt.ts), [domain/session.ts](../apps/web/src/domain/session.ts), [domain/return-to.ts](../apps/web/src/domain/return-to.ts) | the 10 minute limit, when to refresh, `safeReturnTo` |
| Ports | [application/ports.ts](../apps/web/src/application/ports.ts) | `IdentityProvider`, `LoginAttemptStore`, `SessionStore`, `BackendApi` |
| Keycloak (adapter) | [adapters/keycloak-identity-provider.ts](../apps/web/src/adapters/keycloak-identity-provider.ts) | `beginLogin`, `completeLogin`, `refresh`, `endSessionUrl`, with the `openid-client` library. The only file that knows Keycloak |
| Stores (adapter) | [adapters/in-memory-stores.ts](../apps/web/src/adapters/in-memory-stores.ts) | login attempts and sessions, in memory |
| Wiring | [composition.ts](../apps/web/src/composition.ts) | picks the adapters. The one file to change for ElastiCache |
| Cookies | [lib/auth/session.ts](../apps/web/src/lib/auth/session.ts), [lib/auth/config.ts](../apps/web/src/lib/auth/config.ts) | cookie names and settings, reading the session id |
| Access token, with refresh | [application/access-token.ts](../apps/web/src/application/access-token.ts) | one refresh at a time per session |
| Call the API | [application/call-backend.ts](../apps/web/src/application/call-backend.ts), [api/backend/[...path]/route.ts](../apps/web/src/app/api/backend/[...path]/route.ts), [lib/api.ts](../apps/web/src/lib/api.ts) | add `Bearer`, for the browser's calls and for pages rendered on the server |
| Sign out | [application/sign-out.ts](../apps/web/src/application/sign-out.ts), [auth/logout/route.ts](../apps/web/src/app/auth/logout/route.ts) | end both sessions |
| Token check (API) | [auth.py](../apps/api/app/auth.py) | verifies the token |
| Endpoints (API) | [main.py](../apps/api/app/main.py) | one check chain per request |
| Use cases (API) | [access/service.py](../apps/api/app/access/service.py) | `account_for`, `change` |
| Rules (API) | [access/domain/account.py](../apps/api/app/access/domain/account.py) | pure rules, no framework |
| Keycloak admin (API) | [access/adapters/keycloak_admin.py](../apps/api/app/access/adapters/keycloak_admin.py) | the API's own login, then enable and disable people |

### Flow A: the first sign-in

The steps are the ones in [0.3](#03-one-sign-in-numbered). Here is where each lives in the code:

| Steps | Route | Use case | Adapter |
|---|---|---|---|
| 1 to 2 | [proxy.ts](../apps/web/src/proxy.ts) | | |
| 3 to 4 | [login/route.ts](../apps/web/src/app/auth/login/route.ts) | `startLogin` | `beginLogin` makes `state`, `nonce`, verifier. `attempts.save` keeps them |
| 5 to 8 | (Keycloak) | | |
| 9 to 12 | [callback/route.ts](../apps/web/src/app/auth/callback/route.ts) | `finishLogin` | `attempts.take`, then `completeLogin` checks all three and swaps the code. `sessions.put` keeps the tokens |
| 13 to 18 | the dashboard page, via [lib/api.ts](../apps/web/src/lib/api.ts) | `callBackend` | Flow B |

**Steps 3 to 4: starting.** The route reads the query, calls the use case, and sets the attempt cookie:

```ts
// app/auth/login/route.ts
const { attemptId, redirectTo } = await app().startLogin({
  returnTo: params.get("returnTo"),
  register: params.get("register") === "1",
});
const res = NextResponse.redirect(redirectTo);
res.cookies.set(LOGIN_COOKIE, attemptId, cookieOptions(LOGIN_ATTEMPT_TTL_MS / 1000));
```

The use case cleans the return address (1.13), asks the identity provider to begin, and saves the attempt:

```ts
// application/sign-in.ts
const returnTo = safeReturnTo(input.returnTo);
const begun = await deps.idp.beginLogin({ register: input.register });
const attemptId = deps.newId();
await deps.attempts.save(attemptId, {
  state: begun.state, nonce: begun.nonce, pkceVerifier: begun.pkceVerifier,
  returnTo, startedAt: deps.now(),
});
```

The Keycloak adapter makes the three values and builds the Keycloak address:

```ts
// adapters/keycloak-identity-provider.ts, beginLogin
const state = client.randomState();
const nonce = client.randomNonce();
const pkceVerifier = client.randomPKCECodeVerifier();
const params = {
  redirect_uri: this.redirectUri(),
  scope: "openid profile email",
  state, nonce,
  code_challenge: await client.calculatePKCECodeChallenge(pkceVerifier),
  code_challenge_method: "S256",
};
if (opts.register) params.prompt = "create"; // Keycloak shows the registration form first
```

`prompt=create` is how "Create account" sends you straight to Keycloak's registration form (Flow E).

**What you can observe.** Run this and read the headers (this is real output, with the random values hidden):

```bash
curl -si http://localhost:3000/auth/login
```

```text
HTTP/1.1 307 Temporary Redirect
location: http://localhost:8080/realms/playground/protocol/openid-connect/auth?redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fcallback&scope=openid+profile+email&state=<random>&nonce=<random>&code_challenge=<hash>&code_challenge_method=S256&client_id=playground-web&response_type=code
set-cookie: playground_login=<id>; Path=/; Max-Age=600; HttpOnly; SameSite=lax
```

Every parameter is explained under step 4 in 0.3.

**Steps 5 to 8: Keycloak.** You type the password **into Keycloak's page on `localhost:8080`**. Our code never sees it. Keycloak then redirects you to the callback address, which must exactly match the realm's `redirectUris` (`http://localhost:3000/auth/callback`). Keycloak refuses any other address, so an attacker cannot have your code sent to their own server.

**Steps 9 to 12: the callback.** The route hands the attempt id and the callback address to the use case, then swaps the cookies:

```ts
// app/auth/callback/route.ts
const { sessionId, returnTo } = await app().finishLogin(request.cookies.get(LOGIN_COOKIE)?.value, callbackUrl);
const res = NextResponse.redirect(new URL(returnTo, env.appUrl));
res.cookies.set(SESSION_COOKIE, sessionId, cookieOptions());
res.cookies.delete(LOGIN_COOKIE);
```

```ts
// application/sign-in.ts, finishLogin
const attempt = await deps.attempts.take(attemptId); // once only: taking it removes it
if (!attempt || isExpired(attempt, deps.now())) throw new SignInFailed("login_expired");
if (callbackUrl.searchParams.has("error")) throw new SignInFailed("login_refused");
session = await deps.idp.completeLogin(callbackUrl, attempt); // checks state, nonce and PKCE
const sessionId = deps.newId();
await deps.sessions.put(sessionId, session);
```

- `take` returns the saved attempt **and deletes it**, so a replayed callback finds nothing (`login_expired`). An attempt older than 10 minutes is refused the same way.
- `completeLogin` hands the saved values to the library:

```ts
// adapters/keycloak-identity-provider.ts, completeLogin
const tokens = await client.authorizationCodeGrant(cfg, callbackUrl, {
  pkceCodeVerifier: attempt.pkceVerifier,
  expectedState: attempt.state,
  expectedNonce: attempt.nonce,
});
return toSession(tokens);
```

  The library checks that `state` matches (step 9), sends the code, verifier and client secret to Keycloak (step 10), and checks the ID token's claims, including the `nonce` (step 11). Any failure throws, and the person lands on `/?error=login_failed`.
- The session cookie `playground_session` holds a new random id. The tokens themselves never leave the server.

**What you can observe.** Sign in with DevTools open (Network, Preserve log). You should see, in order: `/auth/login` (307), Keycloak's `auth` page, the form POST, then `/auth/callback?...code=...&state=...` (307), then your page. Click the callback request and read `code` and `state` in the URL. Then open Application, Cookies, `localhost:3000`: `playground_session` is there, flagged `HttpOnly`, and `playground_login` is gone. In the console, type `document.cookie` and notice the session cookie is **not** listed: scripts cannot read it.

### Flow B: an ordinary request

After signing in, every page and API call goes through the same three hops.

```mermaid
sequenceDiagram
    actor P as Person
    participant W as Next.js server
    participant K as Keycloak
    participant A as API
    participant D as API database
    P->>W: request with the session cookie
    W->>W: look up tokens by session id
    alt access token ends in under 30 s
        W->>K: refresh token grant
        K-->>W: new access token and refresh token
    end
    W->>A: GET /me with Bearer access token
    A->>A: verify signature, issuer, audience, expiry
    A->>D: find the account by sub
    D-->>A: role and status
    A-->>W: the account, or a refusal
    W-->>P: page
```

**Hop 1: the gate.** [proxy.ts](../apps/web/src/proxy.ts) runs before `/dashboard` and `/admin`:

```ts
if (!request.cookies.has("playground_session")) {
  const login = new URL("/auth/login", request.url);
  login.searchParams.set("returnTo", request.nextUrl.pathname + request.nextUrl.search);
  return NextResponse.redirect(login);
}
```

It only checks that a cookie *exists*. It is a quick bounce, not a security check. The real check is that the page then asks the API, which verifies the token.

**Hop 2: getting a usable access token.** `accessTokenFor` in [access-token.ts](../apps/web/src/application/access-token.ts), with the 30 second rule `needsRefresh` from [domain/session.ts](../apps/web/src/domain/session.ts):

```ts
const session = await deps.sessions.get(sessionId);
if (!sessionId || !session) return null;
if (!needsRefresh(session, deps.now())) return session.accessToken;

let pending = refreshing.get(sessionId);
if (!pending) {
  pending = deps.idp
    .refresh(session)
    .then(async (fresh) => { await deps.sessions.put(sessionId, fresh); return fresh; })
    .catch(async () => { await deps.sessions.take(sessionId); return null; }) // Keycloak refused
    .finally(() => { refreshing.delete(sessionId); });
  refreshing.set(sessionId, pending);
}
return (await pending)?.accessToken ?? null;
```

Read it as three cases:

1. More than 30 seconds left: use the token as is.
2. 30 seconds or less: refresh. The session row gets new tokens under the **same id**, so the browser's cookie does not change and the browser notices nothing (Flow F, F1). The `refreshing` map holds *one refresh in flight per session*. If two requests arrive together, the second **waits for the first** instead of sending a second refresh. Why it matters: if the realm rotates refresh tokens (it does not today, but production should consider it), sending the old one twice looks like theft and kills the session. Even without rotation, two refreshes at once are wasted calls. This lock is the fix for the log-out-when-switching-windows bug MK3 had, which came from exactly that race.
3. Keycloak refuses (session ended, user disabled, token already used): drop our session. The person is asked to sign in again.

**Hop 3: the forwarder.** `callBackend` in [call-backend.ts](../apps/web/src/application/call-backend.ts) gets the token and makes the call. With no session it makes no call at all:

```ts
const token = await deps.accessTokenFor(sessionId);
if (!token) return { kind: "no_session" };
return { kind: "response", ...(await deps.backend.request(req, token)) }; // the adapter adds "Authorization: Bearer <token>"
```

Two places use it. The browser's own calls go to [api/backend/[...path]/route.ts](../apps/web/src/app/api/backend/[...path]/route.ts), which answers `401 no_session` when there is no session. Pages rendered on the server use [lib/api.ts](../apps/web/src/lib/api.ts) (`getMe()`). Either way the token goes from Next.js to the API and no further.

**Hop 4: the API verifies the token.** [auth.py](../apps/api/app/auth.py):

```python
claims = jwt.decode(
    token,
    self._signing_key(token),          # Keycloak's public key, found by the token's kid
    algorithms=["RS256"],              # only this algorithm is accepted
    audience=self.audience,            # must be "playground-api"
    issuer=self.issuer,                # must be our realm
    options={"require": ["exp", "iss", "aud", "sub"]},
)
```

- The key is found by the `kid` in the token header, from Keycloak's JWKS (`/protocol/openid-connect/certs`), which the library caches.
- `algorithms=["RS256"]` matters: it blocks the classic trick of a token that claims `alg: none` or a weaker algorithm.
- A token with no `email` is refused too.

**Hop 5: the account, then the permission.** [main.py](../apps/api/app/main.py) builds a chain of checks. Each layer depends on the one before:

```mermaid
flowchart TB
    T["principal<br/>valid token?"] --> AA["any_account<br/>find the account, or create it"]
    AA --> ND["not_deactivated<br/>refuse if deactivated"]
    ND --> AC["active_account<br/>refuse if pending"]
    AC --> AD["administrator<br/>refuse if not an administrator"]
    ND -.->|"/me stops here"| ME["GET /me"]
    AC -.-> LIST["most endpoints"]
    AD -.-> ADM["/accounts, /audit, approve, deactivate ..."]
```

- `GET /me` stops at `not_deactivated`, so a **pending** person can ask for their own status and nothing else.
- Admin endpoints need `administrator`, which needs `active_account`, which needs `not_deactivated`.
- **The account is read from the database on every request.** That is why deactivating someone, or changing a role, takes effect on their very next request, not when their token expires.

**First sight creates an account.** `any_account` calls `AccessService.account_for` ([service.py](../apps/api/app/access/service.py)). Step 16 in 0.3 shows the rows it writes.

```python
existing = self.accounts.by_identity(identity)       # identity is the token's sub
if existing:
    ... refresh name and email from the token, return it
first_admin = email_verified and email.lower() in self.bootstrap_admins
account = Account(..., role=administrator if first_admin else user,
                       status=active if first_admin else pending, ...)
```

- A new person gets a **pending** account on their first request. Registering was Keycloak's job; becoming known to *our* system happens here, silently.
- The first administrator comes from setup: an email in `BOOTSTRAP_ADMIN_EMAILS` **and** verified by Keycloak, so nobody can claim it by registering with someone else's address.

### Flow C: an administrator changes an account

This is where the API becomes a *client* of Keycloak.

```mermaid
sequenceDiagram
    actor Adm as Administrator
    participant A as API
    participant S as AccessService
    participant K as Keycloak
    participant D as API database
    Adm->>A: POST /accounts/{id}/deactivate with a reason
    A->>A: administrator check
    A->>S: change(actor, target, deactivate, reason)
    S->>S: decide: the pure rules (reason, not yourself, last administrator)
    S->>K: client credentials token (the API's own login)
    K-->>S: service account access token
    S->>K: disable the user, then end their sessions
    K-->>S: ok
    S->>D: save the account, then the audit entry
    A-->>Adm: the updated account
```

[service.py](../apps/api/app/access/service.py) `change`:

```python
updated = decide(action, actor, target, self.accounts.count_active_administrators())
# Keycloak first. If it fails nothing changes on our side (BC-ACCESS question 6).
try:
    if action is Action.deactivate:
        self.idp.disable_user(target.identity)
        self.idp.end_sessions(target.identity)
    elif action is Action.reinstate:
        self.idp.enable_user(target.identity)
except Exception as exc:
    raise IdentityProviderUnavailable("Keycloak could not be reached. Nothing was changed.") from exc
self.accounts.save(updated)
self.audit.record(actor.id, action.value, target.id, cleaned, _now())
```

- `decide` ([access/domain/account.py](../apps/api/app/access/domain/account.py)) is **pure**: no database, no HTTP. It enforces the rules (a reason of at least three letters, nobody deactivates themselves, there is always an administrator).
- **Keycloak is called first.** Two systems cannot change in one transaction. If Keycloak succeeds and our database then fails, a person is disabled but our record still says active. If we did it the other way and Keycloak failed, we would say deactivated while they could still sign in. Calling Keycloak first means a failure leaves *nothing* changed. (Open: a failure between the two steps. Decision 26 lists it.)
- **Approve does not call Keycloak.** A pending person already has a Keycloak login. Approving is only a status change in our database.
- The API proves itself to Keycloak in [keycloak_admin.py](../apps/api/app/access/adapters/keycloak_admin.py) with the **client credentials** grant (Part 1.12), caching the token until 10 seconds before it expires:

```python
r = self._http.post(f"{...}/protocol/openid-connect/token", data={
    "grant_type": "client_credentials",
    "client_id": self._s.keycloak_backend_client_id,
    "client_secret": self._s.keycloak_backend_client_secret,
})
```

### Flow D: sign out, and what happens to tokens you already issued

[auth/logout/route.ts](../apps/web/src/app/auth/logout/route.ts) is a **POST** only, so a link or an image on another site cannot sign you out.

```ts
// app/auth/logout/route.ts
const { redirectTo } = await app().signOut(await currentSessionId());
const res = NextResponse.redirect(redirectTo ?? new URL("/", env.appUrl), 303);
res.cookies.delete(SESSION_COOKIE);

// application/sign-out.ts
const session = await deps.sessions.take(sessionId);              // forget our session and its tokens
return { redirectTo: await deps.idp.endSessionUrl(session?.idToken) }; // Keycloak's end-session address
```

If Keycloak cannot be reached, `redirectTo` is null and the person just goes home: our session has ended either way. `303` is a redirect that tells the browser to follow with a `GET`.

Two sessions end: ours (memory plus cookie) and Keycloak's (by sending you to its end-session address with the ID token as `id_token_hint`, which is the one real use the app makes of the ID token). If Keycloak's session stayed alive, the next "Sign in" would log you straight back in.

Now a harder question: **what if a token is already out there when something changes?**

```mermaid
flowchart LR
    T0["t=0<br/>access token issued<br/>valid 5 min"] --> T1["t=2 min<br/>admin deactivates the person"]
    T1 --> Q{"person's next request"}
    Q --> R1["API reads the account<br/>status = deactivated<br/>REFUSED at once"]
    T1 --> Q2{"web server tries to refresh<br/>after the 5 min"}
    Q2 --> R2["Keycloak refuses:<br/>user disabled, sessions ended"]
```

- The token itself would still pass the *signature* check until it expires. What refuses the person immediately is the API reading the **account** on every request.
- Keycloak also disabled them and ended their sessions, so they cannot refresh or sign in again.

Both are needed. Keycloak alone would leave up to 5 minutes. The account check alone would leave them able to log in again. This is the practical reason roles and status live in our database and not inside the token.

### Flow E: registering

"Create account" goes to `/auth/login?register=1`, which adds `prompt=create` so Keycloak opens its registration form. The realm has `registrationAllowed: true`. After registering, Keycloak signs the person in, and the flow continues exactly as Flow A. They arrive with a Keycloak user and no API account, and their first request creates a **pending** one (Flow B). That is the whole reason there is no "sign up" code in this repo.

### Flow F: the data after sign in

[0.3](#03-one-sign-in-numbered) printed every value up to the first page. This flow carries on with the same cast: Maya's session five minutes on, an administrator changing her account, and sign out. Each shows exactly what is stored or sent.

#### F1. Five minutes on: a refresh changes only the session row

```mermaid
sequenceDiagram
    autonumber
    actor B as Browser
    participant N as Next.js server
    participant K as Keycloak
    participant API as API
    B->>N: GET /dashboard, same cookie
    N->>N: session row: access token ends in under 30 s
    N->>K: refresh token + client secret
    K-->>N: new access token (and maybe a new refresh token)
    N->>N: overwrite the row, same session id
    N->>API: Bearer new access token
    API-->>N: the account
    N-->>B: the page
```

How to read it: the browser sends the same ticket and gets a page. Only the coat on the rack was swapped for a fresh one.

The data. At 01:58:30 the access token has 18 seconds left, under the 30 second margin, so Next.js refreshes:

```text
POST http://keycloak:8080/realms/playground/protocol/openid-connect/token

grant_type    = refresh_token
refresh_token = eyJhbGciOiJIUzUxMiIs…
client_id     = playground-web
client_secret = playground-web-dev-secret
```

The answer has the same shape as at step 11 in 0.3. The session row is overwritten under the **same id**:

```text
  "qzRp2pmHUgXwm6PKAT9Ohvm-2gv_J513URogcTDR1jA" ->
    {
      idToken:         "eyJhbGciOiJSUzI1NiIs…",   // the new one, or the old one kept
      accessToken:     "eyJhbGciOiJSUzI1NiIs…",   // NEW: iat 01:58:30, exp 02:03:30
      refreshToken:    "eyJhbGciOiJIUzUxMiIs…",   // NEW if Keycloak sent one, else the old one kept
      accessExpiresAt: 1794881010000              // 02:03:30
    }
```

The cookie does not change. The database does not change. Only the coat on the rack is new.

#### F2. An administrator approves, then deactivates her

Approve: `POST /accounts/0c1f6d2e-…/approve` with no body. No Keycloak call, one field changes:

```text
 id          | … | role | status  →  status
 0c1f6d2e-…  | … | user | pending →  active
```

Deactivate, with a reason. The request:

```text
POST /accounts/0c1f6d2e-7a43-4b8e-9d51-2f6a8e3b9c07/deactivate
Content-Type: application/json

{"reason": "Left the project team"}
```

Keycloak is changed first (`enabled` becomes `false` on her user, and her sessions, including `sid` `6194819b-…`, are ended). Then our two tables:

```text
accounts
 id          | identity    | name     | role | status
 0c1f6d2e-…  | 64b93477-…  | Maya Rao | user | deactivated

audit_entries
 id | at                  | actor_id                             | action     | target_id   | reason
----+---------------------+--------------------------------------+------------+-------------+-----------------------
  2 | 2026-11-17 01:53:49 |                                      | register   | 0c1f6d2e-…  |
  3 | 2026-11-17 02:05:10 | 7d3a9b25-1e6f-4c80-b2d4-93a1f0e6c518 | approve    | 0c1f6d2e-…  |
  4 | 2026-11-17 02:20:42 | 7d3a9b25-1e6f-4c80-b2d4-93a1f0e6c518 | deactivate | 0c1f6d2e-…  | Left the project team
```

`7d3a9b25-…` is the administrator's account id. Approve needs no reason, so its `reason` is empty. Deactivate does.

Now look at Maya's session row in Next.js. **It has not changed.** Her access token is still validly signed. Her next request goes to the API with it, the API reads her row, sees `deactivated`, and refuses with a `403`:

```json
{"detail": {"code": "account_deactivated", "message": "Your account is deactivated."}}
```

That is the rule from the top of this guide, as data: the token says who, the row says what.

#### F3. Sign out: rows disappear

When a signed-in person signs out, Next.js takes their session row out of the store and sends the browser to Keycloak:

```text
HTTP/1.1 303 See Other
location: http://localhost:8080/realms/playground/protocol/openid-connect/logout?post_logout_redirect_uri=http%3A%2F%2Flocalhost%3A3000%2F&id_token_hint=eyJhbGciOiJSUzI1NiIs…&client_id=playground-web
set-cookie: playground_session=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT
```

Afterwards:

| Place | Holds for this person |
|---|---|
| browser, `localhost:3000` | nothing |
| Next.js attempt store | nothing |
| Next.js session store | nothing |
| Keycloak | the user record, no session |
| API database | the account row and its audit entries, unchanged. Signing out is not an account change |

#### The whole journey in one table

| Step | Browser (`localhost:3000`) | Next.js memory | Keycloak | API database |
|---|---|---|---|---|
| before | nothing | nothing | user, no session | no row |
| steps 3 to 4, `/auth/login` | `playground_login` | attempt row | user | no row |
| steps 9 to 12, callback | `playground_session` | session row (3 tokens) | user, session `sid` | no row |
| steps 13 to 18, first page | same cookie | same row | same | account `pending`, audit `register` |
| F1 refresh | same cookie | same id, new tokens | same session | unchanged |
| F2 deactivate | same cookie | same row, now useless | user disabled, no session | account `deactivated`, 2 more audit rows |
| F3 sign out | nothing | nothing | no session | unchanged |

> **Your turn.**
> In F2, Maya is deactivated but her session row in Next.js still holds a validly signed access token with minutes left. Name the one piece of data that stops her, and where it lives.

<details>
<summary>Answer</summary>

The `status` column of her row in the `accounts` table, in the API's PostgreSQL: `deactivated`. The API reads it on every request, after the token has passed its checks. The token itself carries no status at all (look at the decoded tokens in 1.9), so it cannot be what stops her.

</details>


---

## 4. Keycloak, the other half

Everything Keycloak does here is configured in one file: [playground-realm.json](../keycloak-config/realm/playground-realm.json). It is imported once, when Keycloak first starts (`start-dev --import-realm`). If the realm already exists it is **not** re-read. To re-import, wipe the data: `docker compose down -v`.

**Concepts first.**

- A **realm** is one isolated world of users, clients and settings. Ours is `playground`.
- A **client** is an app registered to use the realm for login.
- A **scope** is a bundle of claims a client may ask for (`profile`, `email`).
- A **protocol mapper** adds or shapes claims in a token.

**The settings that matter** (open the file next to this table):

| Setting | Value | What it does |
|---|---|---|
| `accessTokenLifespan` | 300 | the access token lives 5 minutes |
| `ssoSessionIdleTimeout` | 1800 | a Keycloak session ends after 30 min idle |
| `ssoSessionMaxLifespan` | 28800 | and after 8 hours regardless |
| `registrationAllowed` | true | the "Create account" page exists |
| `bruteForceProtected` | true | repeated wrong passwords lock the user for a while |
| `verifyEmail` | false | no email check (a dev shortcut: `email_verified` is set by hand) |
| `sslRequired` | none | HTTP is accepted. **Dev only.** |

**Client `playground-web`** (the Next.js server):

| Setting | Value | Why |
|---|---|---|
| `publicClient` | false | it is confidential: it has a secret |
| `standardFlowEnabled` | true | the authorization code flow is allowed |
| `directAccessGrantsEnabled` | false | the password grant is switched off, so nobody can post a password to the token endpoint |
| `implicitFlowEnabled` | false | the old, leaky flow that put tokens in URLs |
| `redirectUris` | `http://localhost:3000/auth/callback` | the only address Keycloak will send a code to |
| `pkce.code.challenge.method` | S256 | PKCE is required |
| mapper `playground-api-audience` | adds `aud: playground-api` | without it the API would refuse the token |

**Client `playground-backend`** (the API's own login): `serviceAccountsEnabled: true`, no browser flows. Its service account holds only `view-users`, `query-users`, `manage-users`.

**The tokens it can issue, and how to see one.** The browser never has a token, so you cannot scrape it from DevTools. Two ways to see real ones:

- The admin console can generate the exact access token it would issue for a user. See experiment 6.
- You can fetch the backend's own token with `curl` and decode it. See experiment 3.

**Endpoints Keycloak publishes.** Everything the code needs is discoverable from one URL (real output):

```bash
curl -s http://localhost:8080/realms/playground/.well-known/openid-configuration
```

```text
issuer                 = http://localhost:8080/realms/playground
authorization_endpoint = .../protocol/openid-connect/auth      (where the browser goes)
token_endpoint         = .../protocol/openid-connect/token     (where the server swaps the code)
jwks_uri               = .../protocol/openid-connect/certs     (the public keys)
end_session_endpoint   = .../protocol/openid-connect/logout    (sign out)
```

**A Docker wrinkle that confuses everyone.** Tokens carry `iss=http://localhost:8080/...` because that is the address the *browser* uses. But inside Docker, the web and API containers reach Keycloak at `http://keycloak:8080`. So two addresses exist for one server. The code handles this on purpose: `KEYCLOAK_ISSUER` is the public one (what to *expect* in tokens), `KEYCLOAK_INTERNAL_ISSUER` is where to *call*, and Keycloak runs with `KC_HOSTNAME_BACKCHANNEL_DYNAMIC=true`. The web app reads Keycloak's discovery document by hand (`load` in [keycloak-identity-provider.ts](../apps/web/src/adapters/keycloak-identity-provider.ts)) because the library would otherwise reject the mismatch. If you ever see "issuer mismatch" or "invalid_token" in Docker, start here.

---

## 5. What lives where, and what an attacker gets

| Thing | Created by | Held by | Visible to the browser? |
|---|---|---|---|
| Password | the person | Keycloak (hashed) | typed into Keycloak's page only |
| Keycloak session cookies | Keycloak | the browser, for `localhost:8080` | yes, but only Keycloak uses them |
| `state`, `nonce`, verifier | Next.js | Next.js memory | no |
| `playground_login` cookie | Next.js | the browser | yes (an opaque id, 10 min) |
| Authorization code | Keycloak | passes through the URL | yes, but one use and needs the verifier |
| Access, refresh, ID tokens | Keycloak | Next.js memory | **no** |
| `playground_session` cookie | Next.js | the browser | yes (an opaque id, `HttpOnly`) |
| Client secret `playground-web` | realm file | Next.js environment | no |
| Backend client secret | realm file | API environment | no |
| Role, status, audit | the API | the API's PostgreSQL | no |

**What does an attacker get with...**

| They have | What they can do | What limits them |
|---|---|---|
| the authorization code from the URL | nothing alone | it is one use, short, and needs the PKCE verifier |
| your `playground_session` cookie | act as you on this site until you sign out or the session ends | `HttpOnly` stops scripts reading it, `Secure` (on HTTPS) stops sniffing, but a stolen cookie is a stolen session. Keep sessions short |
| an access token | call the API as you until it expires | 5 minutes, and the API still reads your account each time |
| a refresh token | mint new access tokens as you | it only works at Keycloak and dies with the session. Rotation (off today) would also let Keycloak detect reuse |
| the client secret | impersonate our app to Keycloak | they still need a valid code and verifier, and the redirect URI is fixed |
| the backend client secret | disable or enable users | only the three rights it holds, nothing else. Rotate it |
| a forged token | nothing | the signature check fails |
| a valid token for another app | nothing | `aud` is not `playground-api` |
| script injected into the page (XSS) | act as you while the page is open | tokens are not in the page, and the cookie is `HttpOnly` |

---

## 6. Experiments

Do these in order. Each takes a minute and shows one idea with real values. Run them from the repo root with the stack up.

### 1. Watch the redirect

```bash
curl -si http://localhost:3000/auth/login | head -5
```

Find `state`, `nonce`, `code_challenge`, `client_id=playground-web`, and the `playground_login` cookie. This is the front channel. (Part 3, Flow A.)

### 2. Hit the API with nothing, then with rubbish

```bash
curl -si http://localhost:8000/me
curl -s  -H "Authorization: Bearer abc.def.ghi" http://localhost:8000/me
```

You should get, real output:

```text
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer
{"detail":{"code":"missing_token","message":"Sign in first."}}

{"detail":{"code":"invalid_token","message":"The token is not valid."}}
```

Two different refusals: no token, and a token that does not verify. Nothing reaches the database in either case.

### 3. Get a real, valid token, decode it, and watch the API reject it

The backend has its own login (client credentials). Use it to get a genuine Keycloak token:

```bash
curl -s -d grant_type=client_credentials \
        -d client_id=playground-backend \
        -d client_secret=playground-backend-dev-secret \
        http://localhost:8080/realms/playground/protocol/openid-connect/token > /tmp/tok.json

python3 - <<'EOF'
import json, base64
t = json.load(open('/tmp/tok.json'))['access_token']
dec = lambda p: json.loads(base64.urlsafe_b64decode(p + '=' * (-len(p) % 4)))
h, p, s = t.split('.')
print('HEADER ', dec(h))
for k, v in dec(p).items(): print(f'  {k}: {v}')
EOF
```

Real output (values differ per run):

```text
HEADER  {'alg': 'RS256', 'typ': 'JWT', 'kid': 'CdLHpIsQVTMSB4ZnSnlCGz9jNP_IAw23bkYEVaSntHI'}
  iss: http://localhost:8080/realms/playground
  sub: f453885d-c354-4e5c-ba6b-cd69c8dcf259
  aud: realm-management
  azp: playground-backend
  exp: ...        (300 seconds after iat)
  preferred_username: service-account-playground-backend
  scope: email profile
```

Notice: it has no refresh token (machines just ask again), `exp` is 300 seconds out, and the **header carries a `kid`**. Now offer it to the API:

```bash
curl -s -H "Authorization: Bearer $(python3 -c "import json;print(json.load(open('/tmp/tok.json'))['access_token'])")" http://localhost:8000/me
```

```text
{"detail":{"code":"invalid_token","message":"The token is not valid."}}
```

**Why?** The signature is valid and the issuer is right, but `aud` is `realm-management`, not `playground-api`, and there is no `email`. Signature checking is only the first of several checks. Delete `/tmp/tok.json` when done.

### 4. Match the token's `kid` to Keycloak's public keys

```bash
curl -s http://localhost:8080/realms/playground/protocol/openid-connect/certs
```

You will see two keys. The one with `"use": "sig"` and `"alg": "RS256"` has the same `kid` as the token's header in experiment 3. That is how the API picks the right key. The other (`"use": "enc"`) is for encryption and is not used here.

### 5. See what the browser can and cannot see

1. Sign in at http://localhost:3000.
2. DevTools, Application, Cookies, `localhost:3000`: find `playground_session`. It has `HttpOnly` ticked and no expiry (a session cookie).
3. DevTools console: type `document.cookie`. `playground_session` is not in the output.
4. Search the Network tab for any request header or response body containing `eyJ` (every JWT starts with those characters). You will not find one.

That is the BFF at work.

### 6. Read a real person's access token in the admin console

1. http://localhost:8080, sign in `admin` / `admin`, choose realm **playground**.
2. Clients, `playground-web`, the **Client scopes** tab, then **Evaluate**.
3. Pick a user (for example `maya@example.test`) and open **Generated access token**.

You will see her `sub`, `email`, `name` and `aud: playground-api`. This is what the API receives for her. (Menu names are from Keycloak 26. If a label differs, use the console's search box.)

### 7. Deactivate someone who is signed in

1. Sign in as Maya in a private window and open the dashboard.
2. As the administrator, open Accounts and deactivate Maya, with a reason.
3. In Maya's window, reload. She is refused immediately, though her token has minutes left.
4. In the admin console, Sessions: Maya's session is gone.
5. Reinstate her. She must sign in again (her sessions were ended).

This shows *both* defences from Flow D: the account check on every request, and Keycloak ending her sessions.

### 8. Restart the web server and see why sessions are in memory

```bash
docker compose restart web
```

Reload your signed-in tab. You are bounced to sign in, though your cookie is unchanged. The cookie is only an id, and the table it pointed to (in the server's memory) is gone. This is the weakness the AWS plan fixes with a shared store (Part 8).

### 9. Tamper with the cookie

In DevTools, edit `playground_session`'s value to anything else and reload. You are treated as signed out. The gate ([proxy.ts](../apps/web/src/proxy.ts)) only checks that *a* cookie exists, so you pass it, but the page asks for the account, the lookup by that id finds nothing, and you are redirected to sign in. This is the difference between the quick gate and the real check.

### 10. Shorten the access token and read the refresh (optional)

1. Admin console, Realm settings, **Tokens**, set **Access Token Lifespan** to 1 minute, save.
2. Sign in, wait over a minute, click around. You stay signed in: the web server refreshed silently.
3. Optional: turn on **Events** (Realm settings, Events, save events) and look at the user events for refresh activity.

---

## 7. When it breaks

| What you see | Most likely cause | Where to look |
|---|---|---|
| `Invalid redirect_uri` on Keycloak's page | the URL the app sent is not in the client's `redirectUris` | realm file, `playground-web` |
| back on `/?error=login_expired` | the `playground_login` cookie is missing or used (a second tab, an old tab, cookies blocked) | `finishLogin` in [sign-in.ts](../apps/web/src/application/sign-in.ts) |
| back on `/?error=login_failed` | the exchange or the `state`, `nonce` or PKCE check failed | `docker compose logs web` |
| endless redirect to sign in | the cookie is set but the lookup fails (the web server restarted) | experiment 8 |
| API says `invalid_token` for a real token | wrong `iss` (a localhost vs `keycloak:8080` mix), missing `aud` mapper, or no `email` | experiment 3, the Docker wrinkle in Part 4 |
| "Waiting for approval" for a long time | the account is pending, an administrator must approve | the Accounts page |
| `identity_provider_unavailable` on deactivate | the API cannot reach Keycloak, nothing was changed | `docker compose logs api` |
| everything fails after `docker compose down -v` | the database is empty and Keycloak re-imported: accounts start again | Maya is pending again |
| tokens rejected suddenly | the clock on a machine is wrong (`exp` and `iat` are times) | check the system clock |

---

## 8. Before you deploy

The playground cuts corners on purpose. Here is each corner, why it is safe locally, and what to do for AWS.

| Item | Today | Before production |
|---|---|---|
| **HTTPS** | plain HTTP, `sslRequired: none` | HTTPS everywhere (an Application Load Balancer with a certificate). Set `sslRequired` to external or all. `Secure` cookies turn on automatically when `APP_URL` is `https://` |
| **Client secrets** | `playground-web-dev-secret` and `playground-backend-dev-secret` in a file in git | generate new ones, keep them in AWS Secrets Manager, never in git, rotate them |
| **Keycloak mode** | `start-dev` (no caching, dev database settings, admin console open) | run in production mode (`start`) with a proper hostname, proxy header settings behind the load balancer, and the admin console not exposed to the internet |
| **Keycloak bootstrap admin** | `admin` / `admin` | a strong, unique password, and remove the bootstrap account after creating a real one |
| **Session store** | web server memory: a restart signs everyone out, and you cannot run two copies | a shared store (ElastiCache). The code is ready: write an adapter for the two store ports in [ports.ts](../apps/web/src/application/ports.ts), and change only [composition.ts](../apps/web/src/composition.ts) |
| **Realm import** | a file read once, with sample users | no sample users or passwords. Manage the realm through a controlled process |
| **Redirect URIs** | one localhost address | exactly your production callback, no wildcards |
| **Email** | `verifyEmail: false` | turn it on, and configure SMTP (Amazon SES), so `email_verified` means something. The first-administrator rule relies on it |
| **Administrator MFA** | none | require a second factor for administrators (Keycloak flow, no code) |
| **Brute force and rate limits** | Keycloak's brute-force lock only | also rate-limit registration and the login route at the edge (AWS WAF) |
| **Token lifetimes** | 5 minutes, 30 min idle, 8 h max | decide deliberately: shorter is safer, longer is friendlier |
| **Refresh token rotation** | off (`revokeRefreshToken = false`) | consider turning on *Revoke Refresh Token*, so a stolen refresh token is detected when reused. The one-at-a-time refresh lock in [access-token.ts](../apps/web/src/application/access-token.ts) already copes with it |
| **Database** | Keycloak and the API on local PostgreSQL | Amazon RDS (or Aurora) PostgreSQL, backups on, encrypted |
| **Schema changes** | tables created at start-up | migrations (for example Alembic) as a deploy step |
| **Logging and audit** | container logs | CloudWatch, with a retention policy. Never log tokens or cookies |
| **Cookie and CSRF** | `SameSite=Lax`, logout is POST only | keep POST for any state change. Do not add GET routes that change anything |

Questions to answer before go-live: who runs Keycloak and how it is patched, how a compromised client secret is rotated, what happens when Keycloak is down (sign-in fails, but already signed-in people continue until their tokens expire, since the API only needs Keycloak's public keys, which it caches), and how you would revoke every session at once.

---

## 9. Test yourself

Try each before opening the answer.

<details>
<summary>1. Why does Keycloak send a <em>code</em> instead of the tokens directly?</summary>
The redirect travels through the browser's address bar, which is visible to the person, extensions and logs. A code is short, one use and worthless without the verifier and client secret, and the server swaps it for tokens over a private back channel.
</details>

<details>
<summary>2. What does PKCE protect, and what is stored where?</summary>
It protects a stolen code. The verifier stays on our server. Only its hash goes to Keycloak at the start. At the exchange the verifier is sent, and Keycloak checks it hashes to what it saw. A thief with only the code cannot complete the exchange.
</details>

<details>
<summary>3. What attack does each of <code>state</code>, <code>nonce</code> and PKCE stop?</summary>
<code>state</code> stops login CSRF: being tricked into finishing someone else's sign in, so you end up signed in as the attacker. It travels in the URL and comes back unchanged. <code>nonce</code> stops replay: it is placed inside the signed ID token, proving that token was issued for this attempt. PKCE stops a stolen code from being swapped for tokens.
</details>

<details>
<summary>4. The payload of a JWT is readable by anyone. Why is that safe?</summary>
It contains nothing secret, and the signature, made with Keycloak's private key, means any change is detected. Readable is not forgeable.
</details>

<details>
<summary>5. Why can the browser hold a cookie but not the access token?</summary>
Any script in the page can read an access token held there. The cookie is an opaque, <code>HttpOnly</code> id that scripts cannot read, and means nothing without the server's memory behind it.
</details>

<details>
<summary>6. An administrator deactivates Maya. Her access token has 4 minutes left. What stops her?</summary>
The API reads her account from the database on every request and refuses a deactivated one. Keycloak also disabled her and ended her sessions, so she cannot refresh or sign in again.
</details>

<details>
<summary>7. Why does the API reject a genuinely signed Keycloak token in experiment 3?</summary>
A valid signature is only one check. The audience is <code>realm-management</code>, not <code>playground-api</code>, and there is no email claim.
</details>

<details>
<summary>8. Why is Keycloak called <em>before</em> the database when deactivating?</summary>
Two systems cannot change atomically. If Keycloak fails first, nothing has changed. The other order could leave our record saying deactivated while the person can still sign in.
</details>

<details>
<summary>9. Why are two requests refreshing at once a problem, and what prevents it?</summary>
If the realm rotates refresh tokens, sending the old one twice looks like theft and can end the session. This realm does not rotate today, but the code is safe either way: the <code>refreshing</code> map makes the second request wait for the first refresh's result. For the same reason the session always keeps the newest refresh token Keycloak sent.
</details>

<details>
<summary>10. What breaks if you restart the web server, and what is the fix for AWS?</summary>
Sessions live in memory, so the cookie's id no longer matches anything and everyone is signed out. Write an ElastiCache adapter for the session and login attempt stores, and change only <code>composition.ts</code> to use it.
</details>

<details>
<summary>11. A hacker sees the PKCE challenge in the redirect URL. Why can they still not swap the code?</summary>
The challenge is a hash of the verifier, and a hash cannot be reversed. Only our server knows the verifier, and it sends it only in the back channel at the swap.
</details>

<details>
<summary>12. Give two <code>returnTo</code> values that look local but are not.</summary>
<code>//evil.example</code> (browsers read it as "same scheme, other site") and <code>/\evil.example</code> (some browsers treat <code>/\</code> like <code>//</code>). Also a full address like <code>https://evil.example</code> and a bare <code>dashboard</code> are not local paths. The rule: a return address must start with a single <code>/</code>.
</details>

---

## 10. Glossary

| Term | Meaning |
|---|---|
| **Access token** | a short-lived signed JWT sent to the API as `Bearer`. It says who, not what they may do |
| **Audience (`aud`)** | who a token is meant for. The API requires `playground-api` |
| **Authorization code** | a one-use ticket in the redirect URL, swapped for tokens by the server |
| **Authorization code flow** | sign in by sending the browser to Keycloak and getting a code back (0.3, steps 3 to 12) |
| **`azp`** | "authorized party": the client that asked for the token (`playground-web`) |
| **Back channel** | a direct server to server call, private |
| **base64url** | a way to write bytes as letters, digits, `-` and `_`, safe to put in a URL |
| **Bearer token** | a token that works for whoever holds it, like a cinema ticket: no name check |
| **BFF** | backend for frontend: the website's server holds the tokens and the browser gets a cookie |
| **Callback / redirect URI** | the address Keycloak sends the browser back to (`/auth/callback`), pre-registered in the client |
| **Challenge (PKCE)** | the hash of the verifier, sent to Keycloak at the start. Safe to show: it cannot be turned back into the verifier |
| **Claim** | one fact inside a token (`sub`, `email`, `exp`) |
| **Client** | an app registered in Keycloak (`playground-web`, `playground-backend`) |
| **Client credentials** | a grant where a program logs in as itself with an id and secret |
| **Client secret** | a password for a confidential client |
| **Confidential client** | a client that can keep a secret (a server). A *public* client cannot (a phone or browser app) |
| **CSRF** | cross-site request forgery: another site making your browser send a request you did not mean to. `SameSite=Lax` and POST-only sign out stop it |
| **Discovery document** | Keycloak's list of its own addresses and settings, at `/.well-known/openid-configuration` |
| **Endpoint** | one address a server answers at, such as the token endpoint |
| **`exp`, `iat`** | when a token expires, and when it was issued: seconds since 1 Jan 1970 |
| **Front channel** | the browser's address bar: visible, not for secrets |
| **Grant** | a way to get tokens. Ours is the authorization code grant. The API's own login uses the client credentials grant. A refresh is the refresh token grant |
| **Hash (SHA-256)** | a one-way fingerprint of a value. The same input always gives the same hash, and the hash cannot be turned back into the input. Not encryption: there is no key |
| **`HttpOnly`** | a cookie setting: page JavaScript cannot read the cookie |
| **ID token** | a JWT saying who just logged in, for Next.js. It carries the `nonce`. Here it is kept for the sign out hint |
| **Identity provider** | the system that checks who people are and issues tokens. Keycloak |
| **Issuer (`iss`)** | who signed the token. The API requires our realm's address |
| **JWKS** | Keycloak's list of public keys, at `/protocol/openid-connect/certs` |
| **JWT** | `header.payload.signature`, a signed, readable token |
| **`kid`** | key id: which of Keycloak's keys signed the token |
| **Login attempt** | the server's record of one sign in in progress: `state`, `nonce`, verifier, return address, start time. Used once, dead after 10 minutes. Its id is in the `playground_login` cookie |
| **Login CSRF** | tricking someone into being signed in to the attacker's account. `state` stops it |
| **Mapper (protocol mapper)** | a Keycloak setting that adds or shapes a claim in a token, such as `aud: playground-api` |
| **Nonce** | "number used once": a random value Keycloak copies into the ID token, proving the token belongs to this attempt |
| **OAuth 2.0** | the standard for letting an app act for a person without their password |
| **OIDC** | OpenID Connect: identity (who signed in) on top of OAuth |
| **Open redirect** | a trusted site that forwards people to any address it is handed. `safeReturnTo` stops it |
| **Optimistic check** | a fast check that trusts a hint (a cookie exists), backed by a real check later. `proxy.ts` is one |
| **PKCE** | "proof key for code exchange", said "pixie": a verifier kept on the server and its hash sent out, so a stolen code is useless |
| **Port, adapter** | a port is the shape the use cases need (a session store); an adapter is one way to fill it (in memory, ElastiCache) |
| **Realm** | an isolated world of users and clients in Keycloak |
| **Redirect (`302`, `303`, `307`)** | a reply that says "go to this address". The browser follows it by itself. `303` always follows with a `GET` |
| **Refresh token** | a voucher for a new access token. Only Keycloak accepts it. It can rotate (a realm setting, off here) |
| **Replay** | using a valid message (a code, a token) a second time. Single-use codes and attempts, and the `nonce`, stop it |
| **`SameSite=Lax`** | a cookie setting: sent when the person navigates here, not on other sites' background requests |
| **Scope** | a bundle of claims a client may request (`openid`, `profile`, `email`) |
| **Service account** | a Keycloak identity for a program, not a person |
| **Session** | the server's record of a signed-in person (the tokens), found by the id in the cookie |
| **Session cookie** | `playground_session`: an opaque id pointing at the tokens in server memory |
| **Session id / ticket** | the random value in the cookie. It holds no information and only means something to the server that made it |
| **`sid`** | Keycloak's session id, inside the tokens |
| **SSO session** | single sign-on: Keycloak's own memory that you are signed in, so a second sign in can skip the password |
| **State** | a random value tying the callback to our attempt |
| **`sub`** | subject: the user's stable Keycloak id. Our link to the account |
| **Token endpoint** | Keycloak's address where codes and refresh tokens are swapped for tokens |
| **Verifier (PKCE)** | a random secret made for one sign in, kept on our server, sent to Keycloak only at the swap |
| **XSS** | cross-site scripting: attacker script running in your page |
