import { NextResponse, type NextRequest } from "next/server";
import { LOGIN_ATTEMPT_TTL_MS, LOGIN_COOKIE } from "@/lib/auth/config";
import { beginLogin } from "@/lib/auth/oidc";
import { safeReturnTo } from "@/lib/auth/safe-return-to";
import { cookieOptions, newSessionId } from "@/lib/auth/session";
import { saveAttempt } from "@/lib/auth/store";

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const returnTo = safeReturnTo(params.get("returnTo"));
  try {
    const { url, ...attempt } = await beginLogin({ register: params.get("register") === "1" });
    const id = newSessionId();
    saveAttempt(id, { ...attempt, returnTo });
    const res = NextResponse.redirect(url);
    res.cookies.set(LOGIN_COOKIE, id, cookieOptions(LOGIN_ATTEMPT_TTL_MS / 1000));
    return res;
  } catch {
    return NextResponse.redirect(new URL("/login?error=identity_provider_unavailable", request.url));
  }
}
