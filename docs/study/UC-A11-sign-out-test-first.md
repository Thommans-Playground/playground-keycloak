# UC-A11 Sign out, test first (build lesson)

> **A lesson plan, not a description of the current code.** Adapted from an earlier note for the "aiaas" project. Playground already signs people out: [auth/logout/route.ts](../../apps/web/src/app/auth/logout/route.ts) does it in a few lines. This lesson shows the ports and adapters version, test first, to build **after** the [sign in lesson](UC-A10-sign-in-test-first.md) (it adds `take` and `endSessionUrl` to the ports that lesson creates).

**Requirement:** FR-125 (sign out). **Use case:** [UC-A11](../usecases/UC-A11-sign-out.md). **Prerequisite:** the [sign in lesson](UC-A10-sign-in-test-first.md), and [UC-A13](../usecases/UC-A13-view-my-name-and-role.md) for the profile.

| Lesson label | What it checks | In this repo |
|---|---|---|
| SO-1 | after sign out, the session is gone and the answer is Keycloak's end session address with the ID token as a hint | **AC-79** (FR-125) |
| SO-2 | signing out twice with the same id is harmless, and the old id opens nothing | *proposed*: no criterion yet |

> **Status: plan.** The specification, diagrams, tests and steps are here. The step by step code is written when it is built, so it matches what really happens.

## 1. Specification

| Field | Value |
|---|---|
| Actor | User |
| Trigger | chooses Sign out in the shell's header |
| Main flow | the server forgets the session, clears the cookie, and sends the browser to Keycloak's end session address with the ID token as a hint. Keycloak ends its own session and sends the browser back to `/` |
| Alternative | no session (already signed out): just go home |
| Postcondition | the old session id opens nothing (SO-2). Keycloak asks for the password again on the next sign in |

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant R as POST /auth/logout route
    participant SO as signOut (use case)
    participant SS as SessionStore
    participant IDP as IdentityProvider
    participant KC as Keycloak
    U->>R: Sign out (a form POST, not a link)
    R->>SO: signOut(session id)
    SO->>SS: take(session id)
    SS-->>SO: session (now forgotten)
    SO->>IDP: endSessionUrl(id token)
    IDP-->>SO: Keycloak logout URL
    SO-->>R: where to go
    R-->>U: clear playground_session, redirect to Keycloak
    U->>KC: end session (id_token_hint, post_logout_redirect_uri)
    KC->>KC: end the SSO session, its refresh tokens die
    KC-->>U: redirect to http://localhost:3000/
```

How to read it: two sessions end. Ours (step 3) ends at once, so the old cookie is useless. Keycloak's (step 8) ends when the browser visits it, which is why the browser is sent there instead of the server calling Keycloak quietly.

## 2. Why a POST, not a link

A link (`GET /auth/logout`) can be fired by any other site with an `<img src=...>`, signing people out against their will. A form POST from our own page, with `SameSite=Lax` cookies, cannot be sent from another site with the cookie attached. Small thing, but it is the habit to build.

## 3. Ports change

```mermaid
classDiagram
    class SessionStore {
        <<port>>
        create(session) id
        get(id)
        take(id) session or undefined
    }
    class IdentityProvider {
        <<port>>
        beginLogin()
        completeLogin(callbackUrl, attempt)
        endSessionUrl(idToken) url
    }
```

`take` (read and forget in one step) again, for the same reason as the sign in attempt: once only.

## 4. Tests to write first

`apps/web/tests/unit/sign-out.test.ts`:
- SO-1: after `signOut`, `currentUser(sessionId)` is null, and the answer is the Keycloak URL with the session's ID token.
- SO-2: signing out twice with the same id is harmless and goes home.
- a sign out with no cookie goes home and calls no identity provider.

The fake identity provider gets `endSessionUrl` returning a fake URL that contains the hint, so the test can check it.

## 5. Steps

1. RED: the three tests. GREEN: `take` in `InMemorySessionStore`, `application/sign-out.ts`.
2. `KeycloakIdentityProvider.endSessionUrl`: `oidc.buildEndSessionUrl(config, { id_token_hint, post_logout_redirect_uri })`. The post logout address must be on `playground-web`'s list (already set in the realm file, see section 3 of the [sign in lesson](UC-A10-sign-in-test-first.md)).
3. `app/auth/logout/route.ts` with a `POST` handler: clears the cookie, redirects with status 303 (so the browser follows with a GET).
4. A Sign out form in the shell header, next to "Signed in as".
5. Acceptance: sign out, press Back, reload `/dashboard`: sent to Keycloak, which asks for the password (SO-1). Copy the cookie before signing out, put it back in the developer tools, reload: still signed out (SO-2).

> **Think first.**
> After sign out, Maya's access token is still valid at Keycloak for up to five minutes. Does that matter here? Who holds it?
