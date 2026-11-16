import { Badge } from "@/components/ui/badge"
import { stageInfo } from "@/lib/stages"
import type { Stage } from "@/lib/types"

export function StageChip({ stage }: { stage: Stage }) {
  const s = stageInfo(stage)
  return <Badge tone={s.tone}>{s.label}</Badge>
}
