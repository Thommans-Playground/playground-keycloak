import { useEffect, useRef, useState } from "react"
import { Check, ChevronDown } from "lucide-react"

import { cn } from "@/lib/utils"

export interface FacetOption {
  value: string
  label: string
  count: number
}

// A multi-select filter for a low-cardinality column. It needs no extra library: a button that opens a list of
// checkboxes with counts, closed by Escape or a click outside.
export function FacetFilter({ label, options, selected, onChange }: {
  label: string
  options: FacetOption[]
  selected: string[]
  onChange: (next: string[]) => void
}) {
  const [open, setOpen] = useState(false)
  const root = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const close = (e: MouseEvent) => !root.current?.contains(e.target as Node) && setOpen(false)
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false)
    document.addEventListener("mousedown", close)
    document.addEventListener("keydown", esc)
    return () => {
      document.removeEventListener("mousedown", close)
      document.removeEventListener("keydown", esc)
    }
  }, [open])

  const toggle = (v: string) => onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v])

  return (
    <div ref={root} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
        className={cn(
          "inline-flex min-h-9 items-center gap-1.5 rounded-control border px-3 text-[13px] font-medium",
          selected.length ? "border-charcoal bg-surface text-ink" : "border-input bg-surface text-ink-2 hover:bg-hover",
        )}
      >
        {label}
        {selected.length > 0 && <span className="rounded-full bg-charcoal px-1.5 text-[11px] font-semibold text-white">{selected.length}</span>}
        <ChevronDown className="size-3.5" aria-hidden="true" />
      </button>
      {open && (
        <div role="listbox" aria-label={label} aria-multiselectable className="absolute left-0 z-20 mt-1 w-60 rounded-card border border-border bg-popover p-1.5 shadow-e3">
          {options.length === 0 && <p className="px-2 py-2 text-xs text-muted-foreground">Nothing to filter by.</p>}
          {options.map((o) => {
            const on = selected.includes(o.value)
            return (
              <button key={o.value} type="button" role="option" aria-selected={on} onClick={() => toggle(o.value)}
                className="flex min-h-9 w-full items-center gap-2 rounded-control px-2 text-left text-[13px] text-ink-2 hover:bg-hover">
                <span className={cn("grid size-4 place-items-center rounded-note border", on ? "border-charcoal bg-charcoal text-white" : "border-input bg-surface")}>
                  {on && <Check className="size-3" aria-hidden="true" />}
                </span>
                <span className="flex-1 truncate">{o.label}</span>
                <span className="font-mono text-xs text-muted-foreground">{o.count}</span>
              </button>
            )
          })}
          {selected.length > 0 && (
            <button type="button" onClick={() => onChange([])} className="mt-1 min-h-9 w-full rounded-control px-2 text-left text-xs font-medium text-link hover:bg-hover">
              Clear {label.toLowerCase()}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
