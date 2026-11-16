import { describe, expect, it } from "vitest"

import { emptyState, hasActiveFilters, readTableState, writeTableState } from "./table-state"

const ids = ["stage", "kind"]

describe("table state in the URL", () => {
  it("round-trips search, filters, sort and page", () => {
    const state = { q: "note", filters: { stage: ["code", "design"], kind: [] }, sort: { id: "wave", desc: true }, page: 3 }
    const url = writeTableState(new URLSearchParams(), "", ids, state)
    expect(url.toString()).toBe("q=note&sort=-wave&page=3&f.stage=code%2Cdesign")
    expect(readTableState(url, "", ids)).toEqual({ ...state, filters: { stage: ["code", "design"] } })
  })

  it("leaves other parameters alone and drops what is empty", () => {
    const base = new URLSearchParams("uc=UC-N-001&q=old&f.stage=code")
    const next = writeTableState(base, "", ids, emptyState)
    expect(next.toString()).toBe("uc=UC-N-001")
  })

  it("keeps two tables on one page apart with a prefix", () => {
    const a = writeTableState(new URLSearchParams(), "ac.", ids, { ...emptyState, q: "x" })
    const b = writeTableState(a, "rung.", ids, { ...emptyState, q: "y" })
    expect(b.toString()).toBe("ac.q=x&rung.q=y")
    expect(readTableState(b, "ac.", ids).q).toBe("x")
    expect(readTableState(b, "rung.", ids).q).toBe("y")
  })

  it("reads an ascending sort, ignores a bad page, and omits page 1", () => {
    expect(readTableState(new URLSearchParams("sort=id&page=abc"), "", ids)).toMatchObject({ sort: { id: "id", desc: false }, page: 1 })
    expect(readTableState(new URLSearchParams("page=0"), "", ids).page).toBe(1)
    expect(writeTableState(new URLSearchParams(), "", ids, { ...emptyState, page: 1 }).has("page")).toBe(false)
  })

  it("knows when a filter is active", () => {
    expect(hasActiveFilters(emptyState)).toBe(false)
    expect(hasActiveFilters({ ...emptyState, q: "a" })).toBe(true)
    expect(hasActiveFilters({ ...emptyState, filters: { stage: ["code"] } })).toBe(true)
    expect(hasActiveFilters({ ...emptyState, filters: { stage: [] } })).toBe(false)
  })
})
