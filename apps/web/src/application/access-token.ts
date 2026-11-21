import { needsRefresh, type Session } from "../domain/session.ts";
import type { IdentityProvider, SecurityLog, SessionStore } from "./ports.ts";

/**
 * The access token for a session, refreshed when it is about to expire.
 * One refresh at a time for each session: two requests together share one refresh, so a realm that
 * rotates refresh tokens never sees the old one twice.
 */
export function makeAccessToken(deps: {
  idp: IdentityProvider;
  sessions: SessionStore;
  now: () => number;
  log: SecurityLog;
}) {
  const refreshing = new Map<string, Promise<Session | null>>();

  return async function accessTokenFor(sessionId: string | undefined): Promise<string | null> {
    const session = await deps.sessions.get(sessionId);
    if (!sessionId || !session) return null;
    if (!needsRefresh(session, deps.now())) return session.accessToken;

    let pending = refreshing.get(sessionId);
    if (!pending) {
      pending = deps.idp
        .refresh(session)
        .then(async (fresh) => {
          await deps.sessions.put(sessionId, fresh);
          return fresh;
        })
        .catch(async () => {
          // once for each shared refresh (AC-48)
          deps.log.event({ name: "token_refresh", result: "refused", sessionId, reason: "refresh_refused" });
          deps.log.event({ name: "session_end", result: "ok", sessionId, reason: "refresh_refused" });
          await deps.sessions.take(sessionId); // Keycloak refused: the session ended, or the person was disabled
          return null;
        })
        .finally(() => {
          refreshing.delete(sessionId);
        });
      refreshing.set(sessionId, pending);
    }
    return (await pending)?.accessToken ?? null;
  };
}
