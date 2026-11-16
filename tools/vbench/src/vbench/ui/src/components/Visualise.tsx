import { ChevronDown } from "lucide-react"
import { useId, type ReactNode } from "react"
import { useSearchParams } from "react-router-dom"

import { cn } from "@/lib/utils"

// A picture is an extra, never the first thing on a page: the rows come first and this opens the graph that
// explains them, beside them. Closed unless asked for; what is open is kept in the URL (`show=a,b`), so a link
// can open it.
export function Visualise({ name, title, hint, children, className }: {
  name: string
  title: string
  hint?: string
  children: ReactNode
  className?: string
}) {
  const [params, setParams] = useSearchParams()
  const panel = useId()
  const open = (params.get("show") ?? "").split(",").includes(name)
  const toggle = () => {
    const shown = (params.get("show") ?? "").split(",").filter((s) => s && s !== name)
    if (!open) shown.push(name)
    const next = new URLSearchParams(params)
    if (shown.length) next.set("show", shown.join(","))
    else next.delete("show")
    setParams(next, { replace: true })
  }
  return (
    <section className={cn("rounded-card border border-border bg-surface shadow-e1", className)}>
      <button
        type="button" onClick={toggle} aria-expanded={open} aria-controls={panel}
        className="flex min-h-11 w-full items-center justify-between gap-3 rounded-card px-4 py-2 text-left hover:bg-hover"
      >
        <span>
          <span className="text-sm font-semibold text-ink">{open ? "Hide" : "Show"} {title}</span>
          {hint && <span className="ml-2 text-[13px] text-muted-foreground">{hint}</span>}
        </span>
        <ChevronDown className={cn("size-4 shrink-0 text-muted-foreground transition-transform", open && "rotate-180")} aria-hidden="true" />
      </button>
      {open && <div id={panel} className="border-t border-border p-4">{children}</div>}
    </section>
  )
}
