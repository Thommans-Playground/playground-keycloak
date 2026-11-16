import { Link, useNavigate } from "react-router-dom"
import { ArrowRight, CheckCheck, ClipboardList, FlaskConical, ListTodo, ShieldCheck } from "lucide-react"

import { useProject } from "@/components/AppShell"
import { CopyCommand } from "@/components/CopyCommand"
import { EmptyState, PageHeader } from "@/components/PageHeader"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Ring } from "@/components/Ring"
import { StatCard } from "@/components/StatCard"
import { Visualise } from "@/components/Visualise"
import { CRITERION_ORDER, CRITERION_STATE } from "@/lib/status"
import { VDiagram } from "@/components/VDiagram"
import { STAGES } from "@/lib/stages"

const STAGE_COLOUR: Record<string, string> = {
  requirements: "var(--subtle)", design: "var(--muted)", code: "var(--warn)", rung: "var(--warn-text)", verify: "var(--ok)",
}
const CRITERIA_SLICES = CRITERION_ORDER.map((key) => ({ key, label: CRITERION_STATE[key].word, colour: CRITERION_STATE[key].colour }))

export default function Overview() {
  const project = useProject()
  const navigate = useNavigate()
  const { useCases, next, gates } = project
  const s = project.v.stats
  const tests = s.tests.unit + s.tests.integration + s.tests.system + s.tests.acceptance
  const built = useCases.filter((u) => u.stage === "verify").length

  return (
    <>
      <PageHeader
        title="Overview"
        description={
          useCases.length
            ? `${built} of ${useCases.length} use cases are built. The next step below follows the build order.`
            : "There are no use cases yet."
        }
      />

      <Card className="mb-6 shadow-[inset_0_3px_0_var(--charcoal),var(--e1)]">
        <CardHeader>
          <div>
            <CardTitle>Next step</CardTitle>
            <CardDescription className="mt-1">{next.why}</CardDescription>
            {next.purpose && (
              <p className="mt-2 text-[13px] text-ink-2">
                <span className="font-semibold text-ink">Why this step:</span> {next.purpose}
              </p>
            )}
          </div>
          {next.uc && (
            <Link to={`/use-cases/${next.uc}`} className="flex shrink-0 items-center gap-1 whitespace-nowrap text-[13px] font-medium">
              Open {next.uc} <ArrowRight className="size-3.5" aria-hidden="true" />
            </Link>
          )}
        </CardHeader>
        <CardContent>
          {next.command ? (
            <CopyCommand command={next.command} primary />
          ) : (
            <p className="text-sm text-ink-2">Nothing can proceed. Run <code className="font-mono">vbench check links</code> to see why.</p>
          )}
          {Object.keys(next.blocked).length > 0 && (
            <ul className="mt-4 space-y-1 text-[13px] text-muted-foreground">
              {Object.entries(next.blocked).map(([uc, waits]) => (
                <li key={uc}>
                  <span className="font-mono text-ink-2">{uc}</span> is waiting for <span className="font-mono text-ink-2">{waits.join(", ")}</span>.
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <section aria-labelledby="stats" className="mb-8">
        <h2 id="stats" className="mb-3 text-[19px] font-semibold text-ink">Statistics</h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <StatCard icon={CheckCheck} label="Use cases built" value={s.useCases.built} of={s.useCases.total} tone={s.useCases.built === s.useCases.total ? "ok" : "neutral"} to="/use-cases" sub="Open the list, filter by stage" />
          <StatCard icon={ShieldCheck} label="Criteria covered" value={s.criteria.covered} of={s.criteria.total} tone={s.criteria.covered === s.criteria.total ? "ok" : "warn"} to="/traceability?ac.f.state=uncovered" sub="by a marked test. Open the ones with no test yet" />
          <StatCard icon={ListTodo} label="Tasks closed" value={s.tasks.closed} of={s.tasks.total} tone={s.tasks.closed === s.tasks.total ? "ok" : "neutral"} to="/v/module-design?f.kind=task" sub="Open the task plan" />
          <StatCard icon={ClipboardList} label="Requirements realised" value={s.requirements.realised} of={s.requirements.total} tone={s.requirements.realised === s.requirements.total ? "ok" : "warn"} to="/v/requirements?f.status=warn" sub="by a use case. Open the ones with none" />
          <StatCard
            icon={FlaskConical} label="Tests on the V" value={tests} to="/v/unit" tone={s.tests.unplaced ? "warn" : "neutral"}
            sub={`unit ${s.tests.unit} · integration ${s.tests.integration} · system ${s.tests.system} · acceptance ${s.tests.acceptance}${s.tests.unplaced ? ` · ${s.tests.unplaced} not on a V` : ""}`}
          />
          <StatCard icon={ShieldCheck} label="Gates passing" value={s.gates.passing} of={s.gates.total} tone={s.gates.passing === s.gates.total ? "ok" : "risk"} sub={s.gates.passing === s.gates.total ? "Every gate is green" : "Open the failing gates below"} />
        </div>
      </section>

      <section aria-labelledby="progress" className="mb-8">
        <h2 id="progress" className="mb-3 text-[19px] font-semibold text-ink">Progress at a glance</h2>
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader><div><CardTitle>Where the use cases are</CardTitle><CardDescription className="mt-1">Press a slice to open those use cases.</CardDescription></div></CardHeader>
            <CardContent className="flex justify-center">
              <Ring
                slices={STAGES.map((st) => ({ key: st.key, label: st.label, value: useCases.filter((u) => u.stage === st.key).length, colour: STAGE_COLOUR[st.key] }))}
                centre={{ value: useCases.length, label: "use cases" }} description="How the use cases divide by stage"
                onSelect={(key) => key && navigate(`/use-cases?f.stage=${key}`)} size={150}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader><div><CardTitle>Acceptance criteria</CardTitle><CardDescription className="mt-1">Press a slice to open those criteria.</CardDescription></div></CardHeader>
            <CardContent className="flex justify-center">
              <Ring
                slices={CRITERIA_SLICES.map((c) => ({ ...c, value: project.criteria.filter((x) => x.state === c.key).length }))}
                centre={{ value: project.criteria.length, label: "criteria" }} description="How the acceptance criteria divide by state"
                onSelect={(key) => key && navigate(`/traceability?ac.f.state=${key}`)} size={150}
              />
            </CardContent>
          </Card>
        </div>
      </section>

      <section aria-labelledby="vglance" className="mb-8">
        <h2 id="vglance" className="sr-only">The V-cycle at a glance</h2>
        <Visualise name="v" title="the V-cycle at a glance" hint="specify down the left, build at the bottom, prove up the right">
          <VDiagram project={project} mode={{ kind: "summary" }} />
        </Visualise>
      </section>

      <section aria-labelledby="gates" className="mb-8">
        <h2 id="gates" className="mb-3 text-[19px] font-semibold text-ink">Gates</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {gates.map((g) => (
            <Card key={g.name}>
              <details>
                <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 px-4">
                  <span className="font-mono text-[13px] font-medium text-ink">{g.name}</span>
                  <Badge tone={g.ok ? "ok" : "risk"}>{g.ok ? "Passing" : "Failing"}</Badge>
                </summary>
                <pre className="max-h-56 overflow-auto whitespace-pre-wrap border-t border-divider px-4 py-3 font-mono text-xs text-ink-2">{g.lines.join("\n")}</pre>
              </details>
            </Card>
          ))}
        </div>
      </section>

      <section aria-labelledby="board">
        <h2 id="board" className="mb-3 text-[19px] font-semibold text-ink">Where each use case is</h2>
        {useCases.length === 0 ? (
          <EmptyState action={next.command ? <CopyCommand command={next.command} primary /> : undefined}>
            Start from a requirement. Run the command below in Claude Code to create the first use case.
          </EmptyState>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {STAGES.map((s) => {
              const here = useCases.filter((u) => u.stage === s.key)
              return (
                <div key={s.key} className="rounded-card bg-hover/60 p-3">
                  <div className="mb-2 flex items-center justify-between px-1">
                    <h3 className="text-[13px] font-semibold text-ink">{s.step}</h3>
                    <span className="rounded-full bg-surface px-2 text-xs font-semibold text-muted-foreground">{here.length}</span>
                  </div>
                  <div className="space-y-2">
                    {here.length === 0 && <p className="px-1 py-3 text-xs text-subtle">None here.</p>}
                    {here.map((u) => (
                      <Link key={u.id} to={`/use-cases/${u.id}`} className="block no-underline">
                        <Card interactive className="px-3 py-3">
                          <p className="font-mono text-xs text-muted-foreground">{u.id}</p>
                          <p className="mt-0.5 text-[13px] font-semibold text-ink">{u.title}</p>
                          <div className="mt-2 flex flex-wrap items-center gap-1.5">
                            <span className="text-xs text-muted-foreground">Wave {u.wave}</span>
                            {u.blockedBy.length > 0 && <Badge tone="warn">Waiting for {u.blockedBy.join(", ")}</Badge>}
                          </div>
                        </Card>
                      </Link>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </section>
    </>
  )
}
