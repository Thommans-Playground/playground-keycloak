import type { BackendApi, BackendRequest } from "./ports.ts";

export type BackendResult =
  | { kind: "no_session" }
  | { kind: "unreachable" }
  | { kind: "response"; status: number; body: string; contentType: string };

/** Call the API for the person in this session, adding their access token. With no session, make no call. */
export function makeCallBackend(deps: { accessTokenFor: (sessionId: string | undefined) => Promise<string | null>; backend: BackendApi }) {
  return async function callBackend(sessionId: string | undefined, req: BackendRequest): Promise<BackendResult> {
    const token = await deps.accessTokenFor(sessionId);
    if (!token) return { kind: "no_session" };
    try {
      return { kind: "response", ...(await deps.backend.request(req, token)) };
    } catch {
      return { kind: "unreachable" };
    }
  };
}
