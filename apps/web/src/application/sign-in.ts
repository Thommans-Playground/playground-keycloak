import { safeReturnTo } from "../domain/return-to.ts";
import { isExpired } from "../domain/login-attempt.ts";
import type { IdentityProvider, LoginAttemptStore, SessionStore } from "./ports.ts";

export type SignInDeps = {
  idp: IdentityProvider;
  attempts: LoginAttemptStore;
  sessions: SessionStore;
  now: () => number;
  newId: () => string;
};

export type SignInFailure = "login_expired" | "login_refused" | "login_failed" | "identity_provider_unavailable";

export class SignInFailed extends Error {
  readonly code: SignInFailure;

  constructor(code: SignInFailure) {
    super(code);
    this.name = "SignInFailed";
    this.code = code;
  }
}

/** `instanceof` is not safe across Next.js bundles, so recognise the failure by its name and code. */
export function isSignInFailed(e: unknown): e is SignInFailed {
  return e instanceof Error && e.name === "SignInFailed" && typeof (e as { code?: unknown }).code === "string";
}

/** The code a page can show for any error raised while signing in. */
export function signInFailureCode(e: unknown): SignInFailure {
  return isSignInFailed(e) ? e.code : "login_failed";
}

/** Make a login attempt, remember it, and say where to send the person. */
export async function startLogin(deps: SignInDeps, input: { returnTo: string | null | undefined; register: boolean }) {
  const returnTo = safeReturnTo(input.returnTo);
  let begun;
  try {
    begun = await deps.idp.beginLogin({ register: input.register });
  } catch {
    throw new SignInFailed("identity_provider_unavailable"); // AC-44: nothing is kept, no session is made
  }
  const attemptId = deps.newId();
  await deps.attempts.save(attemptId, {
    state: begun.state,
    nonce: begun.nonce,
    pkceVerifier: begun.pkceVerifier,
    returnTo,
    startedAt: deps.now(),
  });
  return { attemptId, redirectTo: begun.redirectTo };
}

/** Finish the attempt the callback belongs to, and make a session. The tokens never leave the store. */
export async function finishLogin(deps: SignInDeps, attemptId: string | undefined, callbackUrl: URL) {
  const attempt = await deps.attempts.take(attemptId); // once only: taking it removes it
  if (!attempt || isExpired(attempt, deps.now())) throw new SignInFailed("login_expired");
  if (callbackUrl.searchParams.has("error")) throw new SignInFailed("login_refused");
  let session;
  try {
    session = await deps.idp.completeLogin(callbackUrl, attempt); // checks state, nonce and PKCE
  } catch {
    throw new SignInFailed("login_failed");
  }
  const sessionId = deps.newId();
  await deps.sessions.put(sessionId, session);
  return { sessionId, returnTo: attempt.returnTo };
}
