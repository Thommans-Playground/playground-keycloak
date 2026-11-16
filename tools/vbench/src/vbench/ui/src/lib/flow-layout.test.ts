import { describe, expect, it } from "vitest"

import { layoutBuildOrder, layoutTrace, TRACE_NODE, UC_NODE } from "./flow-layout"
import type { ProjectState, UseCase, VItem } from "./types"

const uc = (id: string, wave: number, dependsOn: string[], stage: UseCase["stage"] = "code"): UseCase => ({
  id, title: id, path: "", actor: null, context: null, rigor: "light", wave, stage, task: null, next: "", blockedBy: [],
  dependsOn, enables: [], acs: 0, covered: 0, enforced: 0, tasks: 0, tasksClosed: 0, code: false, tested: false,
})

describe("build order layout", () => {
  const cases = [uc("UC-N-003", 2, ["UC-N-001", "UC-N-002"]), uc("UC-N-001", 0, [], "verify"), uc("UC-N-002", 1, ["UC-N-001"]), uc("UC-X-001", 1, ["UC-GONE"])]
  const { nodes, edges, width, height } = layoutBuildOrder(cases)
  const at = (id: string) => nodes.find((n) => n.id === id)!.position

  it("puts each wave in its own column, left to right", () => {
    expect(at("UC-N-001").x).toBe(0)
    expect(at("UC-N-002").x).toBe(UC_NODE.column)
    expect(at("UC-N-003").x).toBe(2 * UC_NODE.column)
  })

  it("stacks a wave's use cases in id order and centres short columns", () => {
    expect(at("UC-N-002").y).toBeLessThan(at("UC-X-001").y)
    expect(at("UC-N-001").y).toBeGreaterThan(0) // wave 0 has one node and the tallest column has two
  })

  it("draws an arrow from each dependency, skipping ids that have no use case", () => {
    expect(edges.map((e) => e.id).sort()).toEqual(["UC-N-001->UC-N-002", "UC-N-001->UC-N-003", "UC-N-002->UC-N-003"])
  })

  it("marks an arrow as waiting until the dependency is built", () => {
    const waiting = Object.fromEntries(edges.map((e) => [e.id, (e.data as { waiting: boolean }).waiting]))
    expect(waiting).toEqual({ "UC-N-001->UC-N-002": false, "UC-N-001->UC-N-003": false, "UC-N-002->UC-N-003": true })
    expect(edges.find((e) => e.id === "UC-N-002->UC-N-003")!.animated).toBe(true)
  })

  it("sizes the frame to the graph", () => {
    expect(width).toBe(2 * UC_NODE.column + UC_NODE.width + UC_NODE.room * 2)
    expect(height).toBe(UC_NODE.row + UC_NODE.height + UC_NODE.room * 2)
  })

  it("copes with no use cases", () => {
    expect(layoutBuildOrder([]).nodes).toEqual([])
  })
})

const item = (over: Partial<VItem> & Pick<VItem, "id" | "phase" | "kind">): VItem => ({
  ref: over.id, description: "", title: over.id, ucs: ["UC-N-001"], file: null, line: null, status: "ok", label: "", acs: [], ...over,
})

describe("trace layout", () => {
  const project = {
    useCases: [uc("UC-N-001", 0, [])],
    criteria: [
      { id: "AC-N-007", uc: "UC-N-001", spec: "", state: "covered", tests: [], text: "", satisfies: [] },
      { id: "AC-N-008", uc: "UC-N-001", spec: "", state: "uncovered", tests: [], text: "", satisfies: [] },
      { id: "AC-N-009", uc: "UC-N-001", spec: "", state: "covered", tests: [], text: "", satisfies: [] },
      { id: "AC-N-010", uc: "UC-N-002", spec: "", state: "covered", tests: [] },
    ],
    v: {
      items: [
        item({ id: "REQ-FR-001", phase: "requirements", kind: "FR" }),
        item({ id: "STK-REQ-001", phase: "requirements", kind: "request" }),
        item({ id: "TSK-N-001", phase: "module-design", kind: "task", acs: ["AC-N-007", "AC-N-008"] }),
        item({ id: "t::one", phase: "unit", kind: "test", acs: ["AC-N-007"] }),
        item({ id: "t::two", phase: "acceptance", kind: "test", acs: [] }),
        item({ id: "REQ-FR-009", phase: "requirements", kind: "FR", ucs: ["UC-N-002"] }),
      ],
    },
  } as unknown as ProjectState
  const { nodes, edges, width } = layoutTrace(project, "UC-N-001")
  const has = (id: string) => edges.some((e) => e.id === id)

  it("puts only this use case's items on the graph, in five columns", () => {
    expect(nodes.map((n) => n.id).sort()).toEqual(["AC-N-007", "AC-N-008", "AC-N-009", "REQ-FR-001", "TSK-N-001", "UC-N-001", "t::one", "t::two"])
    expect(new Set(nodes.map((n) => n.position.x)).size).toBe(5)
    expect(width).toBe(4 * TRACE_NODE.column + TRACE_NODE.width + TRACE_NODE.room * 2)
  })

  it("leads from requirement to use case to task to criterion to test", () => {
    for (const id of ["REQ-FR-001->UC-N-001", "UC-N-001->TSK-N-001", "TSK-N-001->AC-N-007", "TSK-N-001->AC-N-008", "AC-N-007->t::one"]) {
      expect(has(id), id).toBe(true)
    }
  })

  it("hangs a criterion no task closes, and a test that marks none, off the use case with a dashed edge", () => {
    for (const id of ["UC-N-001->AC-N-009", "UC-N-001->t::two"]) {
      expect(has(id), id).toBe(true)
      expect(edges.find((e) => e.id === id)!.style).toEqual({ strokeDasharray: "5 4" })
    }
  })

  it("shows a criterion's state as a status and a word", () => {
    const b = nodes.find((n) => n.id === "AC-N-008")!.data as { status: string; label: string }
    expect(b).toMatchObject({ status: "risk", label: "No test yet" })
  })
})
