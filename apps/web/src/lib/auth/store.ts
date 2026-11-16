import { LOGIN_ATTEMPT_TTL_MS } from "./config";

/** Started at /auth/login, finished at /auth/callback. Used once. */
export type LoginAttempt = {
  state: string;
  nonce: string;
  pkceVerifier: string;
  returnTo: string;
  expiresAt: number;
};

/** The tokens. They live here, on the server. The browser holds only the session id. */
export type Session = {
  idToken: string;
  accessToken: string;
  refreshToken: string | undefined;
  accessExpiresAt: number; // ms since epoch
};

// In memory, kept on globalThis so dev hot reloads do not drop it. A restart signs everyone out.
// Swap for Redis or a database behind these same functions when it must survive restarts.
const g = globalThis as unknown as {
  __attempts?: Map<string, LoginAttempt>;
  __sessions?: Map<string, Session>;
  __refreshing?: Map<string, Promise<Session | null>>;
};
const attempts = (g.__attempts ??= new Map());
const sessions = (g.__sessions ??= new Map());
export const refreshing = (g.__refreshing ??= new Map());

export function saveAttempt(id: string, a: Omit<LoginAttempt, "expiresAt">) {
  attempts.set(id, { ...a, expiresAt: Date.now() + LOGIN_ATTEMPT_TTL_MS });
}

export function takeAttempt(id: string | undefined): LoginAttempt | null {
  if (!id) return null;
  const a = attempts.get(id);
  attempts.delete(id); // single use, even when expired
  return a && a.expiresAt > Date.now() ? a : null;
}

export const getSessionById = (id: string | undefined) => (id ? (sessions.get(id) ?? null) : null);
export const putSession = (id: string, s: Session) => void sessions.set(id, s);
export const dropSession = (id: string) => void sessions.delete(id);
