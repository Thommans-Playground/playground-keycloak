import { useEffect, useLayoutEffect, useRef, useState, type KeyboardEvent } from "react"
import { useLocation } from "react-router-dom"
import { ArrowUp, Check, Copy, RotateCcw, Square, Trash2, Wrench, X } from "lucide-react"

import { AiSparkle } from "@/components/assistant/AiSparkle"
import { AnswerMarkdown } from "@/components/assistant/AnswerMarkdown"
import { focusLauncher, useAssistant } from "@/components/assistant/AssistantContext"
import { Button } from "@/components/ui/button"
import { pageContext, type Message } from "@/lib/assistant"
import { cn } from "@/lib/utils"

const MARK = "AI-generated · verify against the files"

function Quote({ about }: { about: NonNullable<Message["about"]> }) {
  return (
    <blockquote className="mt-2 rounded-control border-l-[3px] border-[var(--ai-spark)] bg-surface-2 px-3 py-2 text-left">
      <p className="t-caption text-muted-foreground">About</p>
      <p className="mt-0.5 text-[13px] font-semibold text-ink [overflow-wrap:anywhere]">{about.title}</p>
      <p className="mt-0.5 line-clamp-4 whitespace-pre-line text-xs text-ink-2 [overflow-wrap:anywhere]">{about.text}</p>
    </blockquote>
  )
}

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false)
  return (
    <button
      type="button" aria-label={done ? "Copied" : "Copy the answer"} title="Copy the answer"
      onClick={() => navigator.clipboard?.writeText(text).then(() => { setDone(true); window.setTimeout(() => setDone(false), 1500) }).catch(() => {})}
      className="inline-flex size-7 items-center justify-center rounded-control text-muted-foreground hover:bg-hover hover:text-ink"
    >
      {done ? <Check className="size-3.5" aria-hidden="true" /> : <Copy className="size-3.5" aria-hidden="true" />}
    </button>
  )
}

function Bubble({ m, last, onRetry, busy }: { m: Message; last: boolean; onRetry: () => void; busy: boolean }) {
  if (m.role === "user") {
    return (
      <li className="flex flex-col items-end">
        <div className="max-w-[88%] rounded-card rounded-br-control bg-primary px-3.5 py-2.5 text-[14px] text-primary-foreground [overflow-wrap:anywhere]">
          <p className="whitespace-pre-wrap">{m.content}</p>
        </div>
        {m.about && <div className="w-[88%]"><Quote about={m.about} /></div>}
      </li>
    )
  }
  return (
    <li className="flex flex-col items-start gap-2">
      <div className="flex items-center gap-1.5 text-[var(--ai)]"><AiSparkle size={12} /><span className="t-caption font-semibold">Assistant</span></div>
      {(m.tools?.length ?? 0) > 0 && (
        <ul className="flex flex-wrap gap-1.5" aria-label="What the assistant looked at">
          {m.tools!.map((t) => (
            <li key={t.label} className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-2 px-2.5 py-0.5 text-xs text-ink-2">
              <Wrench className="size-3" aria-hidden="true" />{t.label}
            </li>
          ))}
        </ul>
      )}
      {m.content ? (
        <div className="w-full rounded-card rounded-bl-control border border-border bg-surface px-3.5 py-3 text-[14px]" aria-live={m.pending ? "polite" : "off"}>
          <AnswerMarkdown source={m.content} />
        </div>
      ) : m.pending ? (
        <p className="inline-flex items-center gap-2 text-[13px] text-muted-foreground" role="status">
          <span className="flex gap-1" aria-hidden="true">{[0, 1, 2].map((i) => <span key={i} className="size-1.5 animate-pulse rounded-full bg-[var(--ai-spark)]" style={{ animationDelay: `${i * 160}ms` }} />)}</span>
          Reading the project…
        </p>
      ) : null}
      {m.failed && (
        <div role="alert" className="flex w-full flex-wrap items-center justify-between gap-2 rounded-control border border-border bg-surface-2 px-3 py-2 text-[13px] text-ink-2">
          <span className="min-w-0 [overflow-wrap:anywhere]">{m.failed}</span>
          {last && !busy && <Button variant="secondary" size="sm" onClick={onRetry}><RotateCcw aria-hidden="true" />Try again</Button>}
        </div>
      )}
      {m.content && !m.pending && (
        <div className="flex items-center gap-2"><CopyButton text={m.content} /><span className="text-xs text-subtle">{MARK}</span></div>
      )}
    </li>
  )
}

function Composer({ busy, onSend, onStop }: { busy: boolean; onSend: (text: string) => void; onStop: () => void }) {
  const [text, setText] = useState("")
  const box = useRef<HTMLTextAreaElement>(null)
  useLayoutEffect(() => {
    const el = box.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }, [text])
  const send = () => {
    if (busy || !text.trim()) return
    onSend(text)
    setText("")
  }
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      send()
    }
  }
  return (
    <div className="border-t border-border bg-surface p-3">
      <div className="flex items-end gap-2 rounded-card border border-input bg-surface px-3 py-2 focus-within:outline-2 focus-within:outline-ring">
        <label className="sr-only" htmlFor="assistant-question">Ask a question about this project</label>
        <textarea
          id="assistant-question" ref={box} rows={1} value={text} onChange={(e) => setText(e.target.value)} onKeyDown={onKey}
          placeholder="Ask about this project…" maxLength={4000}
          className="max-h-40 min-h-7 flex-1 resize-none bg-transparent py-1 text-[14px] text-ink outline-none placeholder:text-subtle"
        />
        {busy ? (
          <Button size="icon" variant="secondary" onClick={onStop} aria-label="Stop the answer" title="Stop the answer"><Square className="size-3.5 fill-current" aria-hidden="true" /></Button>
        ) : (
          <Button size="icon" onClick={send} disabled={!text.trim()} aria-label="Send" title="Send (Enter)"><ArrowUp aria-hidden="true" /></Button>
        )}
      </div>
      <p className="mt-1.5 px-1 text-xs text-subtle">Enter sends · Shift+Enter adds a line · {MARK}. It reads the project and never changes it.</p>
    </div>
  )
}

function Empty({ onAsk }: { onAsk: (q: string) => void }) {
  const { pathname } = useLocation()
  const page = pageContext(pathname)
  return (
    <div className="flex flex-1 flex-col justify-center gap-5 px-5 py-8">
      <div>
        <span className="inline-flex size-10 items-center justify-center rounded-full bg-[var(--ai-bg)] text-[var(--ai)]"><AiSparkle size={20} /></span>
        <h3 className="t-title mt-3 text-ink">Ask about this project</h3>
        <p className="t-subhead mt-1 text-muted-foreground">It reads the requirements, use cases, tests and gates, and answers from them. You are on <span className="font-medium text-ink-2">{page.label}</span>.</p>
      </div>
      <ul className="space-y-2" aria-label="Suggested questions">
        {page.suggested.map((q) => (
          <li key={q}>
            <button type="button" onClick={() => onAsk(q)} className="flex min-h-11 w-full items-center gap-2.5 rounded-card border border-border bg-surface px-3.5 py-2 text-left text-[13px] text-ink hover:bg-hover">
              <AiSparkle size={13} className="shrink-0 text-[var(--ai-spark)]" /><span>{q}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

// The docked panel: a header, the thread (or the questions worth asking on this page), and the composer.
export function AssistantPanel() {
  const a = useAssistant()
  const end = useRef<HTMLDivElement>(null)
  const panel = useRef<HTMLElement>(null)
  const last = a.messages[a.messages.length - 1]

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" })
  }, [a.messages.length, last?.content.length, last?.tools?.length])
  useEffect(() => {
    panel.current?.querySelector<HTMLTextAreaElement>("textarea")?.focus()
  }, [])

  return (
    <aside
      ref={panel} aria-label="Assistant" id="assistant-panel"
      className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[26rem] flex-col border-l border-border bg-surface shadow-e2 lg:sticky lg:top-0 lg:z-20 lg:h-screen lg:max-w-none lg:w-[26rem] lg:shrink-0 lg:self-start lg:shadow-none"
    >
      <header className="flex min-h-16 items-center justify-between gap-2 border-b border-border px-4">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-[var(--ai-bg)] text-[var(--ai)]"><AiSparkle size={16} /></span>
          <div className="min-w-0">
            <h2 className="t-subhead truncate font-semibold text-ink">Assistant</h2>
            {a.agent && <p className="t-caption truncate text-muted-foreground">{a.agent}</p>}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Button variant="ghost" size="icon" onClick={a.clear} disabled={a.messages.length === 0} aria-label="Clear the conversation" title="Clear the conversation"><Trash2 aria-hidden="true" /></Button>
          <Button variant="ghost" size="icon" onClick={() => { a.close(); window.setTimeout(focusLauncher, 0) }} aria-label="Close the assistant" title="Close (Esc)"><X aria-hidden="true" /></Button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto" role="log" aria-label="Conversation">
        {a.messages.length === 0 ? (
          <Empty onAsk={(q) => a.ask(q)} />
        ) : (
          <ol className={cn("flex flex-col gap-5 px-4 py-5")}>
            {a.messages.map((m, i) => <Bubble key={m.id} m={m} last={i === a.messages.length - 1} onRetry={a.retry} busy={a.busy} />)}
          </ol>
        )}
        <div ref={end} />
      </div>

      <Composer busy={a.busy} onSend={(t) => a.ask(t)} onStop={a.stop} />
    </aside>
  )
}

// What AppShell puts in its row: the panel when it is open and the server has an assistant, nothing otherwise.
export function AssistantDock() {
  const { available, isOpen } = useAssistant()
  return available && isOpen ? <AssistantPanel /> : null
}
