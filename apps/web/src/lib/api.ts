import "server-only";
import { cache } from "react";
import { app } from "@/composition";
import { currentSessionId } from "./auth/session";
import type { DuplicateOf } from "@/domain/duplicate-warning";

export type Account = {
  id: string;
  name: string;
  email: string;
  role: "user" | "administrator";
  status: "pending" | "active" | "deactivated";
  created: string;
  created_by: string | null;
  /** The other accounts with the same email. Missing (an older API) means none. */
  duplicate_of?: DuplicateOf[];
};

export type AuditEntry = {
  id: number;
  at: string;
  actor_id: string | null;
  actor_name: string | null;
  actor_email: string | null;
  action: string;
  target_id: string;
  target_name: string | null;
  target_email: string | null;
  reason: string | null;
};

export type ApiResult<T> = { ok: true; data: T } | { ok: false; status: number; code: string };

/** Server side call to the FastAPI API, for the signed-in person. */
export async function api<T>(path: string): Promise<ApiResult<T>> {
  const sessionId = await currentSessionId(); // before app(): the cookie makes the page dynamic
  const result = await app().callBackend(sessionId, { method: "GET", path: path.replace(/^\//, "") });
  if (result.kind === "no_session") return { ok: false, status: 401, code: "no_session" };
  if (result.kind === "unreachable") return { ok: false, status: 502, code: "api_unreachable" };
  const body = (() => {
    try {
      return JSON.parse(result.body);
    } catch {
      return {};
    }
  })();
  if (result.status >= 200 && result.status < 300) return { ok: true, data: body as T };
  return { ok: false, status: result.status, code: body?.detail?.code ?? body?.code ?? "error" };
}

/** The signed-in person's account. Asked once per request, however many components want it. */
export const getMe = cache(() => api<Account>("/me"));
