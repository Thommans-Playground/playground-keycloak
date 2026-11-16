import { useEffect, useRef, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Check, GitCommitHorizontal, X } from "lucide-react"

import { OverlapCheck } from "@/components/change/OverlapCheck"
import { DiffView, Field, ImpactView } from "@/components/change/parts"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FIELDS, NOUN, REQUIREMENT_KINDS, initialValues, missingRequired, radius, toChange, type Applied, type Kind, type Op, type Preview, type Session, type Values } from "@/lib/changes"
import type { ProjectState } from "@/lib/types"
import { applyChange, commitChange, previewChange } from "@/lib/write"

export interface Intent {
  op: Op
  kind: Kind
  id?: string
  defaults?: Values
}

type Step = "form" | "review" | "done"

// The panel where a change is made: fill it in, see exactly what it would change and what else it touches, apply it,
// then commit if you want to. Nothing is written until Apply, and nothing is committed until Commit.
export function ChangeSheet({ intent, project, session, reload, onClose }: { intent: Intent; project: ProjectState; session: Session; reload: () => void; onClose: () => void }) {
  const { op, kind, id } = intent
  const navigate = useNavigate()
  const token = session.token ?? ""
  const [values, setValues] = useState<Values>(() => initialValues(kind, project.requirements, id, intent.defaults))
  const [step, setStep] = useState<Step>(op === "delete" ? "review" : "form")
  const [preview, setPreview] = useState<Preview | null>(null)
  const [applied, setApplied] = useState<Applied | null>(null)
  const [committed, setCommitted] = useState<{ commit: string; message: string } | null>(null)
  const [busy, setBusy] = useState(false)
  const [problem, setProblem] = useState("")
  const panel = useRef<HTMLDivElement>(null)

  const change = () => toChange(op, kind, id, values)

  const run = async (work: () => Promise<void>) => {
    setBusy(true)
    setProblem("")
    try {
      await work()
    } catch (e) {
      setProblem(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  const review = () =>
    run(async () => {
      const missing = missingRequired(kind, values)
      if (op !== "delete" && missing.length) throw new Error(`Fill in: ${missing.join(", ")}.`)
      setPreview(await previewChange(token, change()))
      setStep("review")
    })

  useEffect(() => {
    if (op === "delete") void review()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const key = (e: KeyboardEvent) => e.key === "Escape" && !busy && onClose()
    document.addEventListener("keydown", key)
    return () => document.removeEventListener("keydown", key)
  }, [busy, onClose])

  const apply = () =>
    run(async () => {
      if (!preview) return
      const done = await applyChange(token, preview.change, preview.digest)
      setApplied(done)
      setStep("done")
      reload()
    })

  const commit = () =>
    run(async () => {
      if (!applied) return
      setCommitted(await commitChange(token, [...new Set([...applied.written, ...applied.regenerated])], applied.summary))
    })

  const finish = () => {
    onClose()
    if (applied && op === "add" && applied.id) {
      if (kind === "usecase") navigate(`/use-cases/${applied.id}`)
      else if (kind !== "criterion") navigate(`/v/requirements/${encodeURIComponent(applied.id)}`)
    }
    if (applied && op === "delete") navigate("/v/requirements")
  }

  const title = op === "add" ? `Add ${/^(?!use)[aeiou]/i.test(NOUN[kind]) ? "an" : "a"} ${NOUN[kind]}` : op === "update" ? `Edit ${id}` : `Delete ${id}`
  const blocked = session.blocked
  const stale = problem.startsWith("The files changed")
  const failing = applied?.gates.filter((g) => !g.ok) ?? []

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40" role="presentation">
      <div ref={panel} role="dialog" aria-modal="true" aria-labelledby="change-title" className="flex h-full w-full max-w-2xl flex-col bg-page shadow-e4">
        <header className="flex items-start justify-between gap-3 border-b border-border bg-surface px-6 py-4">
          <div>
            <p className="t-overline">{step === "form" ? "Step 1 of 3 · Write it" : step === "review" ? "Step 2 of 3 · Check it" : "Step 3 of 3 · Done"}</p>
            <h2 id="change-title" className="t-title mt-1 text-ink">{title}</h2>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} disabled={busy} aria-label="Close without saving"><X aria-hidden="true" /></Button>
        </header>

        <div className="flex-1 space-y-6 overflow-y-auto px-6 py-5">
          {blocked && <p role="status" className="rounded-control border border-warn/40 bg-warn-bg px-4 py-3 text-[13px] text-warn-text">{blocked} You can look, but not apply.</p>}
          {problem && (
            <p role="alert" className="rounded-control border border-risk/40 bg-risk-bg px-4 py-3 text-[13px] text-risk-text">
              {problem}{stale && <> <button type="button" onClick={review} className="font-semibold underline">Preview again</button></>}
            </p>
          )}

          {step === "form" && (
            <form onSubmit={(e) => { e.preventDefault(); void review() }} className="space-y-5" id="change-form">
              {FIELDS[kind].map((f, i) => (
                <Field key={f.key} spec={f} value={values[f.key]} sheet={project.requirements} useCases={project.useCases} autoFocus={i === 0} onChange={(v) => setValues((cur) => ({ ...cur, [f.key]: v }))} />
              ))}
              {op === "add" && REQUIREMENT_KINDS.includes(kind) && <OverlapCheck kind={kind} values={values} session={session} />}
            </form>
          )}

          {step === "review" && preview && (
            <>
              <section>
                <h3 className="t-headline text-ink">{preview.summary}</h3>
                {preview.nextStep && <p className="t-subhead mt-1 text-muted-foreground">{preview.nextStep}</p>}
              </section>
              {preview.errors.length > 0 && (
                <ul role="alert" className="space-y-1 rounded-control border border-risk/40 bg-risk-bg px-4 py-3 text-[13px] text-risk-text">
                  {preview.errors.map((e) => <li key={e}>{e}</li>)}
                </ul>
              )}
              {preview.warnings.length > 0 && (
                <ul className="space-y-1 rounded-control border border-warn/40 bg-warn-bg px-4 py-3 text-[13px] text-warn-text">
                  {preview.warnings.map((w) => <li key={w}>{w}</li>)}
                </ul>
              )}
              <section>
                <h3 className="t-headline mb-2 text-ink">What changes in the files</h3>
                <DiffView diff={preview.diff} />
              </section>
              <section>
                <h3 className="t-headline text-ink">What else it touches</h3>
                <p className="t-subhead mb-3 text-muted-foreground">{radius(preview.impact)}. Links inside the requirements doc are cleaned up for you; anything in a spec, a criterion or a test is for you to read again.</p>
                <ImpactView impact={preview.impact} />
              </section>
            </>
          )}

          {step === "review" && !preview && !problem && <p className="text-sm text-muted-foreground">Working out what it touches…</p>}

          {step === "done" && applied && (
            <>
              <section className="flex items-center gap-2"><Check className="size-5 text-ok" aria-hidden="true" /><h3 className="t-headline text-ink">{applied.summary}: written</h3></section>
              <section>
                <h3 className="t-subhead mb-2 font-semibold text-ink">The checks, run again</h3>
                <ul className="flex flex-wrap gap-2">
                  {applied.gates.map((g) => <li key={g.name}><Badge tone={g.ok ? "ok" : "risk"}>{g.name}: {g.ok ? "passing" : "failing"}</Badge></li>)}
                </ul>
                {failing.length > 0 && <p className="t-footnote mt-2 text-muted-foreground">Failing: {failing.map((g) => g.name).join(", ")}. A check that was already failing before this change stays failing; <span className="font-mono">vbench check {failing[0].name}</span> says why.</p>}
              </section>
              {applied.nextStep && <p className="t-subhead text-muted-foreground">{applied.nextStep}</p>}
              <section>
                <h3 className="t-subhead mb-1 font-semibold text-ink">Files written</h3>
                <ul className="font-mono text-xs text-ink-2">{[...new Set([...applied.written, ...applied.regenerated])].map((p) => <li key={p}>{p}</li>)}</ul>
              </section>
              {committed ? (
                <p role="status" className="rounded-control border border-ok/40 bg-ok-bg px-4 py-3 text-[13px] text-ok-text"><GitCommitHorizontal className="mr-1.5 inline size-4" aria-hidden="true" />Committed <span className="font-mono font-semibold">{committed.commit}</span>: {committed.message}</p>
              ) : (
                <p className="t-footnote text-muted-foreground">Not committed yet. Commit records only these files, with a one-line message.</p>
              )}
            </>
          )}
        </div>

        <footer className="flex flex-wrap items-center justify-end gap-3 border-t border-border bg-surface px-6 py-4">
          {step === "form" && (
            <>
              <Button variant="secondary" onClick={onClose} disabled={busy}>Cancel</Button>
              <Button type="submit" form="change-form" disabled={busy}>{busy ? "Checking…" : "Review the change"}</Button>
            </>
          )}
          {step === "review" && (
            <>
              {op !== "delete" && <Button variant="secondary" onClick={() => setStep("form")} disabled={busy}>Back to edit</Button>}
              {op === "delete" && <Button variant="secondary" onClick={onClose} disabled={busy}>Keep it</Button>}
              <Button variant={op === "delete" ? "destructive" : "default"} onClick={apply} disabled={busy || !preview || preview.errors.length > 0 || !preview.digest || Boolean(blocked)}>
                {busy ? "Working…" : op === "delete" ? `Delete ${id}` : "Apply the change"}
              </Button>
            </>
          )}
          {step === "done" && (
            <>
              {!committed && <Button variant="secondary" onClick={commit} disabled={busy || Boolean(blocked)}><GitCommitHorizontal aria-hidden="true" />{busy ? "Committing…" : "Commit these files"}</Button>}
              {applied?.id && op !== "delete" && kind !== "criterion" && <Link to={kind === "usecase" ? `/use-cases/${applied.id}` : `/v/requirements/${encodeURIComponent(applied.id)}`} onClick={onClose} className="t-subhead font-medium">Open {applied.id}</Link>}
              <Button onClick={finish}>Done</Button>
            </>
          )}
        </footer>
      </div>
    </div>
  )
}
