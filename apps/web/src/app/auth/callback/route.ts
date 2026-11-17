import { NextResponse, type NextRequest } from "next/server";
import { isSignInFailed } from "@/application/sign-in";
import { app } from "@/composition";
import { env, LOGIN_COOKIE, SESSION_COOKIE } from "@/lib/auth/config";
import { cookieOptions } from "@/lib/auth/session";

export async function GET(request: NextRequest) {
  const fail = (code: string) => {
    const res = NextResponse.redirect(new URL(`/?error=${code}`, env.appUrl));
    res.cookies.delete(LOGIN_COOKIE);
    return res;
  };

  try {
    // Rebuild the address from APP_URL: the request may have come through a proxy.
    const callbackUrl = new URL(`${request.nextUrl.pathname}${request.nextUrl.search}`, env.appUrl);
    const { sessionId, returnTo } = await app().finishLogin(request.cookies.get(LOGIN_COOKIE)?.value, callbackUrl);
    const res = NextResponse.redirect(new URL(returnTo, env.appUrl));
    res.cookies.set(SESSION_COOKIE, sessionId, cookieOptions());
    res.cookies.delete(LOGIN_COOKIE);
    return res;
  } catch (e) {
    return fail(isSignInFailed(e) ? e.code : "login_failed");
  }
}
