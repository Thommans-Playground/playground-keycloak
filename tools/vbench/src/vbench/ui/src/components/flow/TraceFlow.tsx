import { useMemo } from "react"
import { Handle, MarkerType, Position, type NodeProps } from "@xyflow/react"
import { useNavigate } from "react-router-dom"

import { FlowFrame } from "@/components/flow/FlowFrame"
import { Badge } from "@/components/ui/badge"
import { layoutTrace, TRACE_NODE, type TraceKind, type TraceNodeData } from "@/lib/flow-layout"
import type { ProjectState } from "@/lib/types"
import { cn } from "@/lib/utils"

const KIND: Record<TraceKind, { word: string; accent: string }> = {
  requirement: { word: "Requirement", accent: "var(--charcoal)" },
  useCase: { word: "Use case", accent: "var(--brand)" },
  task: { word: "Task", accent: "var(--border-input)" },
  criterion: { word: "Criterion", accent: "var(--border-input)" },
  test: { word: "Test", accent: "var(--border-input)" },
}

function TraceNode({ data }: NodeProps) {
  const d = data as TraceNodeData
  const hub = d.kind === "useCase"
  return (
    <div
      className={cn("rounded-control border bg-surface px-2.5 py-1.5 text-left shadow-e1", d.href && "cursor-pointer hover:shadow-e2", hub ? "border-charcoal ring-1 ring-charcoal" : "border-border")}
      style={{ width: TRACE_NODE.width, minHeight: TRACE_NODE.height, boxShadow: `inset 3px 0 0 ${KIND[d.kind].accent}, var(--e1)` }}
    >
      <Handle type="target" position={Position.Left} className="size-1.5! border-0! bg-muted-foreground!" />
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-wide text-subtle">{KIND[d.kind].word}</span>
        {d.label && <Badge tone={d.kind === "useCase" ? "neutral" : d.status} className="px-1.5 text-[10px]">{d.label}</Badge>}
      </div>
      <p className={cn("truncate text-xs font-semibold text-ink", d.kind !== "useCase" && "font-mono")} title={d.title}>{d.title}</p>
      {d.sub && <p className="truncate text-[11px] text-muted-foreground" title={d.sub}>{d.sub}</p>}
      <Handle type="source" position={Position.Right} className="size-1.5! border-0! bg-muted-foreground!" />
    </div>
  )
}

const nodeTypes = { trace: TraceNode }

/** From a requirement through the use case, its tasks and criteria, to the tests that prove them. */
export function TraceFlow({ project, uc }: { project: ProjectState; uc: string }) {
  const navigate = useNavigate()
  const layout = useMemo(() => layoutTrace(project, uc), [project, uc])
  const edges = useMemo(
    () => layout.edges.map((e) => ({ ...e, style: { stroke: "var(--ink-2)", strokeWidth: 1.5, ...e.style }, markerEnd: { type: MarkerType.ArrowClosed, color: "var(--ink-2)" } })),
    [layout],
  )
  return (
    <div>
      <FlowFrame
        label={`The trace for ${uc}, from requirements to tests`} nodes={layout.nodes} edges={edges} nodeTypes={nodeTypes} width={layout.width} height={layout.height}
        onNodeClick={(_, n) => { const href = (n.data as TraceNodeData).href; if (href) navigate(href) }}
        words={
          <ol>
            {layout.nodes.map((n) => { const d = n.data as TraceNodeData; return <li key={n.id}>{KIND[d.kind].word} {d.title}: {d.label || "no status"}.</li> })}
          </ol>
        }
      />
      <p className="mt-2 text-xs text-muted-foreground">
        A solid arrow is a link the specs and tags record; a dashed one is attached to the use case because nothing closer is named.
        Click a requirement, task or test to open it.
      </p>
    </div>
  )
}
