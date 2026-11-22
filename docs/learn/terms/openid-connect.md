---
term: OpenID Connect
say: OpenID Connect (OIDC) is how an app learns who a person is without ever handling their password.
aliases: [OIDC, OpenID Connect, authorization code flow, authorization code]
code:
  - apps/web/src/application/sign-in.ts :: startLogin
  - apps/web/src/application/sign-in.ts :: finishLogin
  - apps/web/src/adapters/keycloak-identity-provider.ts :: buildAuthorizationUrl
guide: 1.3 OAuth 2.0 and OpenID Connect
check: Why is the code in the address not the thing that proves who you are?
---

## In one line

OAuth 2.0 lets an app get permission to act for a person. OpenID Connect adds one more thing on top: a signed answer to "who is this person?". Together they let Playground trust Keycloak's word about a person without ever seeing a password.

## Why we need it

If every app asked for passwords itself, every app would have to store and protect them. Instead the person signs in at Keycloak, which is built for that, and Keycloak tells us the result. We use the authorization code flow: the person is sent to Keycloak, signs in there, and comes back with a short-lived `code`. Our web server, not the browser, swaps that code for tokens in a direct call to Keycloak. The tokens never travel through the browser.

## In our code

`startLogin` makes the address the person is sent to, and `finishLogin` takes the `code` they come back with and swaps it. Both are in `application/sign-in.ts`. `buildAuthorizationUrl` in the Keycloak adapter builds the address.

## Look for yourself

Study guide experiment 1, "Watch the redirect": open the network tab, start a sign in and read the address you are sent to.
