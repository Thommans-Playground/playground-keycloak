// Layouts for the two React Flow graphs. Both are plain functions of the project state: columns left to right,
// nodes stacked within a column, so the positions are predictable and testable without a browser.

import type { Edge, Node } from "@xyflow/react"

import type { ItemStatus, ProjectState, Stage, UseCase } from "@/lib/types"

export interface Layout {
  nodes: Node[]
  edges: Edge[]
  width: number
  height: number
}

// ---- build order: one column per wave, an arrow from what must be built first to what needs it ----------------

export interface UcNodeData extends Record<string, unknown> {
  id: string
  title: string
  stage: Stage
  wave: number
  covered: number
  enforced: number
  waiting: string[]
}

export const UC_NODE = { width: 220, height: 96, column: 300, row: 124, room: 24 }

export function layoutBuildOrder(useCases: UseCase[]): Layout {
  const known = new Map(useCases.map((u) => [u.id, u]))
  const byWave = new Map<number, UseCase[]>()
  for (const u of useCases) byWave.set(u.wave, [...(byWave.get(u.wave) ?? []), u])
  const waves = [...byWave.keys()].sort((a, b) => a - b)
  const tallest = Math.max(...[...byWave.values()].map((c) => c.length), 1)

  const nodes: Node[] = []
  waves.forEach((w, col) => {
    const column = (byWave.get(w) ?? []).sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }))
    const top = ((tallest - column.length) * UC_NODE.row) / 2
    column.forEach((u, i) =>
      nodes.push({
        id: u.id,
        type: "useCase",
        position: { x: col * UC_NODE.column, y: top + i * UC_NODE.row },
        data: { id: u.id, title: u.title, stage: u.stage, wave: u.wave, covered: u.covered, enforced: u.enforced, waiting: u.blockedBy } satisfies UcNodeData,
      }),
    )
  })

  const edges: Edge[] = useCases.flatMap((u) =>
    u.dependsOn
      .filter((d) => known.has(d))
      .map((d) => {
        const waiting = known.get(d)!.stage !== "verify"
        return { id: `${d}->${u.id}`, source: d, target: u.id, type: "smoothstep", animated: waiting, data: { waiting } }
      }),
  )
  return {
    nodes,
    edges,
    width: Math.max(waves.length - 1, 0) * UC_NODE.column + UC_NODE.width + UC_NODE.room * 2,
    height: (tallest - 1) * UC_NODE.row + UC_NODE.height + UC_NODE.room * 2,
  }
}

// ---- trace: from a requirement, through its use case, tasks and criteria, to the tests that prove it ----------

export type TraceKind = "requirement" | "useCase" | "task" | "criterion" | "test"

export interface TraceNodeData extends Record<string, unknown> {
  kind: TraceKind
  title: string
  sub: string
  status: ItemStatus
  label: string
  href: string | null
}

export const TRACE_NODE = { width: 220, height: 64, column: 290, row: 82, room: 24 }
const COLUMNS: TraceKind[] = ["requirement", "useCase", "task", "criterion", "test"]

export function layoutTrace(project: ProjectState, uc: string): Layout {
  const u = project.useCases.find((x) => x.id === uc)
  const mine = project.v.items.filter((i) => i.ucs.includes(uc))
  const reqs = mine.filter((i) => i.phase === "requirements" && (i.kind === "FR" || i.kind === "NFR"))
  const tasks = mine.filter((i) => i.kind === "task")
  const tests = mine.filter((i) => i.kind === "test")
  const criteria = project.criteria.filter((c) => c.uc === uc)

  const columns: Record<TraceKind, { id: string; data: TraceNodeData }[]> = {
    requirement: reqs.map((r) => ({
      id: r.id,
      data: { kind: "requirement", title: r.id, sub: r.title, status: r.status, label: r.label, href: `/v/requirements/${encodeURIComponent(r.id)}` },
    })),
    useCase: [{ id: uc, data: { kind: "useCase", title: uc, sub: u?.title ?? "", status: "neutral", label: u?.stage ?? "", href: null } }],
    task: tasks.map((t) => ({
      id: t.id,
      data: { kind: "task", title: t.id, sub: t.title, status: t.status, label: t.label, href: `/v/module-design/${encodeURIComponent(t.id)}` },
    })),
    criterion: criteria.map((c) => ({
      id: c.id,
      data: {
        kind: "criterion", title: c.id, sub: c.text,
        status: c.state === "covered" ? "ok" : c.state === "uncovered" ? "risk" : c.state === "tbd" ? "warn" : "neutral",
        label: { covered: "Covered", uncovered: "No test yet", planned: "Planned", tbd: "Not written yet" }[c.state], href: null,
      },
    })),
    test: tests.map((t) => ({
      id: t.id,
      data: { kind: "test", title: t.ref, sub: t.description || t.title, status: t.status, label: t.label, href: `/v/${t.phase}/${encodeURIComponent(t.id)}` },
    })),
  }

  const tallest = Math.max(...COLUMNS.map((k) => columns[k].length), 1)
  const nodes: Node[] = []
  COLUMNS.forEach((kind, col) => {
    const list = columns[kind]
    const top = ((tallest - list.length) * TRACE_NODE.row) / 2
    list.forEach((n, i) => nodes.push({ id: n.id, type: "trace", position: { x: col * TRACE_NODE.column, y: top + i * TRACE_NODE.row }, data: n.data }))
  })

  const edges: Edge[] = []
  const edge = (source: string, target: string, dashed = false) =>
    edges.push({ id: `${source}->${target}`, source, target, type: "smoothstep", style: dashed ? { strokeDasharray: "5 4" } : undefined })
  const closed = new Set<string>()
  for (const r of reqs) edge(r.id, uc)
  for (const t of tasks) {
    edge(uc, t.id)
    for (const ac of t.acs) if (criteria.some((c) => c.id === ac)) (edge(t.id, ac), closed.add(ac))
  }
  for (const c of criteria) if (!closed.has(c.id)) edge(uc, c.id, true) // a criterion no task closes hangs off the use case
  const marked = new Set<string>()
  for (const t of tests) {
    const hits = t.acs.filter((ac) => criteria.some((c) => c.id === ac))
    hits.forEach((ac) => (edge(ac, t.id), marked.add(t.id)))
    if (!marked.has(t.id)) edge(uc, t.id, true) // a test that marks no criterion still verifies the use case
  }
  return {
    nodes,
    edges,
    width: (COLUMNS.length - 1) * TRACE_NODE.column + TRACE_NODE.width + TRACE_NODE.room * 2,
    height: (tallest - 1) * TRACE_NODE.row + TRACE_NODE.height + TRACE_NODE.room * 2,
  }
}
