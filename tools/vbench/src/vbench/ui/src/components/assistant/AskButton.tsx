import { useEffect, useRef, useState, type KeyboardEvent } from "react"
import { createPortal } from "react-dom"
import { PenLine, X } from "lucide-react"

import { AiSparkle } from "@/components/assistant/AiSparkle"
import { useAssistant } from "@/components/assistant/AssistantContext"
import { Button } from "@/components/ui/button"
import type { About } from "@/lib/assistant"
import { usePopover } from "@/lib/usePopover"

// A small dialog over the page for a question of your own, with the card it is about quoted above the box.
function OwnQuestion({ about, onSend, onClose }: { about: About; onSend: (q: string) => void; onClose: () => void }) {
  const [text, setText] = useState("")
  const box = useRef<HTMLTextAreaElement>(null)
  useEffect(() => box.current?.focus(), [])
  const send = () => text.trim() && onSend(text.trim())
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault()
      onClose()
    } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      send()
    }
  }
  return createPortal(
    <div className="fixed inset-0 z-[60] flex items-start justify-center bg-ink/30 p-4 pt-[15vh]" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div role="dialog" aria-modal="true" aria-labelledby="own-question-h" onKeyDown={onKey} className="w-full max-w-lg rounded-card border border-border bg-surface p-5 shadow-e3">
        <div className="flex items-start justify-between gap-3">
          <h2 id="own-question-h" className="t-title flex items-center gap-2 text-ink"><AiSparkle size={16} className="text-[var(--ai-spark)]" />Ask your own question</h2>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Cancel"><X aria-hidden="true" /></Button>
        </div>
        <blockquote className="mt-3 rounded-control border-l-[3px] border-[var(--ai-spark)] bg-surface-2 px-3 py-2">
          <p className="t-caption text-muted-foreground">About</p>
          <p className="text-[13px] font-semibold text-ink [overflow-wrap:anywhere]">{about.title}</p>
          <p className="line-clamp-4 whitespace-pre-line text-xs text-ink-2 [overflow-wrap:anywhere]">{about.text}</p>
        </blockquote>
        <label htmlFor="own-question" className="sr-only">Your question</label>
        <textarea
          id="own-question" ref={box} rows={3} value={text} onChange={(e) => setText(e.target.value)} maxLength={2000}
          placeholder="What do you want to know about it?"
          className="mt-3 w-full resize-none rounded-control border border-input bg-surface p-3 text-[14px] text-ink placeholder:text-subtle"
        />
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="text-xs text-subtle">Ctrl or ⌘ with Enter sends.</p>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={onClose}>Cancel</Button>
            <Button size="sm" onClick={send} disabled={!text.trim()}>Send</Button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}

// "Ask" at the top right of a card: one pill that opens a short menu of questions written from what the card shows, ending in
// "Ask your own question…". Choosing one opens the assistant with the card quoted under the question. Not on the page at all
// when the server has no assistant.
export function AskButton({ about, questions }: { about: About; questions: string[] }) {
  const { available, ask } = useAssistant()
  const { open, setOpen, root } = usePopover()
  const [own, setOwn] = useState(false)
  if (!available) return null
  return (
    <div ref={root} className="relative">
      <button
        type="button" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen(!open)}
        className="inline-flex min-h-8 items-center gap-1.5 rounded-full bg-[var(--ai-bg)] px-3 text-[13px] font-medium text-[var(--ai)] transition-colors hover:ring-1 hover:ring-[var(--ai-spark)] focus-visible:outline-2 focus-visible:outline-ring"
      >
        <AiSparkle size={13} />Ask
      </button>
      {open && (
        <ul role="menu" aria-label={`Ask about ${about.title}`} className="absolute right-0 top-full z-40 mt-1.5 w-80 max-w-[85vw] overflow-hidden rounded-card border border-border bg-surface py-1 shadow-e3">
          {questions.map((q) => (
            <li key={q} role="none">
              <button role="menuitem" type="button" onClick={() => { setOpen(false); ask(q, about) }} className="flex min-h-10 w-full items-center gap-2 px-3.5 py-2 text-left text-[13px] text-ink hover:bg-hover">
                <AiSparkle size={12} className="shrink-0 text-[var(--ai-spark)]" />{q}
              </button>
            </li>
          ))}
          <li role="none" className="border-t border-divider">
            <button role="menuitem" type="button" onClick={() => { setOpen(false); setOwn(true) }} className="flex min-h-10 w-full items-center gap-2 px-3.5 py-2 text-left text-[13px] font-medium text-link hover:bg-hover">
              <PenLine className="size-3.5 shrink-0" aria-hidden="true" />Ask your own question…
            </button>
          </li>
        </ul>
      )}
      {own && <OwnQuestion about={about} onClose={() => setOwn(false)} onSend={(q) => { setOwn(false); ask(q, about) }} />}
    </div>
  )
}
