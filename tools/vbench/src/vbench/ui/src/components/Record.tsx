import { LayoutDashboard } from "lucide-react"
import type { ReactNode } from "react"
import { Link } from "react-router-dom"

import { Scrollspy, SectionChips, useActiveSection, type SpySection } from "@/components/Scrollspy"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { CRITERION_STATE } from "@/lib/status"
import type { CriterionState, ItemStatus } from "@/lib/types"
import { cn } from "@/lib/utils"

export type Variant = "page" | "pane"

// One record, laid out as dim-a lays out a run or a checklist result: a header card with its facts, then sections in a
// column with a rail that follows the reader (a wide window), or a row of jump chips (a narrower one). In a pane the
// sections just stack, since the page around it is already scrolling.
export function RecordFrame({ variant, sections, header, children }: { variant: Variant; sections: SpySection[]; header: ReactNode; children: ReactNode }) {
  const all: SpySection[] = [{ id: "overview", label: "Overview", icon: LayoutDashboard }, ...sections]
  const [active, jump] = useActiveSection(variant === "page" ? all.map((s) => s.id) : [])
  if (variant === "pane") {
    return <div className="space-y-8">{header}{children}</div>
  }
  return (
    <div className="xl:grid xl:grid-cols-[minmax(0,1fr)_11rem] xl:gap-10">
      <div className="min-w-0 space-y-10">
        <div id="overview" className="scroll-mt-32">{header}</div>
        <div className="xl:hidden"><SectionChips sections={all} active={active} jump={jump} /></div>
        {children}
      </div>
      <div className="hidden xl:block"><Scrollspy sections={all} active={active} jump={jump} /></div>
    </div>
  )
}

export function RecordHeader({ overline, id, title, description, chips, facts, actions }: {
  overline: string
  id?: string
  title: ReactNode
  description?: ReactNode
  chips?: ReactNode
  facts?: { label: string; value: ReactNode }[]
  actions?: ReactNode
}) {
  return (
    <Card>
      <div className="space-y-3 px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <p className="t-overline flex flex-wrap items-center gap-2">
            {overline}
            {id && <span className="font-mono text-[13px] font-semibold normal-case tracking-normal text-ink">{id}</span>}
          </p>
          <div className="flex flex-wrap items-center gap-2">
            {actions}
          </div>
        </div>
        <h1 className="t-title max-w-3xl text-ink [overflow-wrap:anywhere]">{title}</h1>
        {description && <p className="t-body max-w-3xl text-ink-2">{description}</p>}
        {chips && <div className="flex flex-wrap items-center gap-2">{chips}</div>}
      </div>
      {facts && facts.length > 0 && (
        <dl className="grid gap-x-8 gap-y-4 rounded-b-card border-t border-divider bg-surface-2 px-6 py-4 sm:grid-cols-2 lg:grid-cols-4">
          {facts.map((f) => (
            <div key={f.label} className="min-w-0">
              <dt className="t-caption text-muted-foreground">{f.label}</dt>
              <dd className="t-subhead mt-0.5 font-medium text-ink [overflow-wrap:anywhere]">{f.value}</dd>
            </div>
          ))}
        </dl>
      )}
    </Card>
  )
}

export function RecordSection({ id, title, hint, count, action, children }: { id: string; title: string; hint?: string; count?: number; action?: ReactNode; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="scroll-mt-32">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id={`${id}-h`} className="t-title text-ink">
          {title}
          {count !== undefined && <span className="ml-2 font-mono text-[15px] font-normal text-muted-foreground">{count}</span>}
        </h2>
        {action && <div className="flex flex-wrap gap-2">{action}</div>}
      </div>
      {hint && <p className="t-subhead mt-1 max-w-3xl text-muted-foreground">{hint}</p>}
      <div className="mt-3">{children}</div>
    </section>
  )
}

// A grouped table: the rows of one kind of related thing, in an inset card.
export function RelatedTable({ label, columns, children, empty }: { label: string; columns: { name: string; className?: string }[]; children: ReactNode; empty?: ReactNode }) {
  const rows = Array.isArray(children) ? children.length : children ? 1 : 0
  return (
    <Card className="overflow-hidden">
      {rows === 0 ? (
        <p className="px-5 py-4 text-sm text-muted-foreground">{empty ?? "Nothing yet."}</p>
      ) : (
        <Table aria-label={label}>
          <TableHeader><TableRow className="hover:bg-transparent">{columns.map((c) => <TableHead key={c.name} className={c.className}>{c.name}</TableHead>)}</TableRow></TableHeader>
          <TableBody>{children}</TableBody>
        </Table>
      )}
    </Card>
  )
}

export const Cell = TableCell
export const Row = TableRow

export const idLink = "whitespace-nowrap font-mono text-[13px] font-semibold text-ink no-underline hover:underline"

export function IdLink({ to, children }: { to: string; children: ReactNode }) {
  return <Link to={to} className={idLink}>{children}</Link>
}

export function StateChip({ state }: { state: CriterionState }) {
  const s = CRITERION_STATE[state]
  return <Badge tone={s.tone}>{s.word}</Badge>
}

export function StatusChip({ status, label }: { status: ItemStatus; label: string }) {
  return label ? <Badge tone={status}>{label}</Badge> : null
}

export const muted = (text: string) => <span className={cn("text-subtle")}>{text}</span>
