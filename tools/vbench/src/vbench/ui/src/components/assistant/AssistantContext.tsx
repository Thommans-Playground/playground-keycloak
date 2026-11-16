import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react"
import { useLocation } from "react-router-dom"

import { buildHistory, isShortcut, withAbout, type About, type Message } from "@/lib/assistant"
import { streamChat } from "@/lib/chat-stream"
import { useSession } from "@/lib/write"

export const LAUNCHER_ATTRIBUTE = "data-assistant-launcher"

interface Assistant {
  available: boolean
  agent: string
  isOpen: boolean
  busy: boolean
  messages: Message[]
  open: () => void
  close: () => void
  toggle: () => void
  ask: (question: string, about?: About) => void
  stop: () => void
  retry: () => void
  clear: () => void
}

const NONE: Assistant = {
  available: false, agent: "", isOpen: false, busy: false, messages: [],
  open: () => {}, close: () => {}, toggle: () => {}, ask: () => {}, stop: () => {}, retry: () => {}, clear: () => {},
}

const Ctx = createContext<Assistant>(NONE)
export const useAssistant = () => useContext(Ctx)

let counter = 0
const nextId = (prefix: string) => `${prefix}-${Date.now().toString(36)}-${(counter++).toString(36)}`

/** Gives the keyboard back to whichever launcher is on the page. */
export function focusLauncher() {
  document.querySelector<HTMLElement>(`[${LAUNCHER_ATTRIBUTE}]`)?.focus()
}

// Holds the one conversation, whether the panel is open, and the request in flight. Nothing is stored: a reload starts afresh,
// and the history goes with each question because the server keeps none.
export function AssistantProvider({ children }: { children: ReactNode }) {
  const session = useSession()
  const { pathname } = useLocation()
  const available = Boolean(session.chat && session.token)
  const [isOpen, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [busy, setBusy] = useState(false)
  const abort = useRef<AbortController | null>(null)
  const thread = useRef<Message[]>([])
  const page = useRef(pathname)
  page.current = pathname
  thread.current = messages

  const patch = useCallback((id: string, change: (m: Message) => Message) => setMessages((all) => all.map((m) => (m.id === id ? change(m) : m))), [])

  const run = useCallback(
    async (question: string, about: About | undefined, before: Message[]) => {
      if (!session.token) return
      const user: Message = { id: nextId("u"), role: "user", content: question, about }
      const answer: Message = { id: nextId("a"), role: "assistant", content: "", pending: true, tools: [] }
      const history = buildHistory(before)
      setMessages([...before, user, answer])
      setBusy(true)
      const controller = new AbortController()
      abort.current = controller
      try {
        await streamChat(session.token, { message: about ? withAbout(question, about) : question, history, page: page.current, about }, controller.signal, (e) => {
          if (e.type === "token") patch(answer.id, (m) => ({ ...m, content: m.content + e.text }))
          else if (e.type === "tool") patch(answer.id, (m) => ({ ...m, tools: [...(m.tools ?? []).filter((t) => t.label !== e.label), { name: e.name, label: e.label }] }))
          else if (e.type === "error") patch(answer.id, (m) => ({ ...m, failed: e.message }))
        })
        patch(answer.id, (m) => ({ ...m, pending: false, failed: m.failed ?? (m.content.trim() ? undefined : "The assistant sent no answer.") }))
      } catch (error) {
        const stopped = error instanceof DOMException && error.name === "AbortError"
        patch(answer.id, (m) => ({ ...m, pending: false, failed: stopped ? (m.content.trim() ? undefined : "Stopped.") : error instanceof Error ? error.message : "The assistant could not answer." }))
      } finally {
        if (abort.current === controller) abort.current = null
        setBusy(false)
      }
    },
    [session.token, patch],
  )

  const ask = useCallback(
    (question: string, about?: About) => {
      const q = question.trim()
      if (!available || !q || abort.current) return
      setOpen(true)
      void run(q, about, thread.current)
    },
    [available, run],
  )

  const stop = useCallback(() => abort.current?.abort(), [])
  const clear = useCallback(() => {
    abort.current?.abort()
    setMessages([])
  }, [])
  const retry = useCallback(() => {
    if (abort.current) return
    const all = thread.current
    const last = [...all].reverse().findIndex((m) => m.role === "user")
    if (last < 0) return
    const at = all.length - 1 - last
    const user = all[at]
    void run(user.content, user.about, all.slice(0, at))
  }, [run])

  const open = useCallback(() => available && setOpen(true), [available])
  const close = useCallback(() => setOpen(false), [])
  const toggle = useCallback(() => available && setOpen((o) => !o), [available])

  // Ctrl or Cmd with / toggles the panel from anywhere; Escape closes it (unless something over it, a dialog or menu, took the key).
  useEffect(() => {
    if (!available) return
    const key = (e: KeyboardEvent) => {
      if (isShortcut(e)) {
        e.preventDefault()
        setOpen((o) => {
          if (o) window.setTimeout(focusLauncher, 0)
          return !o
        })
      } else if (e.key === "Escape" && !e.defaultPrevented && isOpenRef.current && !document.querySelector('[role="dialog"], [role="menu"]')) {
        setOpen(false)
        window.setTimeout(focusLauncher, 0)
      }
    }
    window.addEventListener("keydown", key)
    return () => window.removeEventListener("keydown", key)
  }, [available])
  const isOpenRef = useRef(false)
  isOpenRef.current = isOpen

  useEffect(() => () => abort.current?.abort(), [])

  const value = useMemo<Assistant>(
    () => (available ? { available, agent: session.agent, isOpen, busy, messages, open, close, toggle, ask, stop, retry, clear } : NONE),
    [available, session.agent, isOpen, busy, messages, open, close, toggle, ask, stop, retry, clear],
  )
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
