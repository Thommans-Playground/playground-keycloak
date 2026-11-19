// Stand-ins for the ports, so a use case runs in milliseconds with no Keycloak and no network.
import type { IdentityProvider, BackendApi, BackendRequest } from "../application/ports.ts";
import type { Session } from "../domain/session.ts";

/** A strict fake: like Keycloak it checks `state` and refuses a code that was used before. */
export class FakeIdentityProvider implements IdentityProvider {
  private begun = 0;
  private usedCodes = new Set<string>();
  refreshes = 0;
  refreshFails = false;
  endSessionFails = false;
  /** a test can make Keycloak unreachable when a sign in starts */
  beginFails = false;
  /** a test can hold a refresh open to prove that two callers share one refresh */
  gate: Promise<void> = Promise.resolve();
  lastBegin: { register: boolean } | undefined;

  private now: () => number;

  constructor(now: () => number = () => Date.now()) {
    this.now = now;
  }

  async beginLogin(opts: { register: boolean }) {
    if (this.beginFails) throw new Error("the identity provider cannot be reached");
    this.lastBegin = opts;
    const n = ++this.begun;
    return {
      redirectTo: `https://kc.test/auth?state=state-${n}&register=${opts.register}`,
      state: `state-${n}`,
      nonce: `nonce-${n}`,
      pkceVerifier: `verifier-${n}`,
    };
  }

  async completeLogin(callbackUrl: URL, attempt: { state: string; nonce: string; pkceVerifier: string }): Promise<Session> {
    const code = callbackUrl.searchParams.get("code");
    if (callbackUrl.searchParams.get("state") !== attempt.state) throw new Error("state does not match");
    if (!code || this.usedCodes.has(code)) throw new Error("the code is missing or was used before");
    this.usedCodes.add(code);
    return { idToken: `id-${code}`, accessToken: `at-${code}`, refreshToken: `rt-${code}`, accessExpiresAt: this.now() + 300_000 };
  }

  async refresh(session: Session): Promise<Session> {
    this.refreshes++;
    await this.gate;
    if (this.refreshFails) throw new Error("Keycloak refused the refresh");
    return { ...session, accessToken: `at-refreshed-${this.refreshes}`, accessExpiresAt: this.now() + 300_000 };
  }

  async endSessionUrl(idToken: string | undefined): Promise<string> {
    if (this.endSessionFails) throw new Error("Keycloak is down");
    return `https://kc.test/logout?hint=${idToken ?? ""}`;
  }
}

/** Records what it was asked, answers what a test tells it to. */
export class FakeBackendApi implements BackendApi {
  calls: Array<{ req: BackendRequest; accessToken: string }> = [];
  fail = false;
  answer = { status: 200, body: "{}", contentType: "application/json" };

  async request(req: BackendRequest, accessToken: string) {
    if (this.fail) throw new Error("the API is down");
    this.calls.push({ req, accessToken });
    return this.answer;
  }
}
