import "server-only";
import { cache } from "react";
import { env } from "./auth/config";
import { accessToken } from "./auth/session";

export type Account = {
  id: string;
  name: string;
  email: string;
  role: "user" | "administrator";
  status: "pending" | "active" | "deactivated";
  created: string;
  created_by: string | null;
};

export type AuditEntry = {
  id: number;
  at: string;
  actor_id: string | null;
  action: string;
  target_id: string;
  reason: string | null;
};

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; status: number; code: string };

/** Server side call to the FastAPI API with the person's access token. */
export async function api<T>(path: string): Promise<ApiResult<T>> {
  const token = await accessToken();
  if (!token) return { ok: false, status: 401, code: "no_session" };
  try {
    const res = await fetch(`${env.apiUrl}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    const body = await res.json().catch(() => ({}));
    if (res.ok) return { ok: true, data: body as T };
    const code = body?.detail?.code ?? body?.code ?? "error";
    return { ok: false, status: res.status, code };
  } catch {
    return { ok: false, status: 502, code: "api_unreachable" };
  }
}

/** The signed-in person's account. Asked once per request, however many components want it. */
export const getMe = cache(() => api<Account>("/me"));
