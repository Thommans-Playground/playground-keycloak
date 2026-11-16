import { NextResponse, type NextRequest } from "next/server";

// A quick gate: no session cookie, no protected page. The pages check the session for real.
export function proxy(request: NextRequest) {
  if (!request.cookies.has("playground_session")) {
    const login = new URL("/auth/login", request.url);
    login.searchParams.set("returnTo", request.nextUrl.pathname + request.nextUrl.search);
    return NextResponse.redirect(login);
  }
  return NextResponse.next();
}

export const config = { matcher: ["/dashboard/:path*", "/admin/:path*"] };
