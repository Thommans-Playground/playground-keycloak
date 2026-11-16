import { useEffect, useId, useRef, useState } from "react"

import { Skeleton } from "@/components/ui/skeleton"

let ready: Promise<typeof import("mermaid").default> | null = null

// Mermaid is large, so it loads on first use. `strict` stops diagram text from running script.
function mermaid() {
  ready ??= import("mermaid").then(({ default: m }) => {
    m.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral", fontFamily: "-apple-system, BlinkMacSystemFont, system-ui, sans-serif" })
    return m
  })
  return ready
}

export function Mermaid({ source }: { source: string }) {
  const id = "m" + useId().replace(/[^a-zA-Z0-9]/g, "")
  const host = useRef<HTMLDivElement>(null)
  const [state, setState] = useState<"loading" | "ok" | "error">("loading")

  useEffect(() => {
    let live = true
    setState("loading")
    mermaid()
      .then((m) => m.render(id, source))
      .then(({ svg }) => {
        if (live && host.current) {
          host.current.innerHTML = svg
          setState("ok")
        }
      })
      .catch(() => live && setState("error"))
    return () => {
      live = false
    }
  }, [id, source])

  if (state === "error") {
    return (
      <div>
        <p className="mb-2 text-[13px] text-muted-foreground">The diagram could not be drawn, so here is its source.</p>
        <pre className="overflow-x-auto rounded-control border border-border bg-surface-2 p-3 font-mono text-xs">{source}</pre>
      </div>
    )
  }
  return (
    <div>
      {state === "loading" && <Skeleton className="h-40 w-full" />}
      <div ref={host} className="overflow-x-auto rounded-control bg-white p-3 [&_svg]:mx-auto [&_svg]:h-auto [&_svg]:max-w-full" role="img" aria-label="Diagram" />
    </div>
  )
}
