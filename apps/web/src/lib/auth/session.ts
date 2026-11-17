import "server-only";
import { cookies } from "next/headers";
import { app } from "@/composition";
import { env, SESSION_COOKIE } from "./config";

// The Next.js side of sessions: the cookie. What a session holds, and what happens to it, is in application/.

const secure = () => env.appUrl.startsWith("https://");

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

export async function hasSession() {
  const sessionId = await currentSessionId(); // read the cookie first: that makes the page dynamic, so nothing runs at build time
  return app().hasSession(sessionId);
}
