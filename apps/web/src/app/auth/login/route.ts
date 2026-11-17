import { NextResponse, type NextRequest } from "next/server";
import { app } from "@/composition";
import { LOGIN_ATTEMPT_TTL_MS } from "@/domain/login-attempt";
import { LOGIN_COOKIE } from "@/lib/auth/config";
import { cookieOptions } from "@/lib/auth/session";

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  try {
    const { attemptId, redirectTo } = await app().startLogin({
      returnTo: params.get("returnTo"),
      register: params.get("register") === "1",
    });
    const res = NextResponse.redirect(redirectTo);
    res.cookies.set(LOGIN_COOKIE, attemptId, cookieOptions(LOGIN_ATTEMPT_TTL_MS / 1000));
    return res;
  } catch {
    return NextResponse.redirect(new URL("/login?error=identity_provider_unavailable", request.url));
  }
}
