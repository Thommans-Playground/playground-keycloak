import { Blocks, ClipboardList, Boxes, CircleCheckBig, Code, FlaskConical, ListTree, Plug, Workflow, type LucideIcon } from "lucide-react"

export interface PhaseUi {
  icon: LucideIcon
  blurb: string // what the phase is, in plain words
  lists: string // what the list on its page holds
  empty: string // the empty state
}

export const PHASE_UI: Record<string, PhaseUi> = {
  requirements: {
    icon: ClipboardList,
    blurb: "What the product must do and how well. Each requirement should be realised by a use case and proved by acceptance tests.",
    lists: "Requests, functional and non-functional requirements",
    empty: "No requirements are recorded yet. They come from the discovery brief.",
  },
  "system-design": {
    icon: Boxes,
    blurb: "Which bounded context each use case lives in, and how the contexts relate. System tests prove it.",
    lists: "Bounded contexts and the use cases placed in them",
    empty: "No use case has a bounded context yet.",
  },
  architecture: {
    icon: Blocks,
    blurb: "The structure inside a context: aggregates, ports and adapters, drawn as a domain model and class diagrams. Integration tests prove it.",
    lists: "Domain models and class diagrams",
    empty: "No domain model or class diagram yet. A use case needs one at the full tier.",
  },
  "module-design": {
    icon: ListTree,
    blurb: "How each use case works inside: the task plan, the sequence diagram and, for anything with a lifecycle, the state diagram. Unit tests prove it.",
    lists: "Tasks and the sequence and state diagrams",
    empty: "Nothing is designed yet. `/vbench:v-2-design` plans the tasks and draws the diagrams.",
  },
  code: {
    icon: Code,
    blurb: "The production code, tagged with the use case it realises. It is written test first, at the vertex of the V.",
    lists: "Production files tagged with a use case",
    empty: "No code is tagged with a use case yet.",
  },
  unit: {
    icon: FlaskConical,
    blurb: "Small tests of one behaviour each. They prove the module design.",
    lists: "Unit tests, one per test function",
    empty: "No unit tests are tagged yet. Tag a test `Verifies UC-… · unit rung.`",
  },
  integration: {
    icon: Plug,
    blurb: "Tests that cross a boundary, such as an adapter or another part of the system. They prove the architecture.",
    lists: "Integration tests, one per test function",
    empty: "No integration tests yet. A use case needs them when it crosses a boundary.",
  },
  system: {
    icon: Workflow,
    blurb: "Tests across contexts or the whole pipeline. They prove the system design.",
    lists: "System tests, one per test function",
    empty: "No system tests yet. They matter once more than one context is involved.",
  },
  acceptance: {
    icon: CircleCheckBig,
    blurb: "Tests that show an acceptance criterion is true, through the public interface. They prove the requirements.",
    lists: "Acceptance tests, one per test function",
    empty: "No acceptance tests are tagged yet. Tag a test `Verifies UC-… · acceptance rung.`",
  },
}
