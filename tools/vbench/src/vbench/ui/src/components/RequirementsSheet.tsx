import type { ReactNode } from "react"
import { Link } from "react-router-dom"

import { EmptyState } from "@/components/PageHeader"
import { Badge } from "@/components/ui/badge"
import { Card } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { CRITERION_STATE } from "@/lib/status"
import type { RequirementsSheet as Sheet, SheetCriterion, SheetRelated } from "@/lib/types"

const here = (id: string) => `/v/requirements/${encodeURIComponent(id)}`

function Section({ id, title, hint, count, action, children }: { id: string; title: string; hint: string; count?: number; action?: ReactNode; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-h`} className="scroll-mt-32">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id={`${id}-h`} className="t-title text-ink">
          {title}
          {count !== undefined && <span className="ml-2 font-mono text-[15px] font-normal text-muted-foreground">{count}</span>}
        </h2>
        {action}
      </div>
      <p className="t-subhead mb-3 mt-1 max-w-3xl text-muted-foreground">{hint}</p>
      {children}
    </section>
  )
}

const Text = ({ id, children, className }: { id: string; children: ReactNode; className?: string }) => (
  <Link to={here(id)} className={`text-ink no-underline hover:underline ${className ?? ""}`}>{children}</Link>
)

const Id = ({ id }: { id: string }) => (
  <Link to={here(id)} className="whitespace-nowrap font-mono text-[13px] font-semibold text-ink no-underline hover:underline">{id}</Link>
)

function UseCases({ ucs }: { ucs: SheetRelated["ucs"] }) {
  if (!ucs.length) return <span className="text-subtle">None yet</span>
  return (
    <ul className="space-y-1.5">
      {ucs.map((u) => (
        <li key={u.id}>
          <Link to={`/use-cases/${u.id}`} className="font-mono text-[13px] font-semibold no-underline hover:underline">{u.id}</Link>
          <span className="block text-[13px] text-muted-foreground">{u.title}</span>
        </li>
      ))}
    </ul>
  )
}

// A criterion, its state, the sentence it says, and the tests that prove it: everything about "done" in one place.
function Criteria({ criteria }: { criteria: SheetCriterion[] }) {
  if (!criteria.length) return <span className="text-subtle">None yet: they are written in the use case&apos;s spec.</span>
  return (
    <ul className="divide-y divide-divider">
      {criteria.map((c) => {
        const s = CRITERION_STATE[c.state]
        return (
          <li key={c.id} className="py-2 first:pt-0 last:pb-0">
            <p className="flex flex-wrap items-center gap-2">
              {c.uc ? (
                <Link to={`/use-cases/${c.uc}#criteria`} className="font-mono text-[13px] font-semibold text-ink no-underline hover:underline">{c.id}</Link>
              ) : (
                <span className="font-mono text-[13px] font-semibold text-ink">{c.id}</span>
              )}
              <Badge tone={s.tone}>{s.word}</Badge>
            </p>
            <p className="mt-1 text-ink-2">{c.text || <span className="text-subtle">No sentence written yet.</span>}</p>
            {c.tests.length > 0 && (
              <p className="mt-1 text-[13px] text-muted-foreground">
                Proved by{" "}
                {c.tests.map((t, i) => (
                  <span key={t.id}>
                    {i > 0 && ", "}
                    <Link to={`/v/${t.phase}/${encodeURIComponent(t.id)}`} className="font-mono text-xs" title={t.title}>{t.ref}</Link>
                    <span> {t.title}</span>
                  </span>
                ))}
              </p>
            )}
          </li>
        )
      })}
    </ul>
  )
}

const SCENARIO: [keyof Sheet["quality"][number], string][] = [
  ["source", "Source"], ["stimulus", "Stimulus"], ["artifact", "Artifact"], ["environment", "Environment"], ["response", "Response"],
]

// The requirements, read as one sheet from the problem down to the tests, with what is related to each requirement in
// its own row. Every id links to its page; every row has an anchor, so a link can point at it.
export function RequirementsSheet({ sheet }: { sheet: Sheet }) {
  const empty = !sheet.problems.length && !sheet.requests.length && !sheet.functional.length && !sheet.quality.length
  if (empty) {
    return (
      <EmptyState>
        No requirements are written yet. Start in <span className="font-mono">/vbench:discovery</span>, then{" "}
        <span className="font-mono">/vbench:v-1-requirements</span>.
      </EmptyState>
    )
  }
  return (
    <div className="space-y-10">
      <nav aria-label="On this sheet" className="flex flex-wrap gap-2">
        {[["problems", `Problems ${sheet.problems.length}`], ["requests", `Requests ${sheet.requests.length}`], ["functional", `Functional ${sheet.functional.length}`], ["quality", `Quality ${sheet.quality.length}`]].map(([id, label]) => (
          <a key={id} href={`#${id}`} className="inline-flex min-h-9 items-center rounded-full bg-hover px-3.5 text-[13px] font-medium text-ink-2 no-underline hover:text-ink">{label}</a>
        ))}
      </nav>

      <Section id="problems" title="Problems" count={sheet.problems.length} hint="What people struggle with, from their side, with no solution in it. A request says which problem it addresses.">
        {sheet.problems.length ? (
          <Card className="overflow-hidden">
            <Table aria-label="Problems">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-44">Id</TableHead><TableHead className="min-w-72">Problem</TableHead><TableHead className="min-w-36">Who is affected</TableHead>
                  <TableHead className="min-w-56">Cost of leaving it</TableHead><TableHead>Addressed by</TableHead><TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sheet.problems.map((p, i) => (
                  <TableRow key={p.id || i} id={p.id || undefined} className="scroll-mt-32">
                    <TableCell>{p.id ? <Id id={p.id} /> : <span className="text-subtle">No id</span>}</TableCell>
                    <TableCell className="font-medium">{p.id ? <Text id={p.id}>{p.text}</Text> : <span className="text-ink">{p.text}</span>}</TableCell>
                    <TableCell>{p.who || <span className="text-subtle">Not said</span>}</TableCell>
                    <TableCell>{p.cost || <span className="text-subtle">Not said</span>}</TableCell>
                    <TableCell>
                      {p.requests.length ? (
                        <span className="flex flex-wrap gap-x-2">{p.requests.map((r) => <a key={r} href={`#${r}`} className="font-mono text-xs">{r}</a>)}</span>
                      ) : <span className="text-subtle">None</span>}
                    </TableCell>
                    <TableCell>{p.label ? <Badge tone={p.status}>{p.label}</Badge> : null}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        ) : (
          <EmptyState>No problems are written yet. They are section 0 of the requirements doc.</EmptyState>
        )}
      </Section>

      <Section id="requests" title="Requests" count={sheet.requests.length} hint="What was asked for, in the stakeholder's words, and the requirements it became.">
        <Card className="overflow-hidden">
          <Table aria-label="Requests">
            <TableHeader><TableRow><TableHead className="w-44">Id</TableHead><TableHead>The ask</TableHead><TableHead>Raised by</TableHead><TableHead>Problem</TableHead><TableHead>Became</TableHead></TableRow></TableHeader>
            <TableBody>
              {sheet.requests.map((r) => (
                <TableRow key={r.id} id={r.id} className="scroll-mt-32">
                  <TableCell><Id id={r.id} /></TableCell>
                  <TableCell><Text id={r.id}>{r.text}</Text></TableCell>
                  <TableCell className="whitespace-nowrap font-mono text-xs">{r.raisedBy || "—"}</TableCell>
                  <TableCell>
                    {r.problems.length ? (
                      <span className="flex flex-wrap gap-x-2">{r.problems.map((x) => <a key={x} href={`#${x}`} className="whitespace-nowrap font-mono text-xs">{x}</a>)}</span>
                    ) : <span className="text-subtle">None named</span>}
                  </TableCell>
                  <TableCell>
                    {r.requirements.length ? (
                      <span className="flex flex-wrap gap-x-2">{r.requirements.map((x) => <a key={x} href={`#${x}`} className="font-mono text-xs">{x}</a>)}</span>
                    ) : <span className="text-subtle">Nothing yet</span>}
                  </TableCell>
                </TableRow>
              ))}
              {!sheet.requests.length && <TableRow><TableCell colSpan={7} className="text-subtle">No requests recorded.</TableCell></TableRow>}
            </TableBody>
          </Table>
        </Card>
      </Section>

      <Section id="functional" title="Functional requirements" count={sheet.functional.length} hint="What the system does. Each has a user story (why), the use cases that realise it, and the criteria that say it is done.">
        <Card className="overflow-hidden">
          <Table aria-label="Functional requirements">
            <TableHeader>
              <TableRow>
                <TableHead className="w-44">Id</TableHead><TableHead className="min-w-64">Requirement and story</TableHead><TableHead className="min-w-40">Realised by</TableHead>
                <TableHead className="min-w-96">Acceptance criteria and tests</TableHead><TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sheet.functional.map((f) => (
                <TableRow key={f.id} id={f.id} className="scroll-mt-32">
                  <TableCell><Id id={f.id} /></TableCell>
                  <TableCell>
                    <p className="font-medium"><Text id={f.id}>{f.text}</Text></p>
                    {f.story && <p className="mt-1 text-muted-foreground">{f.story}</p>}
                  </TableCell>
                  <TableCell><UseCases ucs={f.ucs} /></TableCell>
                  <TableCell><Criteria criteria={f.criteria} /></TableCell>
                  <TableCell><Badge tone={f.status}>{f.label}</Badge></TableCell>
                </TableRow>
              ))}
              {!sheet.functional.length && <TableRow><TableCell colSpan={7} className="text-subtle">No functional requirements recorded.</TableCell></TableRow>}
            </TableBody>
          </Table>
        </Card>
      </Section>

      <Section id="quality" title="Quality requirements" count={sheet.quality.length} hint="How well it does it, as a six-part scenario whose response measure can be checked.">
        <Card className="overflow-hidden">
          <Table aria-label="Quality requirements">
            <TableHeader>
              <TableRow>
                <TableHead className="w-44">Id</TableHead><TableHead className="min-w-44">Quality</TableHead><TableHead className="min-w-96">Scenario</TableHead>
                <TableHead className="min-w-80">Acceptance criteria and tests</TableHead><TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sheet.quality.map((q) => (
                <TableRow key={q.id} id={q.id} className="scroll-mt-32">
                  <TableCell><Id id={q.id} /></TableCell>
                  <TableCell>
                    <p className="font-medium"><Text id={q.id}>{q.quality}</Text></p>
                    {q.outline && <p className="mt-1 text-muted-foreground">{q.outline}</p>}
                  </TableCell>
                  <TableCell>
                    <dl className="grid grid-cols-[6.5rem_1fr] gap-x-3 gap-y-1">
                      {SCENARIO.filter(([k]) => q[k]).map(([k, word]) => (
                        <div key={k} className="contents"><dt className="text-muted-foreground">{word}</dt><dd className="text-ink-2">{q[k] as string}</dd></div>
                      ))}
                      {q.measure && <div className="contents"><dt className="font-semibold text-ink">Measure</dt><dd className="font-semibold text-ink">{q.measure}</dd></div>}
                    </dl>
                  </TableCell>
                  <TableCell><Criteria criteria={q.criteria} /></TableCell>
                  <TableCell><Badge tone={q.status}>{q.label}</Badge></TableCell>
                </TableRow>
              ))}
              {!sheet.quality.length && <TableRow><TableCell colSpan={7} className="text-subtle">No quality requirements recorded.</TableCell></TableRow>}
            </TableBody>
          </Table>
        </Card>
      </Section>
    </div>
  )
}
