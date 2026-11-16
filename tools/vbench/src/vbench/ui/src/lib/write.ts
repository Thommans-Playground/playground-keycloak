import { useCallback, useEffect, useState } from "react"

import type { Applied, Change, Overlap, Preview, Session } from "@/lib/changes"

export const READ_ONLY: Session = { write: false, token: null, blocked: "", agent: "" }

async function send<T>(path: string, token: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Vbench-Token": token },
    body: JSON.stringify(body),
  })
  const data = (await r.json().catch(() => ({}))) as { error?: string }
  if (!r.ok) throw new Error(data.error ?? `${r.status} ${r.statusText}`)
  return data as T
}

export const previewChange = (token: string, change: Change) => send<Preview>("/api/changes/preview", token, { change })
export const checkOverlap = (token: string, change: Change) => send<Overlap>("/api/assist/overlap", token, { change })
export const applyChange = (token: string, change: Change, digest: string) => send<Applied>("/api/changes/apply", token, { change, digest })
export const commitChange = (token: string, paths: string[], summary: string) =>
  send<{ commit: string; message: string; paths: string[] }>("/api/changes/commit", token, { paths, summary })

/** Whether the server was started with --write, the token that goes with a write, and whether writing is blocked. */
export function useSession(): Session {
  const [session, setSession] = useState<Session>(READ_ONLY)
  const load = useCallback(() => {
    fetch("/api/session")
      .then((r) => (r.ok ? (r.json() as Promise<Session>) : READ_ONLY))
      .then(setSession)
      .catch(() => setSession(READ_ONLY))
  }, [])
  useEffect(() => {
    load()
    window.addEventListener("focus", load)
    return () => window.removeEventListener("focus", load)
  }, [load])
  return session
}
