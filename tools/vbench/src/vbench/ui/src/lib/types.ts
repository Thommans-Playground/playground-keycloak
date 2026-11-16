// The shape of `GET /api/state` (see src/vbench/app/export.py). The UI computes none of this.
export type Stage = "requirements" | "design" | "code" | "rung" | "verify"

export interface UseCase {
  id: string
  title: string
  path: string
  actor: string | null
  context: string | null
  rigor: string
  wave: number
  stage: Stage
  task: string | null // the id of the first open task, while the stage is code
  next: string
  blockedBy: string[]
  dependsOn: string[]
  enables: string[]
  acs: number
  covered: number
  enforced: number
  tasks: number
  tasksClosed: number
  code: boolean
  tested: boolean
}

export type CriterionState = "covered" | "uncovered" | "planned" | "tbd"

export interface Criterion {
  id: string
  uc: string | null
  spec: string
  state: CriterionState
  tests: string[]
  text: string // the Given / when / then sentence
  satisfies: string[] // the requirements it satisfies
}

export interface Rung {
  uc: string
  realisedIn: string[]
  verifiedBy: { file: string; rung: string }[]
}

export interface Gate {
  name: string
  ok: boolean
  lines: string[]
}

export interface DocItem {
  path: string
  title: string
}

export interface DiagramItem {
  path: string
  title: string // the diagram's own title line, or empty
  kind: string
  uc?: string | null
  generated: boolean
}

export type ItemStatus = "ok" | "warn" | "risk" | "neutral"

/** One thing the project holds, placed on a phase of the V (see src/vbench/domain/vview.py). */
export interface VItem {
  id: string
  ref: string // the id a person reads and quotes (REQ-FR-001, CTX-notes, CODE-notes/create.py); `id` is the stable key
  phase: string
  kind: string
  title: string
  ucs: string[]
  file: string | null
  line: number | null
  status: ItemStatus
  label: string // the status word, always shown with the colour
  acs: string[]
  description: string // what it is, in words; the title is its name
}

export interface VPhase {
  key: string
  label: string
  arm: "left" | "vertex" | "right"
  pairs: string | null // the phase on the other arm that proves it
}

export interface VStats {
  useCases: { built: number; total: number }
  criteria: { covered: number; total: number }
  tasks: { closed: number; total: number }
  requirements: { realised: number; total: number }
  tests: { unit: number; integration: number; system: number; acceptance: number; unplaced: number }
  gates: { passing: number; total: number }
}

export interface VView {
  phases: VPhase[]
  items: VItem[]
  unplaced: VItem[]
  stats: VStats
}

export interface SheetTest {
  ref: string
  id: string
  phase: string
  title: string
}

export interface SheetCriterion {
  id: string
  uc: string | null
  text: string
  state: CriterionState
  tests: SheetTest[]
}

// What is related to one requirement: its use cases, the criteria that satisfy it, the tests that prove them.
export interface SheetRelated {
  status: ItemStatus
  label: string
  ucs: { id: string; title: string }[]
  criteria: SheetCriterion[]
}

export interface SheetFunctional extends SheetRelated {
  id: string
  text: string
  story: string
  satisfies: string[]
}

export interface SheetQuality extends SheetRelated {
  id: string
  quality: string
  outline: string
  source: string
  stimulus: string
  artifact: string
  environment: string
  response: string
  measure: string
  satisfies: string[]
  evidence: string
}

export interface SheetProblem {
  id: string // empty for a problem written as a paragraph in a doc that predates the table
  text: string
  who: string
  cost: string
  status: ItemStatus
  label: string
  requests: string[] // the requests that address it
}

export interface SheetRequest {
  id: string
  raisedBy: string
  text: string
  problems: string[]
  requirements: string[]
}

export interface RequirementsSheet {
  problems: SheetProblem[]
  requests: SheetRequest[]
  functional: SheetFunctional[]
  quality: SheetQuality[]
}

export interface ProjectState {
  branch: string
  next: { command: string | null; uc: string | null; why: string; purpose: string; blocked: Record<string, string[]> }
  gates: Gate[]
  v: VView
  requirements: RequirementsSheet
  useCases: UseCase[]
  criteria: Criterion[]
  rungs: Rung[]
  orphans: string[]
  docs: DocItem[]
  diagrams: DiagramItem[]
  graph: string
}
