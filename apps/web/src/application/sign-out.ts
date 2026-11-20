import type { IdentityProvider, SessionStore } from "./ports.ts";

/**
 * Forget our session, then say where Keycloak ends its own. Two sessions end, ours at once.
 * `redirectTo` is null, and the person just goes home, when there is nothing to end at Keycloak:
 * no session of ours (no cookie, a second sign out, an expired session), a session store that fails, or an end
 * session address that cannot be built. It never throws, so the route can always clear the cookie.
 */
export async function signOut(deps: { idp: IdentityProvider; sessions: SessionStore }, sessionId: string | undefined) {
  let session;
  try {
    session = await deps.sessions.take(sessionId);
  } catch {
    return { redirectTo: null };
  }
  if (!session) return { redirectTo: null };
  try {
    return { redirectTo: await deps.idp.endSessionUrl(session.idToken) };
  } catch {
    return { redirectTo: null };
  }
}
