import type { LucideIcon } from "lucide-react"
import { Link } from "react-router-dom"

import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"

type Tone = "neutral" | "ok" | "warn" | "risk"
const TONE: Record<Tone, { tile: string; edge: string; bar: string }> = {
  neutral: { tile: "bg-hover text-ink-2", edge: "var(--border-input)", bar: "bg-charcoal" },
  ok: { tile: "bg-ok-bg text-ok-text", edge: "var(--ok)", bar: "bg-ok" },
  warn: { tile: "bg-warn-bg text-warn-text", edge: "var(--warn)", bar: "bg-warn" },
  risk: { tile: "bg-risk-bg text-risk-text", edge: "var(--risk)", bar: "bg-risk" },
}

/**
 * A number with its context: an icon tile, the value (with "of N" when it is part of a whole), a progress bar and a
 * line of explanation. A card with a destination lifts on hover and opens a view with the matching filter set.
 */
export function StatCard({ icon: Icon, label, value, of, sub, tone = "neutral", to, className }: {
  icon: LucideIcon
  label: string
  value: number | string
  of?: number
  sub?: React.ReactNode
  tone?: Tone
  to?: string
  className?: string
}) {
  const ratio = of ? Math.min(1, Number(value) / of) : null
  const body = (
    <Card interactive={Boolean(to)} className={cn("h-full px-4 py-4", className)} style={{ boxShadow: `inset 0 3px 0 ${TONE[tone].edge}, var(--e1)` }}>
      <div className="flex items-start gap-3">
        <span className={cn("grid size-9 shrink-0 place-items-center rounded-control", TONE[tone].tile)}>
          <Icon className="size-[18px]" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-muted-foreground">{label}</p>
          <p className="mt-0.5 font-mono text-[28px] font-semibold leading-none text-ink">
            {value}
            {of !== undefined && <span className="ml-1.5 text-sm font-medium text-muted-foreground">of {of}</span>}
          </p>
        </div>
        {ratio !== null && <span className="font-mono text-xs font-semibold text-muted-foreground">{Math.round(ratio * 100)}%</span>}
      </div>
      {ratio !== null && (
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-hover" role="img" aria-label={`${value} of ${of}`}>
          <div className={cn("h-full rounded-full transition-[width] duration-500 motion-reduce:transition-none", TONE[tone].bar)} style={{ width: `${ratio * 100}%` }} />
        </div>
      )}
      {sub && <p className="mt-2.5 text-xs text-muted-foreground">{sub}</p>}
    </Card>
  )
  return to ? <Link to={to} className="block no-underline">{body}</Link> : body
}
