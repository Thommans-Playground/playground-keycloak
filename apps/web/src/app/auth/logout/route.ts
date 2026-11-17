import { NextResponse } from "next/server";
import { app } from "@/composition";
import { env, SESSION_COOKIE } from "@/lib/auth/config";
import { currentSessionId } from "@/lib/auth/session";

// POST only: a link or an image on another site cannot sign a person out.
export async function POST() {
  const sessionId = await currentSessionId();
  const { redirectTo } = await app().signOut(sessionId);
  const res = NextResponse.redirect(redirectTo ?? new URL("/", env.appUrl), 303);
  res.cookies.delete(SESSION_COOKIE);
  return res;
}
