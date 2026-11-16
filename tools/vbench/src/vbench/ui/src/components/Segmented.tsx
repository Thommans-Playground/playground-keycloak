import { useRef, type ReactNode } from "react"

import { cn } from "@/lib/utils"

export interface Segment<K extends string> {
  key: K
  label: string
  icon?: ReactNode
}

// A segmented control: a few mutually exclusive views of the same content, one always chosen. It is one stop for
// the Tab key; the arrow keys move the choice.
export function Segmented<K extends string>({ label, segments, value, onChange, className }: {
  label: string
  segments: Segment<K>[]
  value: K
  onChange: (key: K) => void
  className?: string
}) {
  const group = useRef<HTMLDivElement>(null)

  const move = (e: React.KeyboardEvent) => {
    const step = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0
    if (!step) return
    e.preventDefault()
    const at = segments.findIndex((s) => s.key === value)
    const next = segments[(at + step + segments.length) % segments.length]
    onChange(next.key)
    requestAnimationFrame(() => group.current?.querySelector<HTMLElement>(`[data-key="${next.key}"]`)?.focus())
  }

  return (
    <div ref={group} role="radiogroup" aria-label={label} onKeyDown={move} className={cn("inline-flex rounded-control bg-hover p-0.5", className)}>
      {segments.map((s) => {
        const on = s.key === value
        return (
          <button
            key={s.key} type="button" role="radio" aria-checked={on} data-key={s.key} tabIndex={on ? 0 : -1} onClick={() => onChange(s.key)}
            className={cn(
              "inline-flex min-h-9 items-center gap-1.5 rounded-[6px] px-3.5 text-[13px] font-medium transition-colors",
              on ? "bg-surface text-ink shadow-e1" : "text-muted-foreground hover:text-ink",
            )}
          >
            {s.icon}{s.label}
          </button>
        )
      })}
    </div>
  )
}
