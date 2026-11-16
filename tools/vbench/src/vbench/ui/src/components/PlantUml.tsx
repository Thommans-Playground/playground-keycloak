import { useState } from "react"

import { Skeleton } from "@/components/ui/skeleton"
import { getDiagram, plantUmlUrl, useText } from "@/lib/api"

// The server inlines the shared `!include` files, then a PlantUML renderer (the compose service) draws it.
// With no renderer, the source is shown instead, so the page is never empty.
export function PlantUml({ path }: { path: string }) {
  const { text, error } = useText(() => getDiagram(path), path)
  const [failed, setFailed] = useState<string | null>(null)

  if (error) return <p className="text-[13px] text-muted-foreground">This diagram could not be read: {error}.</p>
  if (text === null) return <Skeleton className="h-64 w-full" />

  const url = plantUmlUrl(text)
  return (
    <div>
      {failed !== path ? (
        <img
          key={path}
          src={url}
          alt={`Diagram ${path}`}
          onError={() => setFailed(path)}
          className="mx-auto max-h-[70vh] max-w-full rounded-control bg-white p-3"
        />
      ) : (
        <p className="mb-2 text-[13px] text-muted-foreground">
          No PlantUML renderer answered, so here is the source. Start the dashboard with <code className="font-mono">docker compose up</code> from the vbench repo to get the renderer.
        </p>
      )}
      <details className="mt-3" open={failed === path}>
        <summary className="cursor-pointer text-[13px] font-medium text-link">PlantUML source</summary>
        <pre className="mt-2 max-h-96 overflow-auto rounded-control border border-border bg-surface-2 p-3 font-mono text-xs">{text}</pre>
      </details>
    </div>
  )
}
