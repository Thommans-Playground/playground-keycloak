import { useMemo } from "react"
import { Link, useSearchParams } from "react-router-dom"
import type { ColumnDef } from "@tanstack/react-table"
import { ClipboardList, ShieldCheck } from "lucide-react"

import { useProject } from "@/components/AppShell"
import { DataTable } from "@/components/data-table/DataTable"
import { EmptyState, PageHeader } from "@/components/PageHeader"
import { Ring } from "@/components/Ring"
import { StatCard } from "@/components/StatCard"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardTitle } from "@/components/ui/card"
import { CRITERION_ORDER, CRITERION_STATE } from "@/lib/status"
import type { Criterion, CriterionState, ItemStatus, Rung, VItem } from "@/lib/types"

const STATE = Object.fromEntries(
  Object.entries(CRITERION_STATE).map(([k, v]) => [k, { label: v.word, tone: v.tone, colour: v.colour }]),
) as Record<CriterionState, { label: string; tone: ItemStatus; colour: string }>
const STATES = CRITERION_ORDER

export default function Traceability() {
  const project = useProject()
  const { criteria, rungs, orphans } = project
  const codeByFile = useMemo(() => new Map(project.v.items.filter((i) => i.kind === "code" && i.file).map((i) => [i.file as string, i])), [project])
  const [params, setParams] = useSearchParams()
  const selected = params.get("ac.f.state")
  const pick = (key: string | null) => {
    const next = new URLSearchParams(params)
    if (key) next.set("ac.f.state", key)
    else next.delete("ac.f.state")
    next.delete("ac.page")
    setParams(next, { replace: true })
  }
  const stats = project.v.stats

  const criteriaCols = useMemo<ColumnDef<Criterion>[]>(
    () => [
      { id: "criterion", header: "Criterion", accessorFn: (c) => c.id, sortingFn: "alphanumeric", cell: ({ getValue }) => <span className="whitespace-nowrap font-mono text-xs font-semibold text-ink">{getValue<string>()}</span> },
      {
        id: "text", header: "What must hold", accessorFn: (c) => c.text, enableSorting: false,
        cell: ({ getValue }) => <span className="block min-w-64 max-w-xl text-ink-2">{getValue<string>() || <span className="text-subtle">No sentence written yet.</span>}</span>,
      },
      {
        id: "uc", header: "Use case", accessorFn: (c) => c.uc ?? "None", meta: { facet: "Use case" },
        cell: ({ row: { original: c } }) => (c.uc ? <Link to={`/use-cases/${c.uc}`} className="font-mono text-xs" onClick={(e) => e.stopPropagation()}>{c.uc}</Link> : "-"),
      },
      {
        id: "state", header: "State", accessorFn: (c) => c.state, meta: { facet: "State", optionLabel: (v) => STATE[v as CriterionState].label },
        cell: ({ row: { original: c } }) => <Badge tone={STATE[c.state].tone}>{STATE[c.state].label}</Badge>,
      },
      {
        id: "tests", header: "Validated by", accessorFn: (c) => c.tests.join(", "), enableSorting: false,
        cell: ({ row: { original: c } }) => <span className="font-mono text-xs">{c.tests.join(", ") || <span className="text-subtle">None</span>}</span>,
      },
    ],
    [],
  )
  const rungCols = useMemo<ColumnDef<Rung>[]>(
    () => [
      {
        id: "uc", header: "Use case", accessorFn: (r) => r.uc, sortingFn: "alphanumeric",
        cell: ({ row: { original: r } }) => <Link to={`/use-cases/${r.uc}`} className="font-mono text-xs" onClick={(e) => e.stopPropagation()}>{r.uc}</Link>,
      },
      {
        id: "code", header: "Realised in", accessorFn: (r) => r.realisedIn.join(", "),
        cell: ({ row: { original: r } }) => (
          <ul className="space-y-1">
            {r.realisedIn.map((f) => {
              const item = codeByFile.get(f)
              return (
                <li key={f}>
                  <span className="font-mono text-xs font-semibold text-ink">{item?.ref ?? f}</span>{" "}
                  <span className="text-ink-2">{item?.description}</span>
                  <span className="block font-mono text-xs text-muted-foreground">{f}</span>
                </li>
              )
            })}
          </ul>
        ),
      },
      {
        id: "verified", header: "Verified by (rung)", accessorFn: (r) => (r.verifiedBy.length ? "Verified" : "No verifying test"), meta: { facet: "Verification" },
        cell: ({ row: { original: r } }) => r.verifiedBy.length
          ? <span className="font-mono text-xs">{r.verifiedBy.map((v) => `${v.file} (${v.rung})`).join(", ")}</span>
          : <Badge tone="risk">No verifying test</Badge>,
      },
    ],
    [codeByFile],
  )
  const loneCols = useMemo<ColumnDef<VItem>[]>(
    () => [
      {
        id: "test", header: "Test", accessorFn: (t) => `${t.ref} ${t.description}`,
        cell: ({ row: { original: t } }) => (
          <div>
            <span className="font-mono text-xs font-semibold text-ink">{t.ref}</span> <span className="text-ink-2">{t.description}</span>
            <p className="font-mono text-xs text-muted-foreground [overflow-wrap:anywhere]">{t.title}  {t.file}{t.line ? `:${t.line}` : ""}</p>
          </div>
        ),
      },
      { id: "why", header: "Why it is not placed", accessorFn: (t) => t.label, cell: ({ row: { original: t } }) => <Badge tone="warn">{t.label}</Badge>, meta: { facet: "Reason" } },
    ],
    [],
  )

  return (
    <>
      <PageHeader title="Traceability" description="Every criterion should reach a test, and every use case in code should reach a verifying test. This proves a link exists, not that the test is good." />

      <div className="mb-6 grid gap-4 md:grid-cols-[1fr_1fr_minmax(0,1.4fr)]">
        <div className="grid gap-4">
          <StatCard icon={ShieldCheck} label="Criteria covered" value={stats.criteria.covered} of={stats.criteria.total} tone={stats.criteria.covered === stats.criteria.total ? "ok" : "warn"} sub="by a marked test" />
          <StatCard icon={ClipboardList} label="Requirements realised" value={stats.requirements.realised} of={stats.requirements.total} tone={stats.requirements.realised === stats.requirements.total ? "ok" : "warn"} sub="by a use case" to="/v/requirements?f.status=warn" />
        </div>
        <Card className="md:col-span-2">
          <div className="flex flex-wrap items-center justify-center gap-6 px-5 py-4">
            <Ring
              slices={STATES.map((s) => ({ key: s, label: STATE[s].label, value: criteria.filter((c) => c.state === s).length, colour: STATE[s].colour }))}
              selected={selected} onSelect={pick} centre={{ value: criteria.length, label: "criteria" }} description="How the acceptance criteria divide by state"
            />
            <p className="max-w-56 text-[13px] text-muted-foreground">Press a slice to filter the criteria below to that state.</p>
          </div>
        </Card>
      </div>

      <h2 className="mb-3 text-[19px] font-semibold text-ink">Acceptance criteria to tests</h2>
      <div className="mb-8">
        <DataTable data={criteria} columns={criteriaCols} noun="criterion" urlPrefix="ac." initialSort={{ id: "criterion" }} searchPlaceholder="Search by criterion, use case or test"
          empty={<EmptyState>No criteria are declared yet.</EmptyState>} />
      </div>

      <h2 className="mb-3 text-[19px] font-semibold text-ink">Use cases in code to verifying tests</h2>
      <div className="mb-8">
        <DataTable data={rungs} columns={rungCols} noun="use case" urlPrefix="rung." initialSort={{ id: "uc" }} searchPlaceholder="Search by use case or file"
          empty={<EmptyState>No code is tagged <span className="font-mono">Realises</span> yet.</EmptyState>} />
      </div>

      {project.v.unplaced.length > 0 && (
        <>
          <Card className="mb-3 border-0 bg-transparent shadow-none"><CardHeader className="px-0 pt-0"><CardTitle className="text-[19px]">Tests that are not on any V yet</CardTitle></CardHeader></Card>
          <DataTable data={project.v.unplaced} columns={loneCols} noun="test" urlPrefix="un." searchPlaceholder="Search by test or file" />
        </>
      )}

      {orphans.length > 0 && (
        <p className="mt-4 text-[13px] text-muted-foreground"><Badge tone="warn">Code with no spec</Badge> <span className="font-mono">{orphans.join(", ")}</span></p>
      )}
    </>
  )
}
