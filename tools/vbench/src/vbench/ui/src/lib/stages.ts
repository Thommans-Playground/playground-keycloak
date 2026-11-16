import type { Stage } from "@/lib/types"

export interface StageInfo {
  key: Stage
  label: string // the chip's word
  step: string // the lifecycle step's name
  hint: string // what has to happen to leave this stage
  tone: "neutral" | "warn" | "ok"
}

// The V-cycle stages in order, as `vbench status` derives them. Words, not just colours.
export const STAGES: StageInfo[] = [
  { key: "requirements", label: "Requirements", step: "Requirements", hint: "Write the acceptance criteria.", tone: "neutral" },
  { key: "design", label: "Design", step: "Design", hint: "Plan the tasks and draw the required diagrams.", tone: "neutral" },
  { key: "code", label: "In code", step: "Code", hint: "Build each task test first.", tone: "warn" },
  { key: "rung", label: "Closing tests", step: "Tests and tags", hint: "Tag the code and tests so the rung closes.", tone: "warn" },
  { key: "verify", label: "Built", step: "Verify", hint: "Re-check independently, then ship.", tone: "ok" },
]

export const stageInfo = (s: Stage): StageInfo => STAGES.find((x) => x.key === s) ?? STAGES[0]
