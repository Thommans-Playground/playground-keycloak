import type { ItemStatus, ProjectState, VItem, VPhase } from "@/lib/types"

export const phaseOf = (p: ProjectState, key: string): VPhase | undefined => p.v.phases.find((x) => x.key === key)
export const itemsFor = (p: ProjectState, phase: string): VItem[] => p.v.items.filter((i) => i.phase === phase)
export const itemsOfUc = (p: ProjectState, uc: string): VItem[] => p.v.items.filter((i) => i.ucs.includes(uc))
export const itemPath = (i: VItem) => `/v/${i.phase}/${encodeURIComponent(i.id)}`
export const phasePath = (phase: string, uc?: string) => `/v/${phase}${uc ? `?uc=${encodeURIComponent(uc)}` : ""}`

const RANK: Record<ItemStatus, number> = { risk: 3, warn: 2, ok: 1, neutral: 0 }

/** The most urgent status among some items, or "none" when there are none. */
export function worst(items: VItem[]): ItemStatus | "none" {
  if (items.length === 0) return "none"
  return items.reduce<ItemStatus>((w, i) => (RANK[i.status] > RANK[w] ? i.status : w), "neutral")
}

export const tone = (s: ItemStatus): "neutral" | "ok" | "warn" | "risk" => s

/** The label of an item chip: its id, the same three-part shape for every kind (the title is the tooltip). */
export function shortTitle(i: VItem): string {
  return i.ref
}
