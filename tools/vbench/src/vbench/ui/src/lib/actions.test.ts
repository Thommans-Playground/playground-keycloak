import { describe, expect, it } from "vitest"

import { actionsFor } from "@/lib/actions"

const keys = (t: Parameters<typeof actionsFor>[0]) => actionsFor(t).map((a) => a.key)

describe("what a row can do", () => {
  it("lets a problem add a request that already names it, and be edited or deleted", () => {
    expect(keys({ kind: "problem", id: "STK-PRB-001" })).toEqual(["add-request", "edit", "delete"])
    expect(actionsFor({ kind: "problem", id: "STK-PRB-001" })[0].intent).toEqual({ op: "add", kind: "request", defaults: { problems: ["STK-PRB-001"] } })
  })

  it("lets a request add either kind of requirement that already satisfies it", () => {
    const [f, q] = actionsFor({ kind: "request", id: "STK-REQ-001" })
    expect(f.intent).toMatchObject({ kind: "functional", defaults: { satisfies: ["STK-REQ-001"] } })
    expect(q.intent).toMatchObject({ kind: "quality", defaults: { satisfies: ["STK-REQ-001"] } })
  })

  it("lets a requirement add a use case, and a criterion once it has one use case to put it in", () => {
    const one = actionsFor({ kind: "functional", id: "REQ-FR-001", ucs: [{ id: "UC-N-001" }] })
    expect(one.find((a) => a.key === "add-criterion")).toMatchObject({ unavailable: undefined, intent: { defaults: { uc: "UC-N-001", satisfies: ["REQ-FR-001"] } } })
    const many = actionsFor({ kind: "quality", id: "REQ-NFR-001", ucs: [{ id: "A" }, { id: "B" }] })
    expect(many.find((a) => a.key === "add-criterion")?.intent.defaults?.uc).toBe("") // it has to be chosen
  })

  it("shows the criterion action disabled, with the reason, when there is no use case yet", () => {
    const none = actionsFor({ kind: "functional", id: "REQ-FR-003", ucs: [] }).find((a) => a.key === "add-criterion")
    expect(none?.unavailable).toBe("A use case comes first")
  })

  it("only offers deletion as destructive, and words the noun for the kind", () => {
    const all = actionsFor({ kind: "quality", id: "REQ-NFR-001", ucs: [] })
    expect(all.filter((a) => a.destructive).map((a) => a.label)).toEqual(["Delete quality requirement"])
    expect(actionsFor({ kind: "functional", id: "REQ-FR-001", ucs: [] }).at(-1)?.label).toBe("Delete requirement")
  })

  it("gives a use case one action: a criterion in it, for what it realises", () => {
    expect(actionsFor({ kind: "usecase", id: "UC-N-001", realises: ["REQ-FR-001"] })).toHaveLength(1)
  })
})
