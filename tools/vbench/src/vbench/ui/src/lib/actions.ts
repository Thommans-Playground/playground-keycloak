import type { Intent } from "@/components/change/ChangeSheet"

// What can be done from a row or a record, as data: a label, where it sits in the menu, and the change it opens. The menu
// only renders this; keeping it here means every row of a kind offers the same things, and a test can say what they are.
export interface ActionSpec {
  key: string
  label: string
  group: "add" | "change"
  intent: Intent
  destructive?: boolean
  unavailable?: string // why it cannot be done now; the item is shown but disabled, with this as its reason
}

export type Target =
  | { kind: "problem"; id: string }
  | { kind: "request"; id: string }
  | { kind: "functional" | "quality"; id: string; ucs: { id: string }[] }
  | { kind: "usecase"; id: string; realises: string[] }

const edit = (kind: "problem" | "request" | "functional" | "quality", id: string, noun: string): ActionSpec[] => [
  { key: "edit", label: `Edit ${noun}`, group: "change", intent: { op: "update", kind, id } },
  { key: "delete", label: `Delete ${noun}`, group: "change", intent: { op: "delete", kind, id }, destructive: true },
]

export function actionsFor(t: Target): ActionSpec[] {
  if (t.kind === "problem") {
    return [
      { key: "add-request", label: "Add a request for this problem", group: "add", intent: { op: "add", kind: "request", defaults: { problems: [t.id] } } },
      ...edit("problem", t.id, "problem"),
    ]
  }
  if (t.kind === "request") {
    return [
      { key: "add-functional", label: "Add a functional requirement", group: "add", intent: { op: "add", kind: "functional", defaults: { satisfies: [t.id] } } },
      { key: "add-quality", label: "Add a quality requirement", group: "add", intent: { op: "add", kind: "quality", defaults: { satisfies: [t.id] } } },
      ...edit("request", t.id, "request"),
    ]
  }
  if (t.kind === "usecase") {
    return [{ key: "add-criterion", label: "Add a criterion", group: "add", intent: { op: "add", kind: "criterion", defaults: { uc: t.id, satisfies: t.realises } } }]
  }
  return [
    { key: "add-usecase", label: "Add a use case that realises it", group: "add", intent: { op: "add", kind: "usecase", defaults: { realises: [t.id] } } },
    {
      key: "add-criterion", label: "Add a criterion", group: "add",
      intent: { op: "add", kind: "criterion", defaults: { uc: t.ucs.length === 1 ? t.ucs[0].id : "", satisfies: [t.id] } },
      unavailable: t.ucs.length ? undefined : "A use case comes first",
    },
    ...edit(t.kind, t.id, t.kind === "functional" ? "requirement" : "quality requirement"),
  ]
}
