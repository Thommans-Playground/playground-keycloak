import { useMemo } from "react"
import { Link } from "react-router-dom"
import type { ColumnDef } from "@tanstack/react-table"

import { useProject } from "@/components/AppShell"
import { DataTable } from "@/components/data-table/DataTable"
import { BuildOrderFlow } from "@/components/flow/BuildOrderFlow"
import { EmptyState, PageHeader } from "@/components/PageHeader"
import { StageChip } from "@/components/StageChip"
import { Badge } from "@/components/ui/badge"
import { Visualise } from "@/components/Visualise"
import { stageInfo } from "@/lib/stages"
import type { UseCase } from "@/lib/types"

const links = (ids: string[]) =>
  ids.length ? (
    <span className="flex flex-wrap gap-x-2">
      {ids.map((id) => (
        <Link key={id} to={`/use-cases/${id}`} onClick={(e) => e.stopPropagation()} className="font-mono text-xs">{id}</Link>
      ))}
    </span>
  ) : (
    <span className="text-subtle">Nothing</span>
  )

export default function BuildOrder() {
  const { useCases } = useProject()
  const columns = useMemo<ColumnDef<UseCase>[]>(
    () => [
      { id: "wave", header: "Wave", accessorFn: (u) => u.wave, cell: ({ getValue }) => <span className="font-mono">{getValue<number>()}</span> },
      {
        id: "use case", header: "Use case", accessorFn: (u) => u.id, sortingFn: "alphanumeric",
        cell: ({ row: { original: u } }) => (
          <Link to={`/use-cases/${u.id}`} className="font-semibold no-underline hover:underline" onClick={(e) => e.stopPropagation()}>
            <span className="font-mono text-[13px] text-ink">{u.id}</span> <span className="text-ink">{u.title}</span>
          </Link>
        ),
      },
      {
        id: "stage", header: "Stage", accessorFn: (u) => u.stage, cell: ({ row }) => <StageChip stage={row.original.stage} />,
        meta: { facet: "Stage", optionLabel: (v) => stageInfo(v as UseCase["stage"]).label },
      },
      { id: "depends", header: "Depends on", accessorFn: (u) => u.dependsOn.join(" "), cell: ({ row }) => links(row.original.dependsOn), enableSorting: false },
      { id: "enables", header: "Enables", accessorFn: (u) => u.enables.join(" "), cell: ({ row }) => links(row.original.enables), enableSorting: false },
      {
        id: "readiness", header: "Waiting for", accessorFn: (u) => (u.blockedBy.length ? "Waiting" : "Ready"),
        cell: ({ row: { original: u } }) => (u.blockedBy.length ? <Badge tone="warn">{u.blockedBy.join(", ")}</Badge> : <span className="text-subtle">Nothing</span>),
        meta: { facet: "Readiness" },
      },
    ],
    [],
  )
  return (
    <>
      <PageHeader title="Build order" description="A use case waits until everything it depends on is built. Wave 0 has no dependencies; each later wave needs an earlier one." />
      <div className="grid grid-cols-[minmax(0,1fr)] gap-3">
        <DataTable
          data={useCases} columns={columns} noun="use case" rowHref={(u) => `/use-cases/${u.id}`} initialSort={{ id: "wave" }}
          searchPlaceholder="Search by id, title or dependency"
          empty={<EmptyState>Nothing to order yet. Create a use case with <code className="font-mono">vbench new uc</code>.</EmptyState>}
        />
        {useCases.length > 0 && (
          <Visualise name="graph" title="the dependency graph" hint="an arrow points from what is built first to what needs it">
            <BuildOrderFlow useCases={useCases} />
          </Visualise>
        )}
      </div>
    </>
  )
}
