import { describe, expect, it } from "vitest"

import { lineageCrumbs, lineageOf, nodeOfItem, nodeOfUseCase, parentsOf } from "@/lib/lineage"
import type { ProjectState, VItem } from "@/lib/types"

const item = (over: Partial<VItem> & Pick<VItem, "id" | "phase" | "kind">): VItem => ({
  ref: over.id, title: over.id, ucs: [], file: null, line: null, status: "ok", label: "", acs: [], description: "", ...over,
})

const req = { status: "ok" as const, label: "", ucs: [], criteria: [] }
const project = {
  useCases: [{ id: "UC-N-001", title: "Create note" }, { id: "UC-N-002", title: "Read note" }],
  criteria: [
    { id: "AC-N-001", uc: "UC-N-001", text: "Given a body", state: "covered", tests: [], satisfies: ["REQ-FR-001"] },
    { id: "AC-N-002", uc: "UC-N-002", text: "Given an id", state: "covered", tests: [], satisfies: ["REQ-FR-002"] },
  ],
  requirements: {
    problems: [{ id: "STK-PRB-001", text: "scattered", who: "", cost: "", status: "ok", label: "", requests: ["STK-REQ-001"] }],
    requests: [
      { id: "STK-REQ-001", raisedBy: "", text: "keep notes", problems: ["STK-PRB-001"], requirements: ["REQ-FR-001", "REQ-FR-002"] },
      { id: "STK-REQ-002", raisedBy: "", text: "find notes", problems: ["STK-PRB-001"], requirements: ["REQ-FR-002"] },
    ],
    functional: [{ id: "REQ-FR-001", text: "create", story: "", satisfies: ["STK-REQ-001"], ...req }, { id: "REQ-FR-002", text: "read", story: "", satisfies: ["STK-REQ-001", "STK-REQ-002"], ...req }],
    quality: [],
  },
  v: {
    items: [
      item({ id: "STK-PRB-001", phase: "requirements", kind: "problem" }),
      item({ id: "STK-REQ-001", phase: "requirements", kind: "request" }),
      item({ id: "STK-REQ-002", phase: "requirements", kind: "request" }),
      item({ id: "REQ-FR-001", phase: "requirements", kind: "FR", ucs: ["UC-N-001"] }),
      item({ id: "REQ-FR-002", phase: "requirements", kind: "FR", ucs: ["UC-N-002"] }),
      item({ id: "t1", ref: "TST-UNT-001", phase: "unit", kind: "test", ucs: ["UC-N-001"], acs: ["AC-N-001"] }),
      item({ id: "src/a.py", ref: "COD-SRC-001", phase: "code", kind: "code", ucs: ["UC-N-001"] }),
      item({ id: "notes", ref: "SYS-CTX-001", phase: "system-design", kind: "context", ucs: ["UC-N-001"] }),
    ],
    unplaced: [],
  },
} as unknown as ProjectState

const node = (id: string) => nodeOfItem(project.v.items.find((i) => i.id === id)!)!

describe("lineage", () => {
  it("climbs from a requirement to its request and the problem behind it", () => {
    expect(lineageOf(project, node("REQ-FR-001")).map((n) => n.ref)).toEqual(["STK-PRB-001", "STK-REQ-001", "REQ-FR-001"])
    expect(lineageOf(project, node("STK-PRB-001")).map((n) => n.ref)).toEqual(["STK-PRB-001"])
  })

  it("never shows more than four layers, dropping the top ones", () => {
    const uc = nodeOfUseCase(project, "UC-N-001")!
    expect(lineageOf(project, uc).map((n) => n.ref)).toEqual(["STK-PRB-001", "STK-REQ-001", "REQ-FR-001", "UC-N-001"])
    // test <- criterion <- use case <- requirement <- request <- problem: only the last four layers are shown
    expect(lineageOf(project, node("t1")).map((n) => n.ref)).toEqual(["REQ-FR-001", "UC-N-001", "AC-N-001", "TST-UNT-001"])
  })

  it("puts a test under the criterion it proves, and code under its use case", () => {
    expect(parentsOf(project, node("t1")).map((n) => n.ref)).toEqual(["AC-N-001"])
    expect(parentsOf(project, node("src/a.py")).map((n) => n.ref)).toEqual(["UC-N-001"])
  })

  it("leaves out what is not on the trace, such as a context", () => {
    expect(nodeOfItem(project.v.items.find((i) => i.id === "notes")!)).toBeNull()
  })

  it("offers the other parents on an ancestor and the siblings on the last crumb", () => {
    const crumbs = lineageCrumbs(project, node("REQ-FR-002"))!
    expect(crumbs.map((c) => c.label)).toEqual(["STK-PRB-001", "STK-REQ-001", "REQ-FR-002"])
    expect(crumbs[1].switch?.items.map((i) => i.id)).toEqual(["STK-REQ-001", "STK-REQ-002"]) // the other request it came from
    expect(crumbs[2].switch?.items.map((i) => i.id)).toEqual(["REQ-FR-001", "REQ-FR-002"]) // the other requirements of that request
    expect(crumbs[0].switch).toBeUndefined() // one problem, so nothing to offer
    expect(crumbs[1].to).toBe("/v/requirements/STK-REQ-001")
  })

  it("has no lineage for something with nothing above it", () => {
    expect(lineageCrumbs(project, node("STK-PRB-001"))).toBeNull()
  })
})
