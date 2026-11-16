import { NextResponse, type NextRequest } from "next/server";
import { env, LOGIN_COOKIE, SESSION_COOKIE } from "@/lib/auth/config";
import { finishLogin } from "@/lib/auth/oidc";
import { cookieOptions, newSessionId } from "@/lib/auth/session";
import { putSession, takeAttempt } from "@/lib/auth/store";

export async function GET(request: NextRequest) {
  const fail = (code: string) => {
    const res = NextResponse.redirect(new URL(`/?error=${code}`, env.appUrl));
    res.cookies.delete(LOGIN_COOKIE);
    return res;
  };

  const attempt = takeAttempt(request.cookies.get(LOGIN_COOKIE)?.value);
  if (!attempt) return fail("login_expired");
  if (request.nextUrl.searchParams.has("error")) return fail("login_refused");

  try {
    // Rebuild the address from APP_URL: the request may have come through a proxy.
    const callbackUrl = new URL(`${request.nextUrl.pathname}${request.nextUrl.search}`, env.appUrl);
    const session = await finishLogin(callbackUrl, attempt); // checks state, nonce and PKCE
    const id = newSessionId();
    putSession(id, session);
    const res = NextResponse.redirect(new URL(attempt.returnTo, env.appUrl));
    res.cookies.set(SESSION_COOKIE, id, cookieOptions());
    res.cookies.delete(LOGIN_COOKIE);
    return res;
  } catch {
    return fail("login_failed");
  }
}
