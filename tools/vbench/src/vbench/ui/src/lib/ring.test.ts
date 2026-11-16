import { describe, expect, it } from "vitest"

import { ringArcs } from "./ring"

const slice = (key: string, value: number) => ({ key, label: key, value, colour: "red" })

describe("ring arcs", () => {
  it("is empty when there is nothing to show", () => {
    expect(ringArcs([], 40)).toEqual([])
    expect(ringArcs([slice("a", 0), slice("b", 0)], 40)).toEqual([])
  })

  it("splits the circle by share, clockwise, each arc starting where the last ended", () => {
    const circ = 2 * Math.PI * 40
    const [a, b] = ringArcs([slice("a", 3), slice("b", 1)], 40, 0)
    expect(a.share).toBeCloseTo(0.75)
    expect(a.offset).toBe(-0)
    expect(b.offset).toBeCloseTo(-circ * 0.75)
    expect(Number.parseFloat(a.dash.split(" ")[0])).toBeCloseTo(circ * 0.75)
  })

  it("leaves a gap between neighbours but not around a single slice", () => {
    const circ = 2 * Math.PI * 40
    const [only] = ringArcs([slice("a", 5)], 40, 3)
    expect(Number.parseFloat(only.dash.split(" ")[0])).toBeCloseTo(circ)
    const [first] = ringArcs([slice("a", 1), slice("b", 1)], 40, 3)
    expect(Number.parseFloat(first.dash.split(" ")[0])).toBeCloseTo(circ / 2 - 3)
  })

  it("skips slices with no value", () => {
    expect(ringArcs([slice("a", 0), slice("b", 2)], 40).map((x) => x.key)).toEqual(["b"])
  })
})
