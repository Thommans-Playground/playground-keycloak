import { useState } from "react"
import { Link } from "react-router-dom"

import { Badge } from "@/components/ui/badge"
import { EFFECT_WORD, groupImpact, type FieldSpec, type Impact, type Values } from "@/lib/changes"
import type { RequirementsSheet } from "@/lib/types"
import { cn } from "@/lib/utils"

const control = "w-full rounded-control border border-input bg-surface px-3 py-2 text-[15px] placeholder:text-subtle"

// The lines a change would add or remove, as a diff: green added, orange removed, grey context.
export function DiffView({ diff }: { diff: string }) {
  if (!diff) return <p className="text-sm text-muted-foreground">No file would change.</p>
  return (
    <pre className="max-h-72 overflow-auto rounded-control border border-border bg-surface-2 py-2 font-mono text-xs leading-5" aria-label="The change to the files">
      {diff.split("\n").map((line, i) => (
        <span
          key={i}
          className={cn(
            "block whitespace-pre-wrap break-words px-3",
            line.startsWith("+") && !line.startsWith("+++") && "bg-ok-bg text-ok-text",
            line.startsWith("-") && !line.startsWith("---") && "bg-risk-bg text-risk-text",
            (line.startsWith("@@") || line.startsWith("---") || line.startsWith("+++")) && "text-muted-foreground",
          )}
        >
          {line || " "}
        </span>
      ))}
    </pre>
  )
}

const to = (i: Impact) =>
  i.kind === "usecase" ? `/use-cases/${i.id}`
  : i.kind === "criterion" ? "/traceability"
  : i.kind === "test" ? `/v/unit/${encodeURIComponent(i.id)}`
  : `/v/requirements/${encodeURIComponent(i.id)}`

function Row({ i }: { i: Impact }) {
  const e = EFFECT_WORD[i.effect]
  return (
    <li className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 border-b border-divider py-2 last:border-0">
      <Link to={to(i)} className="whitespace-nowrap font-mono text-xs font-semibold text-ink no-underline hover:underline">{i.id.length > 40 ? `${i.id.slice(0, 38)}…` : i.id}</Link>
      <Badge tone={e.tone}>{e.word}</Badge>
      {i.auto && <span className="text-xs text-muted-foreground">done by this change</span>}
      <span className="basis-full text-[13px] text-ink-2">{i.detail}{i.label ? <span className="text-muted-foreground"> · {i.label.slice(0, 70)}</span> : null}</span>
    </li>
  )
}

function Group({ title, hint, items }: { title: string; hint: string; items: Impact[] }) {
  const [all, setAll] = useState(false)
  const direct = items.filter((i) => i.effect !== "affected")
  const far = items.filter((i) => i.effect === "affected")
  return (
    <section aria-label={title}>
      <h4 className="t-headline text-ink">{title} <span className="font-mono text-[15px] font-normal text-muted-foreground">{items.length}</span></h4>
      <p className="t-footnote mb-1 text-muted-foreground">{hint}</p>
      {items.length === 0 ? <p className="text-[13px] text-subtle">Nothing.</p> : (
        <ul>
          {direct.map((i) => <Row key={`${i.id}-${i.effect}`} i={i} />)}
          {(all ? far : far.slice(0, 3)).map((i) => <Row key={`${i.id}-${i.effect}`} i={i} />)}
        </ul>
      )}
      {far.length > 3 && (
        <button type="button" onClick={() => setAll((a) => !a)} className="mt-1 min-h-9 text-[13px] font-medium text-link hover:underline">
          {all ? "Show fewer" : `Show ${far.length - 3} more that may be affected`}
        </button>
      )}
    </section>
  )
}

// The blast radius: what else the change touches, up toward the problem and down toward the tests.
export function ImpactView({ impact }: { impact: Impact[] }) {
  const g = groupImpact(impact)
  return (
    <div className="grid gap-5 md:grid-cols-2">
      <Group title="Up the trace" hint="Toward the problem." items={g.up} />
      <Group title="Down the trace" hint="Toward the tests." items={g.down} />
    </div>
  )
}

// The existing problems or requests a link can point at, as a list to tick.
function LinkPicker({ spec, value, sheet, onChange }: { spec: FieldSpec; value: string[]; sheet: RequirementsSheet; onChange: (v: string[]) => void }) {
  const options =
    spec.links === "problem" ? sheet.problems.filter((p) => p.id).map((p) => ({ id: p.id, text: p.text }))
    : spec.links === "requirement" ? [...sheet.functional.map((f) => ({ id: f.id, text: f.text })), ...sheet.quality.map((q) => ({ id: q.id, text: `${q.quality}: ${q.outline}` }))]
    : sheet.requests.map((r) => ({ id: r.id, text: r.text }))
  if (!options.length) return <p className="text-[13px] text-muted-foreground">There are none yet; add one first.</p>
  return (
    <ul className="max-h-44 overflow-auto rounded-control border border-input bg-surface">
      {options.map((o) => (
        <li key={o.id} className="border-b border-divider last:border-0">
          <label className="flex min-h-11 cursor-pointer items-start gap-3 px-3 py-2 hover:bg-hover">
            <input
              type="checkbox" className="mt-1 size-4" checked={value.includes(o.id)}
              onChange={(e) => onChange(e.target.checked ? [...value, o.id] : value.filter((x) => x !== o.id))}
            />
            <span className="min-w-0">
              <span className="block font-mono text-xs font-semibold text-ink">{o.id}</span>
              <span className="block text-[13px] text-ink-2">{o.text.slice(0, 110)}</span>
            </span>
          </label>
        </li>
      ))}
    </ul>
  )
}

export function Field({ spec, value, sheet, useCases = [], onChange, autoFocus }: { spec: FieldSpec; value: string | string[]; sheet: RequirementsSheet; useCases?: { id: string; title: string }[]; onChange: (v: string | string[]) => void; autoFocus?: boolean }) {
  const id = `field-${spec.key}`
  return (
    <div>
      <label htmlFor={id} className="t-subhead font-semibold text-ink">
        {spec.label}{spec.required && <span className="text-risk" aria-hidden="true"> *</span>}
      </label>
      {spec.hint && <p id={`${id}-hint`} className="t-footnote mb-1 text-muted-foreground">{spec.hint}</p>}
      {spec.input === "select" ? (
        <select id={id} value={value as string} autoFocus={autoFocus} aria-required={spec.required} onChange={(e) => onChange(e.target.value)} className={cn(control, "min-h-11")}>
          <option value="">Choose one…</option>
          {useCases.map((u) => <option key={u.id} value={u.id}>{u.id}  {u.title}</option>)}
        </select>
      ) : spec.input === "links" ? (
        <LinkPicker spec={spec} value={value as string[]} sheet={sheet} onChange={onChange} />
      ) : spec.input === "area" ? (
        <textarea id={id} rows={3} value={value as string} autoFocus={autoFocus} aria-describedby={spec.hint ? `${id}-hint` : undefined} aria-required={spec.required} onChange={(e) => onChange(e.target.value)} className={control} />
      ) : (
        <input id={id} type="text" value={value as string} autoFocus={autoFocus} aria-describedby={spec.hint ? `${id}-hint` : undefined} aria-required={spec.required} onChange={(e) => onChange(e.target.value)} className={cn(control, "min-h-11")} />
      )}
    </div>
  )
}

export type { Values }
