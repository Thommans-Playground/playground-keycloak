import type { BackendApi, BackendRequest } from "../application/ports.ts";

/** The Playground API over HTTP, with the person's access token as a bearer header. */
export class FetchBackendApi implements BackendApi {
  private apiUrl: string;

  constructor(apiUrl: string) {
    this.apiUrl = apiUrl;
  }

  async request(req: BackendRequest, accessToken: string) {
    const hasBody = req.body !== undefined;
    const res = await fetch(`${this.apiUrl}/${req.path}${req.search ?? ""}`, {
      method: req.method,
      headers: {
        Authorization: `Bearer ${accessToken}`,
        ...(hasBody ? { "Content-Type": req.contentType ?? "application/json" } : {}),
      },
      body: req.body,
      cache: "no-store",
    });
    return { status: res.status, body: await res.text(), contentType: res.headers.get("content-type") ?? "application/json" };
  }
}
