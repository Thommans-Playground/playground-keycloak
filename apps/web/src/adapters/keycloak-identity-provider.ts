import * as client from "openid-client";
import type { IdentityProvider } from "../application/ports.ts";
import type { Session } from "../domain/session.ts";

export type KeycloakSettings = {
  appUrl: string;
  issuer: string;
  /** Set in Docker, where the server reaches Keycloak at a different address than the browser does. */
  internalIssuer?: string;
  clientId: string;
  clientSecret: string;
};

function toSession(t: client.TokenEndpointResponse, previous?: Session): Session {
  return {
    idToken: t.id_token ?? previous?.idToken ?? "",
    accessToken: t.access_token,
    refreshToken: t.refresh_token ?? previous?.refreshToken,
    accessExpiresAt: Date.now() + (t.expires_in ?? 300) * 1000,
  };
}

/** Keycloak over OpenID Connect, with the `openid-client` library. The only file that knows either. */
export class KeycloakIdentityProvider implements IdentityProvider {
  private settings: KeycloakSettings;
  private cached: Promise<client.Configuration> | undefined;

  constructor(settings: KeycloakSettings) {
    this.settings = settings;
  }

  private insecure() {
    return this.settings.issuer.startsWith("http://"); // plain http is fine on localhost only
  }

  private async load(): Promise<client.Configuration> {
    const { issuer, internalIssuer, clientId, clientSecret } = this.settings;
    if (!internalIssuer) {
      return client.discovery(new URL(issuer), clientId, clientSecret, undefined, {
        execute: this.insecure() ? [client.allowInsecureRequests] : [],
      });
    }
    // In Docker the server asks Keycloak at its internal address. Keycloak answers with the browser facing
    // address for the sign in page and the issuer, and the internal one for the token endpoints.
    // openid-client would refuse that mismatch in discovery(), so the metadata is read by hand.
    const res = await fetch(`${internalIssuer}/.well-known/openid-configuration`, { cache: "no-store" });
    if (!res.ok) throw new Error(`discovery failed: ${res.status}`);
    const config = new client.Configuration(
      await res.json(),
      clientId,
      undefined,
      client.ClientSecretPost(clientSecret),
    );
    if (this.insecure()) client.allowInsecureRequests(config);
    return config;
  }

  private configuration() {
    this.cached ??= this.load();
    this.cached.catch(() => (this.cached = undefined)); // retry next time if Keycloak was not up yet
    return this.cached;
  }

  private redirectUri() {
    return `${this.settings.appUrl}/auth/callback`;
  }

  async beginLogin(opts: { register: boolean }) {
    const cfg = await this.configuration();
    const state = client.randomState();
    const nonce = client.randomNonce();
    const pkceVerifier = client.randomPKCECodeVerifier();
    const params: Record<string, string> = {
      redirect_uri: this.redirectUri(),
      scope: "openid profile email",
      state,
      nonce,
      code_challenge: await client.calculatePKCECodeChallenge(pkceVerifier),
      code_challenge_method: "S256",
    };
    if (opts.register) params.prompt = "create"; // Keycloak shows the registration form first
    return { redirectTo: client.buildAuthorizationUrl(cfg, params).href, state, nonce, pkceVerifier };
  }

  async completeLogin(
    callbackUrl: URL,
    attempt: { state: string; nonce: string; pkceVerifier: string },
  ): Promise<Session> {
    const cfg = await this.configuration();
    const tokens = await client.authorizationCodeGrant(cfg, callbackUrl, {
      pkceCodeVerifier: attempt.pkceVerifier,
      expectedState: attempt.state,
      expectedNonce: attempt.nonce,
    });
    return toSession(tokens);
  }

  async refresh(session: Session): Promise<Session> {
    if (!session.refreshToken) throw new Error("no refresh token");
    const tokens = await client.refreshTokenGrant(await this.configuration(), session.refreshToken);
    return toSession(tokens, session);
  }

  async endSessionUrl(idToken: string | undefined): Promise<string> {
    const cfg = await this.configuration();
    return client.buildEndSessionUrl(cfg, {
      post_logout_redirect_uri: `${this.settings.appUrl}/`,
      ...(idToken ? { id_token_hint: idToken } : {}),
    }).href;
  }
}
