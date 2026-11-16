import { Link } from "react-router-dom"

import { PHASE_UI } from "@/lib/phases"
import type { ProjectState, VItem, VPhase } from "@/lib/types"
import { itemPath, itemsFor, itemsOfUc, phasePath, shortTitle, worst } from "@/lib/v"
import { cn } from "@/lib/utils"

// Where each phase sits in the V: [column, row] on a 9 by 5 grid. The left arm descends, the vertex is the
// bottom, the right arm climbs. Dashed lines pair each specification with the test level that proves it.
const POS: Record<string, [number, number]> = {
  requirements: [0, 0], "system-design": [1, 1], architecture: [2, 2], "module-design": [3, 3], code: [4, 4],
  unit: [5, 3], integration: [6, 2], system: [7, 1], acceptance: [8, 0],
}
const ROWS = 5
// Percent coordinates inside the diagram: nodes are 20% wide, so column centres run from 10% to 90% and the
// outer nodes sit flush with the edges instead of overhanging them.
const xPct = (col: number) => 10 + col * 10
const yPct = (row: number) => (row + 0.5) * (100 / ROWS)
const ACCENT: Record<string, string> = {
  ok: "var(--ok)", warn: "var(--warn-text)", risk: "var(--risk)", neutral: "var(--border-input)", none: "var(--border-input)",
}

export type VMode = { kind: "uc"; uc: string } | { kind: "summary" }
export interface Highlight { phase: string; id?: string }

const pairedWith = (phases: VPhase[], key?: string) => phases.find((p) => p.key === key)?.pairs ?? null

function Node({ project, phase, mode, highlight }: { project: ProjectState; phase: VPhase; mode: VMode; highlight?: Highlight }) {
  const Icon = PHASE_UI[phase.key].icon
  const items = mode.kind === "uc" ? itemsOfUc(project, mode.uc).filter((i) => i.phase === phase.key) : itemsFor(project, phase.key)
  const uc = mode.kind === "uc" ? mode.uc : undefined
  const here = highlight?.phase === phase.key
  const pair = !here && pairedWith(project.v.phases, highlight?.phase) === phase.key
  const attention = items.filter((i) => i.status === "warn" || i.status === "risk").length
  const visible = items.slice(0, 3)

  return (
    <div
      className={cn(
        "rounded-card border bg-surface p-2.5 text-left",
        here ? "border-charcoal ring-2 ring-charcoal" : pair ? "border-ink-2 ring-1 ring-ink-2/40" : "border-border shadow-e1",
      )}
      style={{ boxShadow: here || pair ? undefined : `inset 0 3px 0 ${ACCENT[worst(items)]}, var(--e1)` }}
      aria-current={here ? "true" : undefined}
    >
      <div className="flex items-center justify-between gap-2">
        <Link to={phasePath(phase.key, uc)} className="flex min-w-0 items-center gap-1.5 text-[13px] font-semibold text-ink no-underline hover:underline">
          <Icon className="size-4 shrink-0 text-ink-2" aria-hidden="true" />
          <span className="truncate">{phase.label}</span>
        </Link>
        <span className="rounded-full bg-hover px-1.5 text-xs font-semibold text-muted-foreground" aria-label={`${items.length} items`}>
          {items.length}
        </span>
      </div>

      {mode.kind === "summary" ? (
        <p className="mt-1 text-xs text-muted-foreground">
          {items.length === 0 ? "None yet" : attention ? <span className="font-semibold text-risk-text">{attention} to look at</span> : "All in order"}
        </p>
      ) : items.length === 0 ? (
        <p className="mt-1 text-xs text-subtle">None yet</p>
      ) : (
        <ul className="mt-1.5 space-y-1">
          {visible.map((i: VItem) => (
            <li key={i.id}>
              <Link
                to={itemPath(i)}
                title={`${i.ref}: ${i.title}${i.description ? ` - ${i.description}` : ""} (${i.label})`}
                className={cn(
                  "block truncate rounded-note px-1.5 py-0.5 font-mono text-[11px] no-underline hover:bg-hover",
                  here && highlight?.id === i.id ? "bg-hover font-semibold text-ink" : "text-ink-2",
                )}
              >
                {shortTitle(i)}
              </Link>
            </li>
          ))}
          {items.length > visible.length && (
            <li>
              <Link to={phasePath(phase.key, uc)} className="px-1.5 text-[11px] text-link no-underline hover:underline">
                +{items.length - visible.length} more
              </Link>
            </li>
          )}
        </ul>
      )}
    </div>
  )
}

export function VDiagram({ project, mode, highlight }: { project: ProjectState; mode: VMode; highlight?: Highlight }) {
  const phases = project.v.phases
  const left = phases.filter((p) => p.arm === "left")
  const vertex = phases.filter((p) => p.arm === "vertex")
  const right = phases.filter((p) => p.arm === "right") // unit first: the order the levels are climbed
  const lit = (a: string, b: string) => highlight && (highlight.phase === a || highlight.phase === b)
  const pairLines = phases.filter((p) => p.arm === "left" && p.pairs)

  return (
    <div>
      {/* the V itself, on wide screens */}
      <div className="relative hidden h-[700px] lg:block" role="group" aria-label="The V-cycle">
        <svg className="absolute inset-0 size-full" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          <polyline
            points={phases.map((p) => `${xPct(POS[p.key][0])},${yPct(POS[p.key][1])}`).join(" ")}
            fill="none" stroke="var(--border-input)" strokeWidth="2.5" vectorEffect="non-scaling-stroke" strokeLinejoin="round"
          />
          {pairLines.map((p) => {
            const [c1, r1] = POS[p.key]
            const [c2, r2] = POS[p.pairs!]
            const on = lit(p.key, p.pairs!)
            return (
              <line key={p.key} x1={xPct(c1)} y1={yPct(r1)} x2={xPct(c2)} y2={yPct(r2)} vectorEffect="non-scaling-stroke"
                stroke={on ? "var(--charcoal)" : "var(--border-input)"} strokeWidth={on ? 2 : 1.5} strokeDasharray="5 5" />
            )
          })}
        </svg>
        {phases.map((p) => {
          const [c, r] = POS[p.key]
          return (
            <div key={p.key} className="absolute w-[20%] -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${xPct(c)}%`, top: `${yPct(r)}%` }}>
              <Node project={project} phase={p} mode={mode} highlight={highlight} />
            </div>
          )
        })}
        <p className="absolute right-0 top-[58%] w-[17%] text-xs text-muted-foreground">
          Dashed lines pair each specification on the left with the tests that prove it on the right.
        </p>
      </div>

      {/* the same nodes as a list, on narrow screens */}
      <div className="space-y-5 lg:hidden">
        {[["Specify", left], ["Build", vertex], ["Prove", right]].map(([title, group]) => (
          <section key={title as string}>
            <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-subtle">{title as string}</h3>
            <div className="space-y-2">
              {(group as VPhase[]).map((p) => (
                <Node key={p.key} project={project} phase={p} mode={mode} highlight={highlight} />
              ))}
            </div>
          </section>
        ))}
        <p className="text-xs text-muted-foreground">Each specification is proved by the test level that pairs with it.</p>
      </div>
    </div>
  )
}
