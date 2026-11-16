import { useMemo } from "react"
import { Link, useParams, useSearchParams } from "react-router-dom"
import type { ColumnDef } from "@tanstack/react-table"
import { ArrowLeftRight, Layers, ListChecks, Rows3, ScrollText, Search, Table2 } from "lucide-react"

import { useProject } from "@/components/AppShell"
import { DataTable } from "@/components/data-table/DataTable"
import { RecordFor } from "@/components/records"
import { MasterDetail } from "@/components/MasterDetail"
import { EmptyState, PageHeader } from "@/components/PageHeader"
import { RequirementsSheet } from "@/components/RequirementsSheet"
import { Segmented } from "@/components/Segmented"
import { Ring } from "@/components/Ring"
import { StatCard } from "@/components/StatCard"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { phaseSwitch } from "@/lib/crumbs"
import { PHASE_UI } from "@/lib/phases"
import { STATUS_COLOUR, STATUS_ORDER, STATUS_WORD } from "@/lib/status"
import type { ItemStatus, VItem } from "@/lib/types"
import { itemPath, itemsFor, phaseOf, phasePath, tone } from "@/lib/v"
import { cn } from "@/lib/utils"

type View = "sheet" | "table" | "list"

// Kinds whose title is a name from the repo (a file, a function, a diagram) rather than a sentence.
const CODE_NAMED = new Set(["test", "code", "sequence diagram", "class diagram", "state diagram"])

export default function Phase() {
  const { phase = "" } = useParams()
  const project = useProject()
  const [params, setParams] = useSearchParams()
  const meta = phaseOf(project, phase)
  const ui = PHASE_UI[phase]
  const items = useMemo(() => itemsFor(project, phase), [project, phase])

  const columns = useMemo<ColumnDef<VItem>[]>(
    () => [
      {
        id: "ref", header: "Id", accessorFn: (i) => i.ref, sortingFn: "alphanumeric",
        cell: ({ row: { original: i } }) => <span className="whitespace-nowrap font-mono text-xs font-semibold text-ink">{i.ref}</span>,
      },
      {
        id: "item", header: "Name and what it is", accessorFn: (i) => `${i.title} ${i.description}`, sortingFn: "alphanumeric",
        cell: ({ row: { original: i } }) => (
          <div className="min-w-56 max-w-xl">
            <Link to={itemPath(i)} className="font-semibold text-ink no-underline hover:underline" onClick={(e) => e.stopPropagation()}>
              <span className={cn(CODE_NAMED.has(i.kind) && "font-mono text-[13px] [overflow-wrap:anywhere]")}>{i.title}</span>
            </Link>
            {i.description && <p className="mt-0.5 text-ink-2">{i.description}</p>}
            <p className="mt-0.5 font-mono text-xs text-muted-foreground [overflow-wrap:anywhere]">{i.file ? `${i.file}${i.line ? `:${i.line}` : ""}` : ""}</p>
          </div>
        ),
      },
      { id: "kind", header: "Kind", accessorFn: (i) => i.kind, cell: ({ getValue }) => <Badge>{getValue<string>()}</Badge>, meta: { facet: "Kind" } },
      {
        id: "ucs", header: "Use cases", accessorFn: (i) => i.ucs, enableSorting: false,
        cell: ({ getValue }) => <span className="font-mono text-xs">{getValue<string[]>().join(", ") || <span className="text-subtle">None</span>}</span>,
        meta: { facet: "Use case" },
      },
      {
        id: "criteria", header: "Criteria", accessorFn: (i) => i.acs.length,
        cell: ({ row: { original: i } }) => <span className="font-mono text-xs">{i.acs.length ? i.acs.join(", ") : <span className="text-subtle">None</span>}</span>,
      },
      {
        id: "status", header: "Status", accessorFn: (i) => i.status, cell: ({ row: { original: i } }) => <Badge tone={tone(i.status)}>{i.label}</Badge>,
        meta: { facet: "Status", optionLabel: (v) => STATUS_WORD[v as ItemStatus] },
      },
    ],
    [],
  )

  if (!meta || !ui) {
    return (
      <>
        <PageHeader title="Phase not found" crumbs={[{ label: "V-cycle" }, { label: phase }]} />
        <EmptyState>There is no phase called <span className="font-mono">{phase}</span>. Pick one from the sidebar.</EmptyState>
      </>
    )
  }

  const partner = meta.pairs ? project.v.phases.find((p) => p.key === meta.pairs) : undefined
  const Icon = ui.icon
  const selected = params.get("f.status")
  const pickStatus = (key: string | null) => {
    const next = new URLSearchParams(params)
    if (key) next.set("f.status", key)
    else next.delete("f.status")
    next.delete("page")
    setParams(next, { replace: true })
  }
  // Requirements open as a sheet, read top to bottom; every other phase opens as a table. The others are one tap away.
  const home: View = phase === "requirements" ? "sheet" : "table"
  const asked = params.get("view")
  const view: View = (asked === "sheet" && phase === "requirements") || asked === "table" || asked === "list" ? (asked as View) : home
  const setView = (v: View) => {
    const next = new URLSearchParams(params)
    if (v === home) next.delete("view")
    else next.set("view", v)
    setParams(next, { replace: true })
  }
  const noun = phase === "code" ? "code file" : meta.label.toLowerCase().replace(/ tests$/, " test").replace(/s$/, "")
  const q = params.get("q") ?? ""
  const search = (value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set("q", value)
    else next.delete("q")
    setParams(next, { replace: true })
  }
  const clear = () => {
    const next = new URLSearchParams(params)
    for (const k of ["q", "f.status"]) next.delete(k)
    setParams(next, { replace: true })
  }
  const needle = q.trim().toLowerCase()
  const shown = items.filter(
    (i) => (!selected || selected.split(",").includes(i.status)) &&
      (!needle || [i.ref, i.title, i.file ?? "", i.id, ...i.ucs, ...i.acs].some((t) => t.toLowerCase().includes(needle))),
  )
  const groups = STATUS_ORDER.map((s) => ({ key: s, label: STATUS_WORD[s], items: shown.filter((i) => i.status === s) }))
  const current = shown.find((i) => i.id === params.get("item")) ?? shown[0]
  const choose = (i: VItem) => {
    const next = new URLSearchParams(params)
    next.set("item", i.id)
    next.delete("uc")
    setParams(next, { replace: true })
  }
  const slices = STATUS_ORDER.map((s) => ({ key: s, label: STATUS_WORD[s], value: items.filter((i) => i.status === s).length, colour: STATUS_COLOUR[s] }))
  const attention = items.filter((i) => i.status === "warn" || i.status === "risk").length

  return (
    <>
      <PageHeader
        crumbs={[{ label: "V-cycle" }, { label: meta.label, switch: phaseSwitch(project, phase) }]}
        title={<span className="inline-flex items-center gap-3"><Icon className="size-7 text-ink-2" aria-hidden="true" />{meta.label}</span>}
        description={ui.blurb}
        actions={
          partner && (
            <Link to={phasePath(partner.key)} className="inline-flex min-h-11 items-center gap-2 rounded-control border border-input bg-surface px-4 text-sm font-medium text-ink no-underline hover:bg-hover">
              <ArrowLeftRight className="size-4" aria-hidden="true" />
              {meta.arm === "left" ? "Proved by" : "Proves"} {partner.label.toLowerCase()}
            </Link>
          )
        }
      />

      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <Segmented
          label="How to show the items" value={view} onChange={setView}
          segments={[
            ...(phase === "requirements" ? [{ key: "sheet" as const, label: "Sheet", icon: <ScrollText className="size-3.5" aria-hidden="true" /> }] : []),
            { key: "table" as const, label: "Table", icon: <Table2 className="size-3.5" aria-hidden="true" /> },
            { key: "list" as const, label: "List and detail", icon: <Rows3 className="size-3.5" aria-hidden="true" /> },
          ]}
        />
      </div>

      {view === "sheet" ? (
        <RequirementsSheet sheet={project.requirements} />
      ) : (
      <>
      <div className="mb-6 grid gap-4 md:grid-cols-[1fr_1fr_minmax(0,1.4fr)]">
        <div className="grid gap-4">
          <StatCard icon={Layers} label="Items" value={items.length} sub={ui.lists} />
          <StatCard
            icon={ListChecks} label="Use cases involved" value={new Set(items.flatMap((i) => i.ucs)).size} of={project.useCases.length}
            tone={attention ? "warn" : "ok"} sub={attention ? `${attention} ${attention === 1 ? "item needs" : "items need"} attention` : "Everything here is in order"}
          />
        </div>
        <Card className="md:col-span-2">
          <div className="flex flex-wrap items-center justify-center gap-6 px-5 py-4">
            <Ring
              slices={slices} selected={selected} onSelect={pickStatus} centre={{ value: items.length, label: items.length === 1 ? "item" : "items" }}
              description={`How the ${items.length} items here divide by status`}
            />
            <p className="max-w-56 text-[13px] text-muted-foreground">
              Press a slice, or its button, to show only that status. Press it again to clear.
            </p>
          </div>
        </Card>
      </div>

      {view === "table" ? (
        <DataTable
          data={items} columns={columns} noun={noun} rowHref={itemPath} initialSort={{ id: "ref" }}
          searchPlaceholder="Search by id, title, file, use case or criterion"
          empty={<EmptyState>{ui.empty}</EmptyState>}
        />
      ) : (
        <MasterDetail
          label={`The ${noun}s`}
          groups={groups} getId={(i) => i.id} selectedId={current?.id} onSelect={choose}
          toolbar={
            <label className="relative block">
              <span className="sr-only">Search the {noun}s</span>
              <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
              <input
                type="search" value={q} onChange={(e) => search(e.target.value)} placeholder="Search by id, title, file, use case or criterion"
                className="min-h-9 w-full rounded-control border border-input bg-surface pl-8 pr-2 text-[13px] placeholder:text-subtle"
              />
            </label>
          }
          row={(i) => (
            <>
              <span className="size-2.5 shrink-0 rounded-full border" style={{ background: i.status === "neutral" ? "transparent" : STATUS_COLOUR[i.status], borderColor: STATUS_COLOUR[i.status] }} role="img" aria-label={i.label} />
              <span className="min-w-0 flex-1">
                <span className="block truncate font-mono text-xs font-semibold text-ink">{i.ref}</span>
                <span className="block truncate text-[13px] text-ink-2">{i.description || i.title}</span>
              </span>
              <span className="shrink-0 text-xs text-muted-foreground">{i.label}</span>
            </>
          )}
          empty={items.length === 0 ? <EmptyState>{ui.empty}</EmptyState> : <>No {noun}s match. <button type="button" className="font-medium text-link hover:underline" onClick={clear}>Clear the filters</button></>}
          detail={current ? <RecordFor project={project} phase={phase} meta={meta} item={current} variant="pane" /> : <EmptyState>Choose an item in the list to read it here.</EmptyState>}
        />
      )}
      </>
      )}
    </>
  )
}
