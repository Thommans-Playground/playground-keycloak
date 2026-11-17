import type { IdentityProvider, SessionStore } from "./ports.ts";

/**
 * Forget our session, then say where Keycloak ends its own. Two sessions end, ours at once.
 * `redirectTo` is null when Keycloak cannot be reached: the person just goes home.
 */
export async function signOut(deps: { idp: IdentityProvider; sessions: SessionStore }, sessionId: string | undefined) {
  const session = await deps.sessions.take(sessionId);
  try {
    return { redirectTo: await deps.idp.endSessionUrl(session?.idToken) };
  } catch {
    return { redirectTo: null };
  }
}
