import { NextResponse, type NextRequest } from "next/server";
import { app } from "@/composition";
import { currentSessionId } from "@/lib/auth/session";
import { methodHasBody } from "@/domain/proxy-methods";

// The browser talks to this route with its cookie. The access token is added in the use case and goes no further.
async function forward(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const { path } = await ctx.params;
  const hasBody = methodHasBody(request.method);
  const sessionId = await currentSessionId();
  const result = await app().callBackend(sessionId, {
    method: request.method,
    path: path.map(encodeURIComponent).join("/"),
    search: request.nextUrl.search,
    body: hasBody ? await request.text() : undefined,
    contentType: hasBody ? (request.headers.get("content-type") ?? "application/json") : undefined,
  });

  if (result.kind === "no_session") {
    return NextResponse.json({ code: "no_session", message: "Sign in first." }, { status: 401 });
  }
  if (result.kind === "unreachable") {
    return NextResponse.json({ code: "api_unreachable", message: "The API is not reachable." }, { status: 502 });
  }
  return new NextResponse(result.body, { status: result.status, headers: { "Content-Type": result.contentType } });
}

// The methods are listed in domain/proxy-methods.ts (a test keeps the two together). PUT and PATCH stay 405.
export { forward as GET, forward as POST, forward as DELETE };
