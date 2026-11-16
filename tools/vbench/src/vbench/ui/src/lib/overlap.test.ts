import { describe, expect, it } from "vitest"

import type { Overlap } from "@/lib/changes"
import { canCheck, editable, fingerprint, headline, VERDICT } from "@/lib/overlap"

describe("does it already exist", () => {
  it("has a word and a tone for every verdict the server can give", () => {
    for (const v of ["new", "duplicate", "overlaps", "refines"] as const) expect(VERDICT[v].word).toBeTruthy()
    expect(VERDICT.new.tone).toBe("ok")
    expect(VERDICT.duplicate.tone).toBe("risk")
  })

  it("can be asked only once the main text is written", () => {
    expect(canCheck("request", { text: "  ", raised_by: "x" })).toBe(false)
    expect(canCheck("problem", { text: "A thing" })).toBe(true)
    expect(canCheck("quality", { quality: "", outline: "Fast" })).toBe(true)
    expect(canCheck("quality", { quality: "", outline: "" })).toBe(false)
  })

  it("treats an answer as stale once the wording changes, but not when only links change", () => {
    const a = fingerprint({ text: "keep notes", problems: ["STK-PRB-001"] })
    expect(fingerprint({ text: "keep notes ", problems: ["STK-PRB-002"] })).toBe(a)
    expect(fingerprint({ text: "keep my notes", problems: ["STK-PRB-001"] })).not.toBe(a)
  })

  it("offers to edit a match instead only when it is the same kind of thing", () => {
    const m = { id: "STK-REQ-001", kind: "request" as const, text: "", why: "", score: 0 }
    expect(editable(m, "request")).toBe(true)
    expect(editable(m, "functional")).toBe(false)
  })

  it("says who answered and how many entries were compared", () => {
    const base: Overlap = { checked: true, verdict: "duplicate", matches: [{ id: "A", kind: "request", text: "", why: "", score: 0 }], compared: 12 }
    expect(headline({ ...base, source: "agent", agent: "Claude" })).toBe("Something that exists already says this. 1 entry is close. Claude read it beside 12 entries.")
    expect(headline({ ...base, source: "rules", matches: [] })).toBe("Something that exists already says this. Compared with 12 entries by wording.")
    expect(headline({ checked: false })).toBe("")
  })
})
