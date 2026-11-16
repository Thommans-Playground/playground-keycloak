import type { RequirementsSheet } from "@/lib/types"

// A change to the requirements, as the server plans it. The server decides what is valid and what it touches; this
// only builds the request and words the answer.
export type Kind = "problem" | "request" | "functional" | "quality" | "criterion" | "usecase"
/** The kinds that sit in the requirements doc; a criterion and a use case are written in the specs and can only be added. */
export const REQUIREMENT_KINDS: Kind[] = ["problem", "request", "functional", "quality"]
export type Op = "add" | "update" | "delete"
export type Values = Record<string, string | string[]>

export interface Change {
  op: Op
  kind: Kind
  id?: string | null
  fields: Values
}

export type Effect = "deleted" | "link-removed" | "link-added" | "status-changes" | "orphaned" | "needs-review" | "affected"

export interface Impact {
  id: string
  kind: string
  label: string
  direction: "up" | "down" | "here"
  effect: Effect
  detail: string
  auto: boolean
}

export interface Preview {
  summary: string
  change: Change
  errors: string[]
  warnings: string[]
  diff: string
  impact: Impact[]
  nextStep: string
  digest: string
  files: string[]
}

export interface Applied {
  summary: string
  id: string | null
  written: string[]
  regenerated: string[]
  gates: { name: string; ok: boolean; lines: string[] }[]
  nextStep: string
  impact: Impact[]
}

export interface Session {
  write: boolean
  token: string | null
  blocked: string
  agent: string // who answers "does this already exist?" and the assistant's questions, or empty
  chat?: boolean // whether the assistant is available (the server was started with an agent)
}

export type Verdict = "new" | "duplicate" | "overlaps" | "refines"

export interface OverlapMatch {
  id: string
  kind: Kind
  text: string
  why: string
  score: number
}

export interface Overlap {
  checked: boolean
  source?: "agent" | "rules"
  agent?: string
  note?: string
  compared?: number
  verdict?: Verdict
  advice?: string
  matches?: OverlapMatch[]
}

export interface FieldSpec {
  key: string
  label: string
  hint?: string
  input: "text" | "area" | "links" | "select"
  links?: "problem" | "request" | "requirement"
  select?: "usecases"
  required?: boolean
}

export const NOUN: Record<Kind, string> = {
  problem: "problem", request: "request", functional: "functional requirement", quality: "quality requirement",
  criterion: "acceptance criterion", usecase: "use case",
}

export const FIELDS: Record<Kind, FieldSpec[]> = {
  problem: [
    { key: "text", label: "The problem", hint: "What goes wrong, in their words, with no solution in it.", input: "area", required: true },
    { key: "who", label: "Who is affected", input: "text" },
    { key: "cost", label: "Cost of leaving it", hint: "What it costs them.", input: "text" },
  ],
  request: [
    { key: "text", label: "The ask", hint: "In the stakeholder's own words, as close as you can.", input: "area", required: true },
    { key: "raised_by", label: "Raised by", hint: "A stakeholder id, such as STK-PER-001.", input: "text" },
    { key: "problems", label: "Problems it addresses", input: "links", links: "problem" },
  ],
  functional: [
    { key: "text", label: "The requirement", hint: "The system shall …", input: "area", required: true },
    { key: "story", label: "User story", hint: "As a <role>, I want <goal> so that <benefit>.", input: "area" },
    { key: "satisfies", label: "Requests it satisfies", input: "links", links: "request" },
  ],
  quality: [
    { key: "quality", label: "Quality", hint: "Performance, security, durability …", input: "text", required: true },
    { key: "outline", label: "What must hold", hint: "One sentence.", input: "area", required: true },
    { key: "satisfies", label: "Requests it satisfies", input: "links", links: "request" },
    { key: "source", label: "Source", hint: "Who or what raises the event.", input: "text" },
    { key: "stimulus", label: "Stimulus", hint: "The event.", input: "text" },
    { key: "artifact", label: "Artifact", hint: "The part of the system it hits.", input: "text" },
    { key: "environment", label: "Environment", hint: "The state the system is in.", input: "text" },
    { key: "response", label: "Response", hint: "What the system does.", input: "text" },
    { key: "measure", label: "Response measure", hint: "A number or a checkable yes or no. This is what a test checks.", input: "text" },
    { key: "evidence", label: "Evidence or ADR", input: "text" },
  ],
  criterion: [
    { key: "uc", label: "Use case", hint: "The use case whose spec it is written in.", input: "select", select: "usecases", required: true },
    { key: "text", label: "What must hold", hint: "Given … when … then …, so it can become a test.", input: "area", required: true },
    { key: "satisfies", label: "Requirements it satisfies", input: "links", links: "requirement" },
  ],
  usecase: [
    { key: "title", label: "Title", hint: "What the actor achieves, in a few words.", input: "text", required: true },
    { key: "area", label: "Area letter", hint: "One letter, the area the use case belongs to (the one in its id, UC-N-001).", input: "text", required: true },
    { key: "realises", label: "Requirements it realises", input: "links", links: "requirement" },
  ],
}

export const EFFECT_WORD: Record<Effect, { word: string; tone: "ok" | "warn" | "risk" | "neutral" }> = {
  deleted: { word: "Deleted", tone: "risk" },
  "link-removed": { word: "Link removed", tone: "neutral" },
  "link-added": { word: "Link added", tone: "ok" },
  "status-changes": { word: "Status changes", tone: "warn" },
  orphaned: { word: "Left with nothing above it", tone: "risk" },
  "needs-review": { word: "Read again", tone: "warn" },
  affected: { word: "May be affected", tone: "neutral" },
}

const str = (v: unknown) => (typeof v === "string" ? v : "")
const list = (v: unknown) => (Array.isArray(v) ? (v as string[]) : [])

function existing(kind: Kind, sheet: RequirementsSheet, id?: string | null): Record<string, unknown> | undefined {
  if (kind === "criterion" || kind === "usecase") return undefined // these can only be added, so there is nothing to start from
  if (kind === "problem") {
    const p = sheet.problems.find((x) => x.id === id)
    return p && { text: p.text, who: p.who, cost: p.cost }
  }
  if (kind === "request") {
    const r = sheet.requests.find((x) => x.id === id)
    return r && { text: r.text, raised_by: r.raisedBy, problems: r.problems }
  }
  if (kind === "functional") {
    const f = sheet.functional.find((x) => x.id === id)
    return f && { text: f.text, story: f.story, satisfies: f.satisfies }
  }
  const q = sheet.quality.find((x) => x.id === id)
  return q && { quality: q.quality, outline: q.outline, satisfies: q.satisfies, source: q.source, stimulus: q.stimulus, artifact: q.artifact, environment: q.environment, response: q.response, measure: q.measure, evidence: q.evidence }
}

/** What the form starts with: the entry's own values when it is being edited, otherwise empty (or the given defaults). */
export function initialValues(kind: Kind, sheet: RequirementsSheet, id?: string | null, defaults: Values = {}): Values {
  const from = existing(kind, sheet, id)
  const out: Values = {}
  for (const f of FIELDS[kind]) {
    const v = from ? from[f.key] : defaults[f.key]
    out[f.key] = f.input === "links" ? list(v) : str(v)
  }
  return out
}

export function toChange(op: Op, kind: Kind, id: string | null | undefined, values: Values): Change {
  const fields: Values = {}
  for (const f of FIELDS[kind]) {
    const v = values[f.key]
    fields[f.key] = f.input === "links" ? list(v) : str(v).replace(/\s+/g, " ").trim()
  }
  return { op, kind, id: id ?? null, fields: op === "delete" ? {} : fields }
}

/** The required fields still empty, by label, so the form can say what is missing before it asks the server. */
export function missingRequired(kind: Kind, values: Values): string[] {
  return FIELDS[kind].filter((f) => f.required && !str(values[f.key]).trim()).map((f) => f.label)
}

export function groupImpact(impact: Impact[]): { up: Impact[]; down: Impact[]; here: Impact[] } {
  return { up: impact.filter((i) => i.direction === "up"), down: impact.filter((i) => i.direction === "down"), here: impact.filter((i) => i.direction === "here") }
}

/** "3 to read again, 17 may be affected": the size of the blast radius in a line. */
export function radius(impact: Impact[]): string {
  const n = (e: Effect) => impact.filter((i) => i.effect === e).length
  const parts = [
    n("needs-review") && `${n("needs-review")} to read again`,
    n("orphaned") && `${n("orphaned")} left with nothing above`,
    n("status-changes") && `${n("status-changes")} changing status`,
    n("affected") && `${n("affected")} may be affected`,
  ].filter(Boolean)
  return parts.length ? parts.join(", ") : "Nothing else is affected"
}
