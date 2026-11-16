import { parseSse, type About, type StreamEvent, type Turn } from "@/lib/assistant"

export interface ChatRequest {
  message: string
  history: Turn[]
  page?: string
  about?: About
}

/**
 * Asks the server and hands each event to `onEvent` as it arrives. A POST, so it is read from the body's stream rather than
 * with EventSource. Rejects with a message a person can read; an aborted request rejects with an AbortError.
 */
export async function streamChat(token: string, body: ChatRequest, signal: AbortSignal, onEvent: (e: StreamEvent) => void): Promise<void> {
  const r = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Vbench-Token": token },
    body: JSON.stringify(body),
    signal,
  })
  if (!r.ok) {
    const data = (await r.json().catch(() => ({}))) as { error?: string }
    throw new Error(data.error ?? `${r.status} ${r.statusText}`)
  }
  if (!r.body) throw new Error("The server sent no answer.")
  const reader = r.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  for (;;) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const { events, rest } = parseSse(done ? `${buffer}\n\n` : buffer)
    buffer = rest
    for (const e of events) onEvent(e)
    if (done) return
  }
}
