import { useState } from "react"
import { Link } from "react-router-dom"
import { Sparkles } from "lucide-react"

import { useChanges } from "@/components/change/ChangeContext"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { Kind, Overlap, Session, Values } from "@/lib/changes"
import { toChange } from "@/lib/changes"
import { KIND_WORD, VERDICT, canCheck, editable, fingerprint, headline } from "@/lib/overlap"
import { checkOverlap } from "@/lib/write"

// "Does this already exist?", asked in the form where the entry is being written. The wording check is free and local;
// when the server has an agent, it reads the entry beside the related ones and says why. It only advises: the entry is
// still the person's to add, edit instead, or drop.
export function OverlapCheck({ kind, values, session }: { kind: Kind; values: Values; session: Session }) {
  const { open } = useChanges()
  const [result, setResult] = useState<{ answer: Overlap; for: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState("")
  const now = fingerprint(values)
  const stale = result !== null && result.for !== now
  const agent = session.agent

  const ask = async () => {
    setBusy(true)
    setProblem("")
    try {
      setResult({ answer: await checkOverlap(session.token ?? "", toChange("add", kind, null, values)), for: now })
    } catch (e) {
      setProblem(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const a = result?.answer
  const v = a?.verdict ? VERDICT[a.verdict] : null

  return (
    <section aria-label="Does this already exist?" className="rounded-card border border-border bg-surface px-5 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 max-w-sm">
          <h3 className="t-headline text-ink">Does this already exist?</h3>
          <p className="t-footnote mt-0.5 text-muted-foreground">
            {agent ? `${agent} reads it beside the entries it might repeat. This sends the new entry and those entries to Anthropic.` : "Compares the wording with what is already written."}
          </p>
        </div>
        <Button variant="secondary" size="sm" onClick={ask} disabled={busy || !canCheck(kind, values)}>
          {agent && <Sparkles aria-hidden="true" />}{busy ? "Checking…" : agent ? `Ask ${agent.split(" ")[0]}` : "Check"}
        </Button>
      </div>

      {problem && <p role="alert" className="mt-3 text-[13px] text-risk-text">{problem}</p>}

      {a?.checked && v && (
        <div className={stale ? "mt-4 opacity-60" : "mt-4"} aria-live="polite">
          <p className="flex flex-wrap items-center gap-2">
            <Badge tone={v.tone}>{v.word}</Badge>
            {stale && <span className="t-footnote text-muted-foreground">You have edited it since. Check again.</span>}
          </p>
          <p className="t-subhead mt-2 text-ink-2">{headline(a)}</p>
          {a.advice && <p className="t-subhead mt-1 font-medium text-ink">{a.advice}</p>}
          {a.note && <p className="t-footnote mt-1 text-muted-foreground">{a.note}</p>}
          {(a.matches?.length ?? 0) > 0 && (
            <ul className="mt-3">
              {a.matches!.map((m) => (
                <li key={m.id} className="border-t border-divider py-3">
                  <p className="flex flex-wrap items-center gap-2">
                    <Link to={`/v/requirements/${encodeURIComponent(m.id)}`} className="whitespace-nowrap font-mono text-xs font-semibold text-ink no-underline hover:underline">{m.id}</Link>
                    <span className="t-caption text-muted-foreground">{KIND_WORD[m.kind]}</span>
                  </p>
                  <p className="mt-1 text-[13px] text-ink">{m.text.slice(0, 160)}{m.text.length > 160 ? "…" : ""}</p>
                  {m.why && <p className="t-footnote mt-0.5 text-muted-foreground">{m.why}</p>}
                  <p className="mt-1 flex flex-wrap gap-3">
                    <Link to={`/v/requirements/${encodeURIComponent(m.id)}`} className="t-footnote font-medium" target="_blank" rel="noreferrer">Open it</Link>
                    {editable(m, kind) && <button type="button" onClick={() => open({ op: "update", kind, id: m.id })} className="t-footnote font-medium text-link hover:underline">Edit it instead</button>}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}
