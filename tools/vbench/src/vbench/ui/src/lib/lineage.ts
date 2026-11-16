import type { Switch, SwitchItem } from "@/lib/crumbs"
import type { ProjectState, VItem } from "@/lib/types"
import { itemPath, phasePath } from "@/lib/v"

// What a breadcrumb shows: where this thing sits in the trace, from the problem someone has down to the test that
// proves it. Problem, request, requirement, use case, criterion, test (or task, code, diagram under a use case).
export type Layer = "problem" | "request" | "requirement" | "usecase" | "criterion" | "test" | "task" | "code" | "diagram"

export interface LineageNode {
  layer: Layer
  id: string
  ref: string
  title: string
  to: string
  list: { label: string; to: string } // the whole list this belongs to
}

export interface LineageCrumb {
  label: string
  title: string
  to: string
  switch?: Switch
}

export const MAX_LAYERS = 4

const NOUN: Record<Layer, string> = {
  problem: "problem", request: "request", requirement: "requirement", usecase: "use case", criterion: "criterion",
  test: "test", task: "task", code: "code file", diagram: "diagram",
}

function layerOf(item: VItem): Layer | null {
  if (item.phase === "requirements") {
    return item.kind === "problem" ? "problem" : item.kind === "request" ? "request" : item.kind === "FR" || item.kind === "NFR" ? "requirement" : null
  }
  if (item.kind === "test") return "test"
  if (item.kind === "task") return "task"
  if (item.kind === "code") return "code"
  return item.kind.endsWith("diagram") ? "diagram" : null // a context or a domain model sits outside the trace
}

const LIST: Record<Layer, { label: string; to: string }> = {
  problem: { label: "All requirements", to: "/v/requirements" },
  request: { label: "All requirements", to: "/v/requirements" },
  requirement: { label: "All requirements", to: "/v/requirements" },
  usecase: { label: "All use cases", to: "/use-cases" },
  criterion: { label: "All criteria", to: "/traceability" },
  test: { label: "All tests", to: "/traceability" },
  task: { label: "All use cases", to: "/use-cases" },
  code: { label: "All use cases", to: "/use-cases" },
  diagram: { label: "All diagrams", to: "/diagrams" },
}

// A name from the repo (a file, a test, a diagram) is explained by its description; a requirement's own words are its title.
const NAMED = new Set<Layer>(["test", "task", "code", "diagram"])

export function nodeOfItem(item: VItem): LineageNode | null {
  const layer = layerOf(item)
  return layer ? { layer, id: item.id, ref: item.ref, title: NAMED.has(layer) && item.kind !== "task" ? item.description || item.title : item.title, to: itemPath(item), list: layer === "test" || layer === "code" || layer === "task" ? { label: "All in this phase", to: phasePath(item.phase) } : LIST[layer] } : null
}

export function nodeOfUseCase(project: ProjectState, id: string): LineageNode | null {
  const u = project.useCases.find((x) => x.id === id)
  return u ? { layer: "usecase", id: u.id, ref: u.id, title: u.title, to: `/use-cases/${u.id}`, list: LIST.usecase } : null
}

function nodeOfCriterion(project: ProjectState, id: string): LineageNode | null {
  const c = project.criteria.find((x) => x.id === id)
  return c ? { layer: "criterion", id: c.id, ref: c.id, title: c.text, to: c.uc ? `/use-cases/${c.uc}#criteria` : "/traceability", list: LIST.criterion } : null
}

const itemNode = (project: ProjectState, id: string, phase?: string) => {
  const item = project.v.items.find((i) => i.id === id && (!phase || i.phase === phase))
  return item ? nodeOfItem(item) : null
}

const compact = (xs: (LineageNode | null)[]) => xs.filter((x): x is LineageNode => x !== null)

// The things this one comes from, most relevant first.
export function parentsOf(project: ProjectState, node: LineageNode): LineageNode[] {
  const sheet = project.requirements
  switch (node.layer) {
    case "problem":
      return []
    case "request":
      return compact((sheet.requests.find((r) => r.id === node.id)?.problems ?? []).map((id) => itemNode(project, id, "requirements")))
    case "requirement":
      return compact(sheet.requests.filter((r) => r.requirements.includes(node.id)).map((r) => itemNode(project, r.id, "requirements")))
    case "usecase":
      return compact(project.v.items.filter((i) => i.phase === "requirements" && (i.kind === "FR" || i.kind === "NFR") && i.ucs.includes(node.id)).map(nodeOfItem))
    case "criterion":
      return compact([nodeOfUseCase(project, project.criteria.find((c) => c.id === node.id)?.uc ?? "")])
    default: {
      const item = project.v.items.find((i) => i.id === node.id && nodeOfItem(i)?.layer === node.layer) ?? project.v.unplaced.find((i) => i.id === node.id)
      if (!item) return []
      const byCriterion = node.layer === "test" ? compact(item.acs.map((a) => nodeOfCriterion(project, a))) : []
      return byCriterion.length ? byCriterion : compact(item.ucs.map((u) => nodeOfUseCase(project, u)))
    }
  }
}

// Every node of a layer, so the others under the same parent can be offered.
function allOfLayer(project: ProjectState, layer: Layer): LineageNode[] {
  if (layer === "usecase") return compact(project.useCases.map((u) => nodeOfUseCase(project, u.id)))
  if (layer === "criterion") return compact(project.criteria.map((c) => nodeOfCriterion(project, c.id)))
  return compact([...project.v.items, ...project.v.unplaced].map(nodeOfItem)).filter((n) => n.layer === layer)
}

// The layers above a node, top first, ending with the node itself; at most four.
export function lineageOf(project: ProjectState, node: LineageNode, max = MAX_LAYERS): LineageNode[] {
  const chain = [node]
  while (chain.length < max) {
    const parent = parentsOf(project, chain[0])[0]
    if (!parent) break
    chain.unshift(parent)
  }
  return chain
}

const toItem = (n: LineageNode): SwitchItem => ({ id: n.id, label: n.ref, detail: n.title, to: n.to })

// The breadcrumb for a node: each ancestor offers the other things the layer below could have come from; the node itself
// offers the others under the same parent. Null when there is nothing above it, so the caller falls back to the plain trail.
export function lineageCrumbs(project: ProjectState, node: LineageNode): LineageCrumb[] | null {
  const chain = lineageOf(project, node)
  if (chain.length < 2) return null
  return chain.map((n, i) => {
    const last = i === chain.length - 1
    const options = last
      ? allOfLayer(project, n.layer).filter((s) => parentsOf(project, s).some((p) => p.id === chain[i - 1].id))
      : parentsOf(project, chain[i + 1])
    const crumb: LineageCrumb = { label: n.ref, title: `${NOUN[n.layer]}: ${n.title}`, to: n.to }
    if (options.length > 1) crumb.switch = { noun: NOUN[n.layer], currentId: n.id, items: options.map((o) => toItem(o)), all: n.list }
    return crumb
  })
}
