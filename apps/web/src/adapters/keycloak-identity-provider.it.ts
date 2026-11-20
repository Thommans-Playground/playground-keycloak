// KeycloakIdentityProvider against the real Keycloak (INTEGRATION=1). Built as composition.ts builds it.
import assert from "node:assert/strict";
import { KeycloakIdentityProvider } from "./keycloak-identity-provider.ts";
import { config, CookieJar, itest, kcAdmin, loginAtKeycloak, throwaway, guardStack } from "../testing/stack.ts";

guardStack();

const newIdp = () =>
  new KeycloakIdentityProvider({
    appUrl: config.appUrl,
    issuer: config.issuer,
    clientId: config.webClientId,
    clientSecret: config.webClientSecret,
  });

/** begin, log in at the real login page, and hand back what completeLogin needs. */
async function realCallback(idp: KeycloakIdentityProvider) {
  const user = await throwaway();
  const attempt = await idp.beginLogin({ register: false });
  const kc = await loginAtKeycloak(attempt.redirectTo, new CookieJar(), user);
  assert.equal(kc.kind, "callback", "Keycloak should send the person back with a code");
  if (kc.kind !== "callback") throw new Error("unreachable");
  return { user, attempt, callbackUrl: new URL(kc.url) };
}

itest("beginLogin builds an authorization URL with PKCE S256, state, nonce, the redirect and the client", async () => {
  const idp = newIdp();
  const { redirectTo, state, nonce, pkceVerifier } = await idp.beginLogin({ register: false });
  const u = new URL(redirectTo);
  assert.equal(u.origin + u.pathname, `${config.issuer}/protocol/openid-connect/auth`);
  assert.equal(u.searchParams.get("code_challenge_method"), "S256");
  assert.ok(u.searchParams.get("code_challenge"));
  assert.equal(u.searchParams.get("state"), state);
  assert.equal(u.searchParams.get("nonce"), nonce);
  assert.equal(u.searchParams.get("redirect_uri"), config.callbackUrl);
  assert.equal(u.searchParams.get("client_id"), config.webClientId);
  assert.equal(u.searchParams.get("response_type"), "code");
  assert.ok(pkceVerifier.length >= 43);
});

itest(
  "completeLogin with the real callback gives a session with tokens and a sensible expiry (Verifies AC-1)",
  async () => {
    const idp = newIdp();
    const { attempt, callbackUrl } = await realCallback(idp);
    const before = Date.now();
    const session = await idp.completeLogin(callbackUrl, attempt);
    assert.ok(session.idToken && session.accessToken && session.refreshToken);
    assert.ok(
      session.accessExpiresAt > before && session.accessExpiresAt <= before + 3_600_000,
      `expiry ${session.accessExpiresAt}`,
    );
  },
);

itest("a callback with another state is refused (Verifies AC-39)", async () => {
  const idp = newIdp();
  const { attempt, callbackUrl } = await realCallback(idp);
  callbackUrl.searchParams.set("state", "not-the-state");
  await assert.rejects(idp.completeLogin(callbackUrl, attempt));
});

itest("a callback for another nonce is refused", async () => {
  const idp = newIdp();
  const { attempt, callbackUrl } = await realCallback(idp);
  await assert.rejects(idp.completeLogin(callbackUrl, { ...attempt, nonce: "not-the-nonce" }));
});

itest("the same code used twice is refused the second time (Verifies AC-39)", async () => {
  const idp = newIdp();
  const { attempt, callbackUrl } = await realCallback(idp);
  await idp.completeLogin(callbackUrl, attempt);
  await assert.rejects(idp.completeLogin(callbackUrl, attempt));
});

itest("a wrong PKCE verifier is refused (Verifies AC-39)", async () => {
  const idp = newIdp();
  const { attempt, callbackUrl } = await realCallback(idp);
  await assert.rejects(idp.completeLogin(callbackUrl, { ...attempt, pkceVerifier: "x".repeat(64) }));
});

itest("refresh gives a new access token", async () => {
  const idp = newIdp();
  const { attempt, callbackUrl } = await realCallback(idp);
  const first = await idp.completeLogin(callbackUrl, attempt);
  const second = await idp.refresh(first);
  assert.notEqual(second.accessToken, first.accessToken);
  assert.ok(second.refreshToken);
  assert.ok(second.accessExpiresAt > Date.now());
});

itest("a refresh token whose Keycloak session ended is refused (Verifies AC-54, the Keycloak half)", async () => {
  const idp = newIdp();
  const { user, attempt, callbackUrl } = await realCallback(idp);
  const session = await idp.completeLogin(callbackUrl, attempt);
  const out = await kcAdmin("POST", `/users/${user.id}/logout`);
  assert.equal(out.status, 204);
  await assert.rejects(idp.refresh(session));
});

itest("endSessionUrl carries id_token_hint and post_logout_redirect_uri", async () => {
  const idp = newIdp();
  const { attempt, callbackUrl } = await realCallback(idp);
  const session = await idp.completeLogin(callbackUrl, attempt);
  const u = new URL(await idp.endSessionUrl(session.idToken));
  assert.equal(u.origin + u.pathname, `${config.issuer}/protocol/openid-connect/logout`);
  assert.equal(u.searchParams.get("id_token_hint"), session.idToken);
  assert.equal(u.searchParams.get("post_logout_redirect_uri"), `${config.appUrl}/`);
});
