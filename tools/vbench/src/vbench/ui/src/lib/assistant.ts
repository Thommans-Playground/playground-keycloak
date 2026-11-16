// The assistant, as plain functions: reading the server's event stream, the history sent with each question, what the
// panel offers on each page, and the questions a card can ask. No React and no network in here, so all of it is tested.

export type Role = "user" | "assistant"

export interface About {
  title: string
  text: string
}

export interface Message {
  id: string
  role: Role
  content: string
  about?: About
  tools?: { name: string; label: string }[]
  failed?: string // why the answer did not arrive, on an assistant message
  pending?: boolean
}

export interface Turn {
  role: Role
  content: string
}

export type StreamEvent =
  | { type: "tool"; name: string; label: string }
  | { type: "token"; text: string }
  | { type: "done" }
  | { type: "error"; message: string }

export const MAX_TURNS = 20 // history sent with a question
export const ABOUT_LIMIT = 1800 // characters of a card sent along with a question

/** Splits a growing text into the complete server-sent events in it and the incomplete tail to keep for later. */
export function parseSse(buffer: string): { events: StreamEvent[]; rest: string } {
  const events: StreamEvent[] = []
  const blocks = buffer.replace(/\r\n/g, "\n").split("\n\n")
  const rest = blocks.pop() ?? ""
  for (const block of blocks) {
    let name = "message"
    const data: string[] = []
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) name = line.slice(6).trim()
      else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""))
    }
    if (!data.length && name === "message") continue
    let body: Record<string, unknown> = {}
    try {
      body = data.length ? (JSON.parse(data.join("\n")) as Record<string, unknown>) : {}
    } catch {
      continue
    }
    if (name === "token") events.push({ type: "token", text: String(body.text ?? "") })
    else if (name === "tool") events.push({ type: "tool", name: String(body.name ?? ""), label: String(body.label ?? body.name ?? "") })
    else if (name === "done") events.push({ type: "done" })
    else if (name === "error") events.push({ type: "error", message: String(body.message ?? "The assistant could not answer.") })
  }
  return { events, rest }
}

/** The turns to send: finished exchanges only (no failed or empty answer), the last MAX_TURNS, starting with a question. */
export function buildHistory(messages: Message[]): Turn[] {
  const turns = messages
    .filter((m) => !m.pending && !m.failed && m.content.trim() !== "")
    .map<Turn>((m) => ({ role: m.role, content: m.role === "user" && m.about ? withAbout(m.content, m.about) : m.content }))
  const last = turns.slice(-MAX_TURNS)
  while (last.length && last[0].role !== "user") last.shift()
  return last
}

/** A question with the card it is about quoted under it, as the thread shows it and as the history replays it. */
export function withAbout(question: string, about: About): string {
  return `${question}\n\nAbout "${about.title}":\n${about.text}`
}

/** Keeps a card's text small enough to send. */
export function clip(text: string, limit = ABOUT_LIMIT): string {
  const flat = text.replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim()
  return flat.length > limit ? `${flat.slice(0, limit - 1)}…` : flat
}

/** A card as the assistant is told about it: a title and a few `label: value` lines, empty values left out. */
export function aboutOf(title: string, facts: Record<string, string | number | null | undefined>): About {
  const lines = Object.entries(facts)
    .filter(([, v]) => v !== null && v !== undefined && String(v).trim() !== "")
    .map(([k, v]) => `${k}: ${String(v)}`)
  return { title, text: clip(lines.join("\n")) }
}

export interface PageContext {
  label: string
  suggested: string[]
}

const GENERAL: PageContext = {
  label: "VBenchAI",
  suggested: ["What should I do next?", "Which gates are failing, and why?", "Explain the V-cycle phases in this project."],
}

/** What the panel offers on the page at `path`: its name and questions worth asking there. First match wins. */
export function pageContext(path: string): PageContext {
  const p = path.replace(/\/+$/, "") || "/"
  if (p === "/") return GENERAL
  if (/^\/use-cases\/[^/]+$/.test(p)) {
    const id = decodeURIComponent(p.split("/")[2])
    return {
      label: `Use case ${id}`,
      suggested: [`What is left to finish ${id}?`, `Which criteria of ${id} have no test yet?`, `What does ${id} depend on, and what waits for it?`],
    }
  }
  if (p === "/use-cases") {
    return { label: "Use cases", suggested: ["Which use case should I build next, and why?", "Which use cases are blocked?", "Which use cases have criteria without tests?"] }
  }
  if (/^\/v\/[^/]+\/[^/]+$/.test(p)) {
    return { label: "Item", suggested: ["Explain this item in plain words.", "Which use cases and criteria does it belong to?", "What breaks if I change it?"] }
  }
  if (/^\/v\/requirements$/.test(p)) {
    return { label: "Requirements", suggested: ["Which requirements have no use case yet?", "Which problems are not covered by any request?", "Summarise the quality requirements."] }
  }
  if (/^\/v\/[^/]+$/.test(p)) {
    const phase = decodeURIComponent(p.split("/")[2])
    return { label: `The ${phase} phase`, suggested: [`What belongs in the ${phase} phase?`, `What is missing from the ${phase} phase?`, "Which items here need attention?"] }
  }
  if (p === "/build-order") return { label: "Build order", suggested: ["Why is the build order what it is?", "What blocks the next wave?", "Which use case can start now?"] }
  if (p === "/traceability") return { label: "Traceability", suggested: ["Which requirements are not traced to a test?", "Show the trace from a problem to its tests.", "Where are the gaps in the trace?"] }
  if (p === "/diagrams") return { label: "Diagrams", suggested: ["Which use cases are missing a required diagram?", "What does the sequence diagram of the first use case show?", "Which diagram kinds does our rigor tier require?"] }
  if (p === "/docs") return { label: "Documents", suggested: ["Which document explains the method?", "Summarise the glossary.", "Where is the architecture described?"] }
  if (p === "/settings") return { label: "Settings", suggested: ["What can I change here?"] }
  return GENERAL
}

export interface CardFacts {
  kind: string // "use case", "test", "task", "criterion", "requirement" ...
  ref: string
  title: string
  state?: string
}

/** The questions a card offers: written from what it is, so the assistant is asked something specific. */
export function cardQuestions({ kind, ref, title, state }: CardFacts): string[] {
  const name = `${kind} ${ref}${title && title !== ref ? ` (${title})` : ""}`
  const base = [`Explain ${name} in plain words.`, `What is left to finish ${name}?`, `What breaks if I change ${name}?`]
  if (kind === "criterion") return [`Explain ${name} in plain words.`, `Which test proves ${ref}, and is it enough?`, `What breaks if I change ${name}?`]
  if (kind === "test") return [`What does ${name} check?`, `Which criteria does ${ref} prove?`, `What breaks if I change ${name}?`]
  if (state && /uncovered|tbd|planned|open|risk|warn/i.test(state)) return [`Why is ${name} ${state}?`, ...base.slice(1)]
  return base
}

export const isMac = () => typeof navigator !== "undefined" && /mac|iphone|ipad/i.test(navigator.platform || navigator.userAgent)

/** Ctrl or Cmd with `/` toggles the panel. */
export function isShortcut(e: { key: string; ctrlKey: boolean; metaKey: boolean; altKey: boolean; shiftKey: boolean }): boolean {
  return e.key === "/" && (e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey
}

export const shortcutLabel = (mac: boolean) => (mac ? "⌘/" : "Ctrl+/")
