import type { Kind, Overlap, OverlapMatch, Values, Verdict } from "@/lib/changes"

export const VERDICT: Record<Verdict, { word: string; tone: "ok" | "warn" | "risk" | "neutral"; lead: string }> = {
  new: { word: "Looks new", tone: "ok", lead: "Nothing that exists covers it." },
  duplicate: { word: "Already exists", tone: "risk", lead: "Something that exists already says this." },
  overlaps: { word: "Partly written", tone: "warn", lead: "Part of this is already covered." },
  refines: { word: "A narrower version", tone: "warn", lead: "This is a more specific version of something that exists." },
}

export const KIND_WORD: Record<Kind, string> = {
  problem: "Problem", request: "Request", functional: "Functional requirement", quality: "Quality requirement",
  criterion: "Acceptance criterion", usecase: "Use case",
}

/** The part of the form that decides whether an earlier answer still applies: change it and the answer is stale. */
export function fingerprint(values: Values): string {
  return JSON.stringify(Object.entries(values).filter(([k]) => !["problems", "satisfies"].includes(k)).map(([k, v]) => [k, String(v).trim()]))
}

export function canCheck(kind: Kind, values: Values): boolean {
  const main = kind === "quality" ? values.quality || values.outline : values.text
  return Boolean(String(main ?? "").trim())
}

/** Whether a match is the same kind of thing as the entry being added, so "edit it instead" makes sense. */
export const editable = (match: OverlapMatch, kind: Kind): boolean => match.kind === kind

export function headline(o: Overlap): string {
  if (!o.checked || !o.verdict) return ""
  const found = o.matches?.length ?? 0
  const by = o.source === "agent" ? `${o.agent} read it beside ${o.compared} entries` : `Compared with ${o.compared} entries by wording`
  return `${VERDICT[o.verdict].lead} ${found ? `${found} ${found === 1 ? "entry is" : "entries are"} close.` : ""} ${by}.`.replace(/\s+/g, " ").trim()
}
