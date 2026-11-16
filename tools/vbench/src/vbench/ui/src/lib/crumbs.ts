import type { ProjectState } from "@/lib/types"
import { itemPath, phasePath } from "@/lib/v"

// What a breadcrumb's menu offers: the other records of the same kind, to go to without going up first.
export interface SwitchItem {
  id: string
  label: string
  detail?: string
  to: string
}

export interface Switch {
  noun: string // singular, lower case: "use case"
  currentId: string
  items: SwitchItem[]
  all: { label: string; to: string }
}

export function useCaseSwitch(project: ProjectState, current: string): Switch {
  return {
    noun: "use case",
    currentId: current,
    items: project.useCases.map((u) => ({ id: u.id, label: `${u.id}  ${u.title}`, detail: u.next, to: `/use-cases/${u.id}` })),
    all: { label: "All use cases", to: "/use-cases" },
  }
}

export function phaseSwitch(project: ProjectState, current: string): Switch {
  return {
    noun: "phase",
    currentId: current,
    items: project.v.phases.map((p) => ({
      id: p.key,
      label: p.label,
      detail: ((n) => `${n} ${n === 1 ? "item" : "items"}`)(project.v.items.filter((i) => i.phase === p.key).length),
      to: phasePath(p.key),
    })),
    all: { label: "Overview", to: "/" },
  }
}

export function itemSwitch(project: ProjectState, phase: string, current: string): Switch {
  return {
    noun: "item",
    currentId: current,
    items: project.v.items
      .filter((i) => i.phase === phase)
      .map((i) => ({ id: i.id, label: `${i.ref}  ${i.title}`, detail: i.description, to: itemPath(i) })),
    all: { label: "All in this phase", to: phasePath(phase) },
  }
}
