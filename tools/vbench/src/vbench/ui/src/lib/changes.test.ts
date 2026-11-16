import { describe, expect, it } from "vitest"

import { EFFECT_WORD, FIELDS, groupImpact, initialValues, missingRequired, radius, toChange, type Effect, type Impact } from "@/lib/changes"
import type { RequirementsSheet } from "@/lib/types"

const rel = { status: "ok" as const, label: "", ucs: [], criteria: [] }
const sheet: RequirementsSheet = {
  problems: [{ id: "STK-PRB-001", text: "scattered", who: "The author", cost: "lost", status: "ok", label: "", requests: [] }],
  requests: [{ id: "STK-REQ-001", raisedBy: "STK-PER-001", text: "keep notes", problems: ["STK-PRB-001"], requirements: [] }],
  functional: [{ id: "REQ-FR-001", text: "create", story: "As an author", satisfies: ["STK-REQ-001"], ...rel }],
  quality: [{ id: "REQ-NFR-001", quality: "Speed", outline: "fast", source: "user", stimulus: "s", artifact: "a", environment: "e", response: "r", measure: "<1s", satisfies: ["STK-REQ-001"], evidence: "ADR-DEC-001", ...rel }],
}
const impact = (effect: Effect, direction: Impact["direction"] = "down"): Impact => ({ id: effect, kind: "request", label: "", direction, effect, detail: "", auto: false })

describe("change forms", () => {
  it("starts empty for an add, with any defaults the page gave it", () => {
    expect(initialValues("request", sheet, null, { problems: ["STK-PRB-001"] })).toEqual({ text: "", raised_by: "", problems: ["STK-PRB-001"] })
    expect(initialValues("problem", sheet)).toEqual({ text: "", who: "", cost: "" })
  })

  it("starts with the entry's own values for an edit, evidence included so an edit cannot wipe it", () => {
    expect(initialValues("problem", sheet, "STK-PRB-001")).toEqual({ text: "scattered", who: "The author", cost: "lost" })
    expect(initialValues("request", sheet, "STK-REQ-001")).toEqual({ text: "keep notes", raised_by: "STK-PER-001", problems: ["STK-PRB-001"] })
    const q = initialValues("quality", sheet, "REQ-NFR-001")
    expect(q.evidence).toBe("ADR-DEC-001")
    expect(Object.keys(q)).toEqual(FIELDS.quality.map((f) => f.key))
  })

  it("builds a change with trimmed text and list fields as lists, and sends no fields for a delete", () => {
    const c = toChange("add", "request", null, { text: "  keep \n notes ", raised_by: " STK-PER-001", problems: ["STK-PRB-001"] })
    expect(c).toEqual({ op: "add", kind: "request", id: null, fields: { text: "keep notes", raised_by: "STK-PER-001", problems: ["STK-PRB-001"] } })
    expect(toChange("delete", "problem", "STK-PRB-001", { text: "x" }).fields).toEqual({})
  })

  it("names the required fields still empty", () => {
    expect(missingRequired("quality", { quality: "", outline: "  " })).toEqual(["Quality", "What must hold"])
    expect(missingRequired("problem", { text: "x" })).toEqual([])
  })
})

describe("blast radius", () => {
  it("groups by direction and sizes the radius in words", () => {
    const all = [impact("needs-review"), impact("needs-review"), impact("affected"), impact("link-added", "up"), impact("deleted", "here")]
    const g = groupImpact(all)
    expect([g.up.length, g.down.length, g.here.length]).toEqual([1, 3, 1])
    expect(radius(all)).toBe("2 to read again, 1 may be affected")
    expect(radius([])).toBe("Nothing else is affected")
  })

  it("has a word for every effect the server can report", () => {
    for (const e of ["deleted", "link-removed", "link-added", "status-changes", "orphaned", "needs-review", "affected"] as Effect[]) expect(EFFECT_WORD[e].word).toBeTruthy()
  })
})
