import type { ReactNode } from "react"
import { Background, Controls, ReactFlow, type Edge, type Node, type NodeMouseHandler, type NodeTypes } from "@xyflow/react"
import "@xyflow/react/dist/style.css"

// A graph in a frame that takes its proportions from the layout (so it hugs the graph instead of leaving a band above
// and below), with the zoom controls, and the same content in words for a screen reader. Read-only: nodes cannot be
// dragged or connected, and scrolling the page does not zoom the graph. `nodeTypes` must be a module-level constant.
export function FlowFrame({ nodes, edges, nodeTypes, width, height, onNodeClick, words, label }: {
  nodes: Node[]
  edges: Edge[]
  nodeTypes: NodeTypes
  width: number
  height: number
  onNodeClick?: NodeMouseHandler
  words: ReactNode
  label: string
}) {
  return (
    <>
      <div className="sr-only" role="group" aria-label={`${label}, in words`}>{words}</div>
      <div
        className="w-full overflow-hidden rounded-card border border-border bg-surface-2"
        style={{ aspectRatio: `${width} / ${height}`, minHeight: 240, maxHeight: 620 }}
        role="group" aria-label={label}
      >
        <ReactFlow
          nodes={nodes} edges={edges} nodeTypes={nodeTypes} onNodeClick={onNodeClick}
          fitView fitViewOptions={{ padding: 0.06 }} minZoom={0.2} maxZoom={1.6}
          nodesDraggable={false} nodesConnectable={false} elementsSelectable={false} zoomOnScroll={false}
          proOptions={{ hideAttribution: false }}
        >
          <Background gap={20} size={1} color="var(--divider)" />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </>
  )
}
