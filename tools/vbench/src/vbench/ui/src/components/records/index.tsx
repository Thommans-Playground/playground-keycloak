import { ItemRecord } from "@/components/records/ItemRecord"
import { RequirementRecord } from "@/components/records/RequirementRecord"
import type { Variant } from "@/components/Record"
import type { ProjectState, VItem, VPhase } from "@/lib/types"

// The record for any item: requirements read from the requirements sheet, everything else from the V view.
export function RecordFor({ project, phase, meta, item, variant }: { project: ProjectState; phase: string; meta: VPhase; item: VItem; variant: Variant }) {
  return item.phase === "requirements" ? (
    <RequirementRecord project={project} id={item.id} variant={variant} />
  ) : (
    <ItemRecord project={project} phase={phase} meta={meta} found={item} variant={variant} />
  )
}
