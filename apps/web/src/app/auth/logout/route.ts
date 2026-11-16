import { NextResponse } from "next/server";
import { env, SESSION_COOKIE } from "@/lib/auth/config";
import { endSessionUrl } from "@/lib/auth/oidc";
import { endSession } from "@/lib/auth/session";

// POST only: a link or an image on another site cannot sign a person out.
export async function POST() {
  const session = await endSession();
  let target = new URL("/", env.appUrl);
  try {
    target = await endSessionUrl(session?.idToken); // also ends the Keycloak session
  } catch {}
  const res = NextResponse.redirect(target, 303);
  res.cookies.delete(SESSION_COOKIE);
  return res;
}
