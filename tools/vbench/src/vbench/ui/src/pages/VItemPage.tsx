import { Link, useParams } from "react-router-dom"

import { useProject } from "@/components/AppShell"
import { EmptyState, PageHeader } from "@/components/PageHeader"
import { RecordFor } from "@/components/records"
import { itemSwitch, phaseSwitch } from "@/lib/crumbs"
import { lineageCrumbs, nodeOfItem } from "@/lib/lineage"
import { phaseOf, phasePath } from "@/lib/v"

export default function VItemPage() {
  const { phase = "", item = "" } = useParams()
  const project = useProject()
  const meta = phaseOf(project, phase)
  const found = project.v.items.find((i) => i.phase === phase && i.id === item) ?? project.v.unplaced.find((i) => i.id === item)

  if (!meta || !found) {
    return (
      <>
        <PageHeader title="Item not found" crumbs={[{ label: "V-cycle" }, { label: meta?.label ?? phase, to: phasePath(phase) }, { label: "Item" }]} />
        <EmptyState>
          That item is not in the project any more. <Link to={phasePath(phase)}>Back to {meta?.label.toLowerCase() ?? "the phase"}</Link>.
        </EmptyState>
      </>
    )
  }

  return (
    <>
      <PageHeader
        crumbs={
          // The trace above it (problem, request, requirement, use case, ...), or the plain trail when it is not on one.
          (() => {
            const node = nodeOfItem(found)
            return (node && lineageCrumbs(project, node)) || [
              { label: "V-cycle" },
              { label: meta.label, to: phasePath(phase), switch: phaseSwitch(project, phase) },
              { label: found.ref, switch: itemSwitch(project, phase, found.id) },
            ]
          })()
        }
      />
      <RecordFor project={project} phase={phase} meta={meta} item={found} variant="page" />
    </>
  )
}
