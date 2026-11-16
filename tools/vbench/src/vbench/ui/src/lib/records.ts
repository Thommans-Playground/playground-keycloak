import type { RequirementsSheet, SheetCriterion, SheetFunctional, SheetProblem, SheetQuality, SheetRequest, SheetTest } from "@/lib/types"

export type Requirement =
  | { kind: "problem"; problem: SheetProblem }
  | { kind: "request"; request: SheetRequest }
  | { kind: "functional"; fr: SheetFunctional }
  | { kind: "quality"; nfr: SheetQuality }

// A requirement-side item, found by its id in the requirements sheet.
export function findRequirement(sheet: RequirementsSheet, id: string): Requirement | null {
  const problem = sheet.problems.find((p) => p.id === id)
  if (problem) return { kind: "problem", problem }
  const request = sheet.requests.find((r) => r.id === id)
  if (request) return { kind: "request", request }
  const fr = sheet.functional.find((f) => f.id === id)
  if (fr) return { kind: "functional", fr }
  const nfr = sheet.quality.find((q) => q.id === id)
  return nfr ? { kind: "quality", nfr } : null
}

// Where a requirement came from: the requests that became it, and the problems those requests address.
export function originOf(sheet: RequirementsSheet, id: string): { requests: SheetRequest[]; problems: SheetProblem[] } {
  const requests = sheet.requests.filter((r) => r.requirements.includes(id))
  const wanted = new Set(requests.flatMap((r) => r.problems))
  return { requests, problems: sheet.problems.filter((p) => wanted.has(p.id)) }
}

// What a problem or a request became: the requirements derived from it.
export function becameOf(sheet: RequirementsSheet, req: Requirement): (SheetFunctional | SheetQuality)[] {
  const ids =
    req.kind === "request" ? req.request.requirements
    : req.kind === "problem" ? sheet.requests.filter((r) => r.problems.includes(req.problem.id)).flatMap((r) => r.requirements)
    : []
  const wanted = new Set(ids)
  return [...sheet.functional, ...sheet.quality].filter((r) => wanted.has(r.id))
}

// The tests that prove a set of criteria, each once, with the criteria it proves.
export function testsOf(criteria: SheetCriterion[]): (SheetTest & { proves: string[] })[] {
  const by = new Map<string, SheetTest & { proves: string[] }>()
  for (const c of criteria) {
    for (const t of c.tests) {
      const seen = by.get(t.id)
      if (seen) seen.proves.push(c.id)
      else by.set(t.id, { ...t, proves: [c.id] })
    }
  }
  return [...by.values()]
}
