import { useMemo } from "react"
import { Handle, MarkerType, Position, type NodeProps } from "@xyflow/react"
import { useNavigate } from "react-router-dom"

import { FlowFrame } from "@/components/flow/FlowFrame"
import { StageChip } from "@/components/StageChip"
import { layoutBuildOrder, UC_NODE, type UcNodeData } from "@/lib/flow-layout"
import { stageInfo } from "@/lib/stages"
import type { UseCase } from "@/lib/types"
import { cn } from "@/lib/utils"

const BORDER = { neutral: "border-border bg-surface", warn: "border-warn/50 bg-[color-mix(in_srgb,var(--warn-bg)_40%,var(--surface))]", ok: "border-ok/50 bg-[color-mix(in_srgb,var(--ok-bg)_50%,var(--surface))]" }

function UseCaseNode({ data }: NodeProps) {
  const d = data as UcNodeData
  const tone = stageInfo(d.stage).tone
  const ratio = d.enforced ? d.covered / d.enforced : 0
  return (
    <div className={cn("cursor-pointer rounded-card border px-3 py-2.5 text-left shadow-e1 transition-shadow hover:shadow-e2", BORDER[tone])} style={{ width: UC_NODE.width }}>
      <Handle type="target" position={Position.Left} className="size-1.5! border-0! bg-muted-foreground!" />
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-xs font-semibold text-ink">{d.id}</span>
        <StageChip stage={d.stage} />
      </div>
      <p className="mt-1 truncate text-[13px] font-medium text-ink-2">{d.title}</p>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-hover" role="img" aria-label={`${d.covered} of ${d.enforced} criteria covered`}>
        <div className="h-full rounded-full bg-ok" style={{ width: `${ratio * 100}%` }} />
      </div>
      <p className="mt-1 text-[10px] text-muted-foreground">
        {d.waiting.length ? `Waiting for ${d.waiting.join(", ")}` : `Wave ${d.wave} · ${d.covered} of ${d.enforced} criteria covered`}
      </p>
      <Handle type="source" position={Position.Right} className="size-1.5! border-0! bg-muted-foreground!" />
    </div>
  )
}

const nodeTypes = { useCase: UseCaseNode }

/** The build order as a graph: a column per wave, an arrow from what must be built first to what needs it. */
export function BuildOrderFlow({ useCases }: { useCases: UseCase[] }) {
  const navigate = useNavigate()
  const layout = useMemo(() => layoutBuildOrder(useCases), [useCases])
  const edges = useMemo(
    () => layout.edges.map((e) => {
      const waiting = Boolean((e.data as { waiting?: boolean }).waiting)
      const colour = waiting ? "var(--warn)" : "var(--ok)"
      return { ...e, style: { stroke: colour, strokeWidth: 1.75 }, markerEnd: { type: MarkerType.ArrowClosed, color: colour } }
    }),
    [layout],
  )
  return (
    <div>
      <FlowFrame
        label="The build order of the use cases" nodes={layout.nodes} edges={edges} nodeTypes={nodeTypes} width={layout.width} height={layout.height}
        onNodeClick={(_, n) => navigate(`/use-cases/${n.id}`)}
        words={
          <ol>
            {useCases.map((u) => (
              <li key={u.id}>{u.id} {u.title}: wave {u.wave}, {stageInfo(u.stage).label}{u.dependsOn.length ? `, depends on ${u.dependsOn.join(", ")}` : ""}.</li>
            ))}
          </ol>
        }
      />
      <p className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-0.5 w-5 bg-ok" aria-hidden="true" /> the dependency is built</span>
        <span className="inline-flex items-center gap-1.5"><i className="inline-block h-0.5 w-5 bg-warn" aria-hidden="true" /> still waiting for it (animated)</span>
        <span>Click a use case to open it.</span>
      </p>
    </div>
  )
}
