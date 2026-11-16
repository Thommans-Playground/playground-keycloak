// Geometry for a donut drawn as stroked circle arcs, so it needs no chart library.

export interface RingSlice {
  key: string
  label: string
  value: number
  colour: string // a CSS value, such as "var(--ok)"
}

export interface Arc extends RingSlice {
  dash: string // the stroke-dasharray: the arc's length, then the rest of the circle
  offset: number // the stroke-dashoffset that starts it after the arcs before it
  share: number // 0..1
}

/** Arcs for the slices with a value, clockwise from the top, with a small gap between neighbours. */
export function ringArcs(slices: RingSlice[], radius: number, gap = 3): Arc[] {
  const live = slices.filter((s) => s.value > 0)
  const total = live.reduce((n, s) => n + s.value, 0)
  if (total === 0) return []
  const circumference = 2 * Math.PI * radius
  const space = live.length > 1 ? gap : 0
  let used = 0
  return live.map((s) => {
    const share = s.value / total
    const length = Math.max(circumference * share - space, 0.01)
    const arc = { ...s, share, dash: `${length} ${circumference - length}`, offset: -used }
    used += circumference * share
    return arc
  })
}
