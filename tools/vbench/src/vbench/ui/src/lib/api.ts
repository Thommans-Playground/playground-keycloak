import { useCallback, useEffect, useState } from "react"

import type { ProjectState } from "@/lib/types"

async function text(url: string): Promise<string> {
  const r = await fetch(url, { headers: { Accept: "text/plain, application/json" } })
  if (!r.ok) throw new Error(`${r.status} ${r.statusText || "request failed"}`)
  return r.text()
}

export const getFile = (path: string) => text(`/api/file?path=${encodeURIComponent(path)}`)
export const getDiagram = (path: string) => text(`/api/diagram?path=${encodeURIComponent(path)}`)

/** PlantUML's `~h` form: the source as hex, so no deflate step is needed in the browser. */
export function plantUmlUrl(source: string, format: "svg" | "png" = "svg"): string {
  const hex = Array.from(new TextEncoder().encode(source), (b) => b.toString(16).padStart(2, "0")).join("")
  return `/plantuml/${format}/~h${hex}`
}

export interface Loaded<T> {
  data: T | null
  error: string | null
  loading: boolean
  reload: () => void
}

/** The project state, refetched when the window regains focus so the page shows the files as they are now. */
export function useProjectState(): Loaded<ProjectState> {
  const [data, setData] = useState<ProjectState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(() => {
    setLoading(true)
    text("/api/state")
      .then((t) => {
        setData(JSON.parse(t) as ProjectState)
        setError(null)
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    reload()
    window.addEventListener("focus", reload)
    return () => window.removeEventListener("focus", reload)
  }, [reload])

  return { data, error, loading, reload }
}

export function useText(load: (() => Promise<string>) | null, key: string) {
  const [state, setState] = useState<{ text: string | null; error: string | null }>({ text: null, error: null })
  useEffect(() => {
    if (!load) return
    let live = true
    setState({ text: null, error: null })
    load().then(
      (t) => live && setState({ text: t, error: null }),
      (e: unknown) => live && setState({ text: null, error: e instanceof Error ? e.message : String(e) }),
    )
    return () => {
      live = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  return state
}
