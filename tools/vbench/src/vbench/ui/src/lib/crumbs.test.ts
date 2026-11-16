import { describe, expect, it } from "vitest"

import { itemSwitch, phaseSwitch, useCaseSwitch } from "@/lib/crumbs"
import type { ProjectState, VItem } from "@/lib/types"

const item = (over: Partial<VItem> & Pick<VItem, "id" | "phase">): VItem => ({
  ref: over.id, kind: "FR", title: over.id, ucs: [], file: null, line: null, status: "ok", label: "", acs: [], description: "", ...over,
})

const project = {
  useCases: [
    { id: "UC-N-001", title: "Create note", next: "/vbench:v-4-verify UC-N-001" },
    { id: "UC-N-002", title: "Read note", next: "/vbench:v-3-code UC-N-002" },
  ],
  v: {
    phases: [{ key: "requirements", label: "Requirements" }, { key: "code", label: "Code" }],
    items: [
      item({ id: "REQ-FR-001", phase: "requirements", description: "As an author, I want to save a note" }),
      item({ id: "REQ-FR-002", phase: "requirements" }),
      item({ id: "src/a.py", ref: "COD-SRC-001", phase: "code", title: "a.py", description: "Does a thing" }),
    ],
  },
} as unknown as ProjectState

describe("breadcrumb switches", () => {
  it("offers every use case, named, with where each one is going next", () => {
    const s = useCaseSwitch(project, "UC-N-002")
    expect(s.items.map((i) => i.label)).toEqual(["UC-N-001  Create note", "UC-N-002  Read note"])
    expect(s.items[1]).toMatchObject({ detail: "/vbench:v-3-code UC-N-002", to: "/use-cases/UC-N-002" })
    expect(s.currentId).toBe("UC-N-002")
    expect(s.all).toEqual({ label: "All use cases", to: "/use-cases" })
  })

  it("offers every phase with a counted, correctly pluralised detail", () => {
    const s = phaseSwitch(project, "code")
    expect(s.items.map((i) => [i.id, i.detail])).toEqual([["requirements", "2 items"], ["code", "1 item"]])
  })

  it("offers the other items of the same phase, each with its id, its name and what it is", () => {
    const s = itemSwitch(project, "requirements", "REQ-FR-001")
    expect(s.items).toHaveLength(2)
    expect(s.items[0]).toMatchObject({ label: "REQ-FR-001  REQ-FR-001", detail: "As an author, I want to save a note" })
    expect(itemSwitch(project, "code", "src/a.py").items[0].label).toBe("COD-SRC-001  a.py")
  })
})
