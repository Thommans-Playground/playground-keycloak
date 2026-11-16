import "server-only";
import { randomBytes } from "node:crypto";
import { cookies } from "next/headers";
import { env, SESSION_COOKIE } from "./config";
import { refresh } from "./oidc";
import { dropSession, getSessionById, putSession, refreshing, type Session } from "./store";

const secure = () => env.appUrl.startsWith("https://");

export const newSessionId = () => randomBytes(32).toString("base64url");

export const cookieOptions = (maxAgeSeconds?: number) => ({
  httpOnly: true, // JavaScript in the page cannot read it
  sameSite: "lax" as const, // sent on the redirect back from Keycloak, not on cross-site posts
  secure: secure(),
  path: "/",
  ...(maxAgeSeconds ? { maxAge: maxAgeSeconds } : {}),
});

export async function currentSessionId() {
  return (await cookies()).get(SESSION_COOKIE)?.value;
}

/**
 * The access token for this browser's session, refreshed when it is about to expire.
 * One refresh at a time per session: refresh tokens rotate, so two at once would log the person out.
 */
export async function accessToken(): Promise<string | null> {
  const id = await currentSessionId();
  const session = getSessionById(id);
  if (!id || !session) return null;
  if (session.accessExpiresAt - Date.now() > 30_000) return session.accessToken;

  let pending = refreshing.get(id);
  if (!pending) {
    pending = refresh(session)
      .then((fresh) => (putSession(id, fresh), fresh))
      .catch(() => (dropSession(id), null)) // Keycloak refused: session ended or person disabled
      .finally(() => refreshing.delete(id));
    refreshing.set(id, pending);
  }
  return (await pending)?.accessToken ?? null;
}

export async function hasSession() {
  return getSessionById(await currentSessionId()) !== null;
}

export async function endSession(): Promise<Session | null> {
  const id = await currentSessionId();
  const session = getSessionById(id);
  if (id) dropSession(id);
  return session;
}
