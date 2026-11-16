import { describe, expect, it } from "vitest"

import { aboutOf, buildHistory, cardQuestions, clip, isShortcut, MAX_TURNS, pageContext, parseSse, withAbout, type Message } from "@/lib/assistant"

const msg = (over: Partial<Message> & Pick<Message, "role" | "content">): Message => ({ id: Math.random().toString(), ...over })

describe("parseSse", () => {
  it("reads whole events and keeps the unfinished tail", () => {
    const text = 'event: tool\ndata: {"name":"get_item","label":"Reading UC-N-001"}\n\nevent: token\ndata: {"text":"Hel"}\n\nevent: tok'
    const { events, rest } = parseSse(text)
    expect(events).toEqual([{ type: "tool", name: "get_item", label: "Reading UC-N-001" }, { type: "token", text: "Hel" }])
    expect(rest).toBe("event: tok")
  })

  it("completes an event that arrives in pieces", () => {
    const first = parseSse('event: token\ndata: {"te')
    expect(first.events).toEqual([])
    const second = parseSse(first.rest + 'xt":"lo"}\n\nevent: done\ndata: {}\n\n')
    expect(second.events).toEqual([{ type: "token", text: "lo" }, { type: "done" }])
    expect(second.rest).toBe("")
  })

  it("handles CRLF, error events and ignores bad json", () => {
    const { events } = parseSse('event: error\r\ndata: {"message":"No key"}\r\n\r\nevent: token\r\ndata: not json\r\n\r\n')
    expect(events).toEqual([{ type: "error", message: "No key" }])
  })
})

describe("buildHistory", () => {
  it("drops failed, pending and empty turns, and starts with a question", () => {
    const history = buildHistory([
      msg({ role: "assistant", content: "Welcome" }),
      msg({ role: "user", content: "q1" }),
      msg({ role: "assistant", content: "", pending: true }),
      msg({ role: "user", content: "q2" }),
      msg({ role: "assistant", content: "a2", failed: "boom" }),
    ])
    expect(history).toEqual([{ role: "user", content: "q1" }, { role: "user", content: "q2" }])
  })

  it("keeps only the last turns", () => {
    const many = Array.from({ length: 50 }, (_, i) => msg({ role: i % 2 === 0 ? "user" : "assistant", content: `m${i}` }))
    const history = buildHistory(many)
    expect(history.length).toBeLessThanOrEqual(MAX_TURNS)
    expect(history[0].role).toBe("user")
    expect(history.at(-1)?.content).toBe("m49")
  })

  it("replays the card a question was about", () => {
    const about = { title: "UC-N-001", text: "stage: code" }
    const [turn] = buildHistory([msg({ role: "user", content: "Explain it", about })])
    expect(turn.content).toBe(withAbout("Explain it", about))
    expect(turn.content).toContain('About "UC-N-001"')
  })
})

describe("cards", () => {
  it("clips long text and builds about from facts, leaving empty ones out", () => {
    expect(clip("x".repeat(3000)).length).toBe(1800)
    const about = aboutOf("AC-N-001", { State: "covered", Tests: "", Missing: null, Text: "Given a note" })
    expect(about.text).toBe("State: covered\nText: Given a note")
  })

  it("asks different things of a test, a criterion and an uncovered use case", () => {
    expect(cardQuestions({ kind: "test", ref: "TST-1", title: "test_create" })[0]).toContain("What does test TST-1")
    expect(cardQuestions({ kind: "criterion", ref: "AC-N-001", title: "" })[1]).toContain("Which test proves AC-N-001")
    expect(cardQuestions({ kind: "criterion", ref: "AC-N-001", title: "", state: "uncovered" }).length).toBe(3)
    expect(cardQuestions({ kind: "use case", ref: "UC-N-001", title: "Create note", state: "uncovered" })[0]).toContain("Why is use case UC-N-001")
  })
})

describe("pageContext", () => {
  it("names each page and offers questions about it", () => {
    expect(pageContext("/use-cases/UC-N-001").label).toBe("Use case UC-N-001")
    expect(pageContext("/use-cases/UC-N-001").suggested[0]).toContain("UC-N-001")
    expect(pageContext("/use-cases").label).toBe("Use cases")
    expect(pageContext("/v/requirements").label).toBe("Requirements")
    expect(pageContext("/v/design").label).toBe("The design phase")
    expect(pageContext("/v/design/ARC-1").label).toBe("Item")
    expect(pageContext("/traceability/").label).toBe("Traceability")
    for (const p of ["/", "/build-order", "/diagrams", "/docs", "/settings", "/nope"]) expect(pageContext(p).suggested.length).toBeGreaterThan(0)
  })
})

describe("isShortcut", () => {
  const key = (over: object) => ({ key: "/", ctrlKey: false, metaKey: false, altKey: false, shiftKey: false, ...over })
  it("is Ctrl or Cmd with slash, and nothing else", () => {
    expect(isShortcut(key({ ctrlKey: true }))).toBe(true)
    expect(isShortcut(key({ metaKey: true }))).toBe(true)
    expect(isShortcut(key({}))).toBe(false)
    expect(isShortcut(key({ ctrlKey: true, shiftKey: true }))).toBe(false)
  })
})
