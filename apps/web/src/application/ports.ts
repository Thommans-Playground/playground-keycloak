// What the use cases need from the outside. They know these shapes, never Keycloak, Redis or fetch.
import type { LoginAttempt } from "../domain/login-attempt.ts";
import type { Session } from "../domain/session.ts";

/** Sign in, refresh and sign out, spoken in the use cases' words. Keycloak is one adapter. */
export interface IdentityProvider {
  beginLogin(opts: {
    register: boolean;
  }): Promise<{ redirectTo: string; state: string; nonce: string; pkceVerifier: string }>;
  /** Checks state, nonce and PKCE, and swaps the code for tokens. Throws if anything is wrong. */
  completeLogin(callbackUrl: URL, attempt: { state: string; nonce: string; pkceVerifier: string }): Promise<Session>;
  refresh(session: Session): Promise<Session>;
  endSessionUrl(idToken: string | undefined): Promise<string>;
}

/** `take` reads and forgets in one step, so "once only" is part of the promise. Asynchronous, so Redis fits. */
export interface LoginAttemptStore {
  save(id: string, attempt: LoginAttempt): Promise<void>;
  take(id: string | undefined): Promise<LoginAttempt | null>;
}

export interface SessionStore {
  get(id: string | undefined): Promise<Session | null>;
  put(id: string, session: Session): Promise<void>;
  take(id: string | undefined): Promise<Session | null>;
}

export type BackendRequest = { method: string; path: string; search?: string; body?: string; contentType?: string };

/** The Playground API. The adapter adds the bearer header and the base address. */
export interface BackendApi {
  request(req: BackendRequest, accessToken: string): Promise<{ status: number; body: string; contentType: string }>;
}
