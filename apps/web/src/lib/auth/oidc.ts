import "server-only";
import * as client from "openid-client";
import { env } from "./config";
import type { Session } from "./store";

let cached: Promise<client.Configuration> | undefined;

const insecure = () => env.issuer.startsWith("http://"); // plain http is fine on localhost only

async function load(): Promise<client.Configuration> {
  if (!env.internalIssuer) {
    return client.discovery(new URL(env.issuer), env.clientId, env.clientSecret, undefined, {
      execute: insecure() ? [client.allowInsecureRequests] : [],
    });
  }
  // In Docker the server asks Keycloak at its internal address. Keycloak answers with the browser facing
  // address for the sign in page and the issuer, and the internal one for the token endpoints.
  // openid-client would refuse that mismatch in discovery(), so the metadata is read by hand.
  const res = await fetch(`${env.internalIssuer}/.well-known/openid-configuration`, { cache: "no-store" });
  if (!res.ok) throw new Error(`discovery failed: ${res.status}`);
  const config = new client.Configuration(await res.json(), env.clientId, undefined, client.ClientSecretPost(env.clientSecret));
  if (insecure()) client.allowInsecureRequests(config);
  return config;
}

function configuration() {
  cached ??= load();
  cached.catch(() => (cached = undefined)); // retry next time if Keycloak was not up yet
  return cached;
}

const redirectUri = () => `${env.appUrl}/auth/callback`;

export async function beginLogin(opts: { register?: boolean }) {
  const cfg = await configuration();
  const state = client.randomState();
  const nonce = client.randomNonce();
  const pkceVerifier = client.randomPKCECodeVerifier();
  const params: Record<string, string> = {
    redirect_uri: redirectUri(),
    scope: "openid profile email",
    state,
    nonce,
    code_challenge: await client.calculatePKCECodeChallenge(pkceVerifier),
    code_challenge_method: "S256",
  };
  if (opts.register) params.prompt = "create"; // Keycloak shows the registration form first
  return { url: client.buildAuthorizationUrl(cfg, params), state, nonce, pkceVerifier };
}

function toSession(t: client.TokenEndpointResponse, previous?: Session): Session {
  return {
    idToken: t.id_token ?? previous?.idToken ?? "",
    accessToken: t.access_token,
    refreshToken: t.refresh_token ?? previous?.refreshToken,
    accessExpiresAt: Date.now() + (t.expires_in ?? 300) * 1000,
  };
}

export async function finishLogin(
  callbackUrl: URL,
  attempt: { state: string; nonce: string; pkceVerifier: string },
): Promise<Session> {
  const cfg = await configuration();
  const tokens = await client.authorizationCodeGrant(cfg, callbackUrl, {
    pkceCodeVerifier: attempt.pkceVerifier,
    expectedState: attempt.state,
    expectedNonce: attempt.nonce,
  });
  return toSession(tokens);
}

export async function refresh(session: Session): Promise<Session> {
  if (!session.refreshToken) throw new Error("no refresh token");
  const tokens = await client.refreshTokenGrant(await configuration(), session.refreshToken);
  return toSession(tokens, session);
}

export async function endSessionUrl(idToken: string | undefined) {
  const cfg = await configuration();
  return client.buildEndSessionUrl(cfg, {
    post_logout_redirect_uri: `${env.appUrl}/`,
    ...(idToken ? { id_token_hint: idToken } : {}),
  });
}
