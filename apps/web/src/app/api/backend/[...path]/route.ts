import { NextResponse, type NextRequest } from "next/server";
import { env } from "@/lib/auth/config";
import { accessToken } from "@/lib/auth/session";

// The browser talks to this route with its cookie. The access token is added here and goes no further.
async function forward(request: NextRequest, ctx: { params: Promise<{ path: string[] }> }) {
  const token = await accessToken();
  if (!token) {
    return NextResponse.json({ code: "no_session", message: "Sign in first." }, { status: 401 });
  }
  const { path } = await ctx.params;
  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  try {
    const upstream = await fetch(`${env.apiUrl}/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`, {
      method: request.method,
      headers: {
        Authorization: `Bearer ${token}`,
        ...(hasBody ? { "Content-Type": request.headers.get("content-type") ?? "application/json" } : {}),
      },
      body: hasBody ? await request.text() : undefined,
      cache: "no-store",
    });
    return new NextResponse(await upstream.text(), {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
    });
  } catch {
    return NextResponse.json({ code: "api_unreachable", message: "The API is not reachable." }, { status: 502 });
  }
}

export { forward as GET, forward as POST };
