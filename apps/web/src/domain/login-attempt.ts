/** One sign in in progress: started at /auth/login, finished at /auth/callback. Used once. */
export const LOGIN_ATTEMPT_TTL_MS = 10 * 60 * 1000;

export type LoginAttempt = {
  state: string;
  nonce: string;
  pkceVerifier: string;
  returnTo: string;
  startedAt: number; // ms since epoch
};

export function isExpired(attempt: LoginAttempt, now: number): boolean {
  return now - attempt.startedAt >= LOGIN_ATTEMPT_TTL_MS;
}
