import { describe, expect, it } from "vitest"

import { becameOf, findRequirement, originOf, testsOf } from "@/lib/records"
import type { RequirementsSheet, SheetCriterion } from "@/lib/types"

const rel = { status: "ok" as const, label: "", ucs: [], criteria: [] as SheetCriterion[] }
const sheet: RequirementsSheet = {
  problems: [
    { id: "STK-PRB-001", text: "a", who: "", cost: "", status: "ok", label: "", requests: ["STK-REQ-001"] },
    { id: "STK-PRB-002", text: "b", who: "", cost: "", status: "warn", label: "", requests: [] },
  ],
  requests: [{ id: "STK-REQ-001", raisedBy: "", text: "ask", problems: ["STK-PRB-001"], requirements: ["REQ-FR-001"] }],
  functional: [{ id: "REQ-FR-001", text: "do", story: "", satisfies: ["STK-REQ-001"], ...rel }],
  quality: [{ id: "REQ-NFR-001", quality: "Speed", outline: "", source: "", stimulus: "", artifact: "", environment: "", response: "", measure: "", satisfies: [], evidence: "", ...rel }],
}

describe("requirement records", () => {
  it("finds any requirement-side id and says what kind it is", () => {
    expect(findRequirement(sheet, "STK-PRB-002")?.kind).toBe("problem")
    expect(findRequirement(sheet, "STK-REQ-001")?.kind).toBe("request")
    expect(findRequirement(sheet, "REQ-FR-001")?.kind).toBe("functional")
    expect(findRequirement(sheet, "REQ-NFR-001")?.kind).toBe("quality")
    expect(findRequirement(sheet, "nope")).toBeNull()
  })

  it("traces a requirement back to its request and the problem behind it", () => {
    const o = originOf(sheet, "REQ-FR-001")
    expect(o.requests.map((r) => r.id)).toEqual(["STK-REQ-001"])
    expect(o.problems.map((p) => p.id)).toEqual(["STK-PRB-001"])
    expect(originOf(sheet, "REQ-NFR-001")).toEqual({ requests: [], problems: [] })
  })

  it("traces a problem or a request forward to what it became", () => {
    expect(becameOf(sheet, findRequirement(sheet, "STK-PRB-001")!).map((r) => r.id)).toEqual(["REQ-FR-001"])
    expect(becameOf(sheet, findRequirement(sheet, "STK-REQ-001")!).map((r) => r.id)).toEqual(["REQ-FR-001"])
    expect(becameOf(sheet, findRequirement(sheet, "STK-PRB-002")!)).toEqual([])
    expect(becameOf(sheet, findRequirement(sheet, "REQ-FR-001")!)).toEqual([])
  })

  it("lists each proving test once, with every criterion it proves", () => {
    const t = { ref: "TST-UNT-001", id: "t1", phase: "unit", title: "x" }
    const c = (id: string): SheetCriterion => ({ id, uc: null, text: "", state: "covered", tests: [t] })
    expect(testsOf([c("AC-N-001"), c("AC-N-002")])).toEqual([{ ...t, proves: ["AC-N-001", "AC-N-002"] }])
    expect(testsOf([])).toEqual([])
  })
})
