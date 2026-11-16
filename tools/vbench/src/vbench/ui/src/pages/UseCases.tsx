import { useMemo } from "react"
import { Link } from "react-router-dom"
import type { ColumnDef } from "@tanstack/react-table"

import { useProject } from "@/components/AppShell"
import { DataTable } from "@/components/data-table/DataTable"
import { EmptyState, PageHeader } from "@/components/PageHeader"
import { StageChip } from "@/components/StageChip"
import { Badge } from "@/components/ui/badge"
import { stageInfo } from "@/lib/stages"
import type { UseCase } from "@/lib/types"

export default function UseCases() {
  const { useCases } = useProject()
  const columns = useMemo<ColumnDef<UseCase>[]>(
    () => [
      {
        id: "use case", header: "Use case", accessorFn: (u) => u.id, sortingFn: "alphanumeric",
        cell: ({ row: { original: u } }) => (
          <Link to={`/use-cases/${u.id}`} className="font-semibold no-underline hover:underline" onClick={(e) => e.stopPropagation()}>
            <span className="font-mono text-[13px] text-ink">{u.id}</span> <span className="text-ink">{u.title}</span>
          </Link>
        ),
      },
      { id: "wave", header: "Wave", accessorFn: (u) => u.wave, cell: ({ getValue }) => <span className="font-mono">{getValue<number>()}</span> },
      {
        id: "stage", header: "Stage", accessorFn: (u) => u.stage, cell: ({ row }) => <StageChip stage={row.original.stage} />,
        meta: { facet: "Stage", optionLabel: (v) => stageInfo(v as UseCase["stage"]).label },
      },
      {
        id: "criteria", header: "Criteria covered", accessorFn: (u) => (u.enforced ? u.covered / u.enforced : 0),
        cell: ({ row: { original: u } }) => <span className="font-mono">{u.covered} of {u.enforced}</span>,
      },
      {
        id: "tasks", header: "Tasks closed", accessorFn: (u) => (u.tasks ? u.tasksClosed / u.tasks : 0),
        cell: ({ row: { original: u } }) => <span className="font-mono">{u.tasksClosed} of {u.tasks}</span>,
      },
      {
        id: "readiness", header: "Waiting for", accessorFn: (u) => (u.blockedBy.length ? "Waiting" : "Ready"),
        cell: ({ row: { original: u } }) => (u.blockedBy.length ? <Badge tone="warn">{u.blockedBy.join(", ")}</Badge> : <span className="text-subtle">Nothing</span>),
        meta: { facet: "Readiness" },
      },
      { id: "context", header: "Context", accessorFn: (u) => u.context ?? "Unassigned", meta: { facet: "Context" } },
      { id: "rigor", header: "Rigor", accessorFn: (u) => u.rigor, meta: { facet: "Rigor" } },
      { id: "next", header: "Next step", accessorFn: (u) => u.next, cell: ({ getValue }) => <span className="font-mono text-xs">{getValue<string>()}</span>, enableSorting: false },
    ],
    [],
  )
  return (
    <>
      <PageHeader title="Use cases" description="Search, filter and sort. Ordered by wave, so anything a use case depends on comes first." />
      <DataTable
        data={useCases} columns={columns} noun="use case" rowHref={(u) => `/use-cases/${u.id}`} initialSort={{ id: "wave" }}
        searchPlaceholder="Search by id, title, context or next step"
        empty={<EmptyState>No use cases yet. Create one with <code className="font-mono">vbench new uc</code>.</EmptyState>}
      />
    </>
  )
}
