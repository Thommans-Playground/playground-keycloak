import type { CriterionState, ItemStatus } from "@/lib/types"

// A status is always a colour and a word. These are the words and the stroke colours for the four tones.
export const STATUS_WORD: Record<ItemStatus, string> = { ok: "In order", warn: "Needs attention", risk: "Failing", neutral: "Not rated" }
export const STATUS_COLOUR: Record<ItemStatus, string> = {
  ok: "var(--ok)",
  warn: "var(--warn)",
  risk: "var(--risk)",
  neutral: "var(--border-input)",
}
export const STATUS_ORDER: ItemStatus[] = ["ok", "warn", "risk", "neutral"]

// A criterion's state is also a word and a colour. The order is the one the legends use.
export const CRITERION_STATE: Record<CriterionState, { word: string; tone: ItemStatus; colour: string }> = {
  covered: { word: "Covered by a test", tone: "ok", colour: "var(--ok)" },
  uncovered: { word: "No test yet", tone: "risk", colour: "var(--risk)" },
  tbd: { word: "Not written yet", tone: "warn", colour: "var(--warn)" },
  planned: { word: "Planned", tone: "neutral", colour: "var(--border-input)" },
}
export const CRITERION_ORDER = Object.keys(CRITERION_STATE) as CriterionState[]
