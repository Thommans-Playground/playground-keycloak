import { Link, useParams, useSearchParams } from "react-router-dom"
import { BookOpen, GitBranch, Layers, ListChecks, ListTodo, Route, Shapes, X } from "lucide-react"

import { useProject } from "@/components/AppShell"
import { CopyCommand } from "@/components/CopyCommand"
import { Lifecycle } from "@/components/Lifecycle"
import { Markdown } from "@/components/Markdown"
import { EmptyState, PageHeader } from "@/components/PageHeader"
import { Cell, RecordFrame, RecordHeader, RecordSection, RelatedTable, Row, StateChip, StatusChip, idLink, muted } from "@/components/Record"
import type { SpySection } from "@/components/Scrollspy"
import { PlantUml } from "@/components/PlantUml"
import { RecordFor } from "@/components/records"
import { CriterionPane, UseCasePane } from "@/components/records/InlinePanes"
import { StageChip } from "@/components/StageChip"
import { VDiagram } from "@/components/VDiagram"
import { ActionsMenu } from "@/components/ActionsMenu"
import { Visualise } from "@/components/Visualise"
import { TraceFlow } from "@/components/flow/TraceFlow"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { getFile, useText } from "@/lib/api"
import { useCaseSwitch } from "@/lib/crumbs"
import { lineageCrumbs, nodeOfUseCase } from "@/lib/lineage"
import type { ProjectState, UseCase } from "@/lib/types"
import { phaseOf, tone } from "@/lib/v"
import { cn } from "@/lib/utils"

function Neighbours({ project, ids, label, empty, openId, onOpen }: { project: ProjectState; ids: string[]; label: string; empty: string; openId: string | null; onOpen: (id: string) => void }) {
  return (
    <RelatedTable label={label} empty={empty} columns={[{ name: "Id", className: "w-44" }, { name: "Use case" }, { name: "Stage" }]}>
      {ids.map((id) => {
        const other: UseCase | undefined = project.useCases.find((x) => x.id === id)
        return (
          <Row key={id} className={cn(other && "cursor-pointer", id === openId && "bg-hover")} onClick={other ? () => onOpen(id) : undefined}>
            <Cell><OpenItem id={other ? id : undefined} active={id === openId} onOpen={onOpen} className={idLink}>{id}</OpenItem></Cell>
            <Cell className="font-medium text-ink">{other?.title ?? muted("No spec")}</Cell>
            <Cell>{other ? <StageChip stage={other.stage} /> : null}</Cell>
          </Row>
        )
      })}
    </RelatedTable>
  )
}

// An id that opens the item in the pane beside this use case, not on a page of its own. Where there is no item to show,
// it is plain text.
function OpenItem({ id, active, onOpen, children, className }: { id: string | undefined; active: boolean; onOpen: (id: string) => void; children: React.ReactNode; className?: string }) {
  if (!id) return <span className={className}>{children}</span>
  return (
    <button
      type="button" onClick={() => onOpen(id)} aria-current={active ? "true" : undefined}
      className={cn("text-left font-semibold text-link hover:underline", active && "text-ink underline", className)}
    >
      {children}
    </button>
  )
}

// One use case as a record: its header with the facts, then progress, criteria, tasks, order, diagrams, the V in context
// and the spec, in a column with a rail that follows the reader.
export default function UseCaseDetail() {
  const { id = "" } = useParams()
  const project = useProject()
  const u = project.useCases.find((x) => x.id === id)
  const [params, setParams] = useSearchParams()
  const spec = useText(u ? () => getFile(u.path) : null, u?.path ?? "")

  if (!u) {
    return (
      <>
        <PageHeader title="Use case not found" crumbs={[{ label: "Use cases", to: "/use-cases" }, { label: id }]} />
        <EmptyState>There is no spec for <span className="font-mono">{id}</span>. <Link to="/use-cases">Back to the use cases</Link>.</EmptyState>
      </>
    )
  }

  const criteria = project.criteria.filter((c) => c.uc === u.id)
  const tests = project.v.items.filter((i) => i.kind === "test")
  const tasks = project.v.items.filter((i) => i.kind === "task" && i.ucs.includes(u.id))
  const drawings = project.diagrams.filter((d) => d.uc === u.id)
  const realised = project.v.items.filter((i) => i.phase === "requirements" && (i.kind === "FR" || i.kind === "NFR") && i.ucs.includes(u.id)).map((i) => i.id)

  // The item open beside the page (`?open=<id>`): a task, a test or a diagram. Choosing another replaces it; the page
  // keeps its place, and Back steps through what was opened.
  const openId = params.get("open")
  const opened = openId ? project.v.items.find((i) => i.id === openId) : undefined
  const openedMeta = opened ? phaseOf(project, opened.phase) : undefined
  const show = (id: string) => setParams((prev) => { const next = new URLSearchParams(prev); next.set("open", id); return next })
  const close = () => setParams((prev) => { const next = new URLSearchParams(prev); next.delete("open"); return next })
  const openedCriterion = openId ? project.criteria.find((c) => c.id === openId) : undefined
  const openedUc = openId && openId !== u.id ? project.useCases.find((x) => x.id === openId) : undefined
  const isOpen = Boolean((opened && openedMeta) || openedCriterion || openedUc)
  const diagramItem = (path: string) => project.v.items.find((i) => i.file === path && i.kind.endsWith("diagram"))

  const sections: SpySection[] = [
    { id: "progress", label: "Progress", icon: Route },
    { id: "criteria", label: "Criteria", icon: ListChecks, badge: criteria.length },
    { id: "tasks", label: "Tasks", icon: ListTodo, badge: tasks.length },
    { id: "order", label: "Order", icon: GitBranch },
    { id: "diagrams", label: "Diagrams", icon: Shapes, badge: drawings.length },
    { id: "context", label: "In context", icon: Layers },
    { id: "spec", label: "Specification", icon: BookOpen },
  ]

  return (
    <>
      <PageHeader
        crumbs={(() => {
          const node = nodeOfUseCase(project, u.id)
          return (node && lineageCrumbs(project, node)) || [{ label: "Use cases", to: "/use-cases" }, { label: u.id, switch: useCaseSwitch(project, u.id) }]
        })()}
      />
      <div className={cn(isOpen && "grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]")}>
      <div className="min-w-0">
      <RecordFrame
        variant={isOpen ? "pane" : "page"} sections={sections}
        header={
          <RecordHeader
            overline="Use case" id={u.id} title={u.title}
            actions={<ActionsMenu target={{ kind: "usecase", id: u.id, realises: realised }} name={u.id} />}
            chips={<><StageChip stage={u.stage} />{u.blockedBy.length > 0 && <Badge tone="warn">Waiting for {u.blockedBy.join(", ")}</Badge>}</>}
            facts={[
              { label: "Actor", value: u.actor ?? "Not said" },
              { label: "Bounded context", value: u.context ?? "Unassigned" },
              { label: "Rigor", value: u.rigor },
              { label: "Wave", value: `${u.wave} · ${u.covered} of ${u.enforced} criteria covered` },
            ]}
          />
        }
      >
        <RecordSection id="progress" title="Progress" hint="Where it is on the V-cycle, and the one next step.">
          <Card>
            <CardContent className="space-y-4 py-5">
              <Lifecycle stage={u.stage} />
              <div className="border-t border-divider pt-4">
                <p className="t-footnote mb-2 text-muted-foreground">Next step for this use case</p>
                <CopyCommand command={u.next} primary />
              </div>
            </CardContent>
          </Card>
        </RecordSection>

        <RecordSection
          id="criteria" title="Acceptance criteria" count={criteria.length} hint={`${u.covered} of ${u.enforced} covered by a test. Each must hold for the use case to count as done.`}
        >
          <RelatedTable label="Acceptance criteria" empty="No criteria are written yet." columns={[{ name: "Criterion", className: "w-44" }, { name: "What must hold", className: "min-w-72" }, { name: "State" }, { name: "Proved by", className: "min-w-64" }]}>
            {criteria.map((c) => {
              const proof = tests.filter((t) => t.acs.includes(c.id))
              return (
                <Row key={c.id} className={cn("cursor-pointer", c.id === openId && "bg-hover")} onClick={() => show(c.id)}>
                  <Cell><OpenItem id={c.id} active={c.id === openId} onOpen={show} className={idLink}>{c.id}</OpenItem></Cell>
                  <Cell className="text-ink-2">{c.text || muted("No sentence written yet.")}</Cell>
                  <Cell><StateChip state={c.state} /></Cell>
                  <Cell>
                    {proof.length ? (
                      <ul className="space-y-1">
                        {proof.map((t) => (
                          <li key={t.id} onClick={(e) => e.stopPropagation()}><OpenItem id={t.id} active={t.id === openId} onOpen={show} className="whitespace-nowrap font-mono text-xs">{t.ref}</OpenItem> <span className="text-ink-2">{t.description}</span></li>
                        ))}
                      </ul>
                    ) : muted("None")}
                  </Cell>
                </Row>
              )
            })}
          </RelatedTable>
        </RecordSection>

        <RecordSection id="tasks" title="Delivery tasks" count={tasks.length} hint={`${u.tasksClosed} of ${u.tasks} closed. A task is closed once the criteria it names have tests.`}>
          <RelatedTable label="Delivery tasks" empty="No task is planned yet." columns={[{ name: "Id", className: "w-44" }, { name: "What it delivers", className: "min-w-72" }, { name: "Closes" }, { name: "Status" }]}>
            {tasks.map((t) => (
              <Row key={t.id} className={cn("cursor-pointer", t.id === openId && "bg-hover")} onClick={() => show(t.id)}>
                <Cell><OpenItem id={t.id} active={t.id === openId} onOpen={show} className={idLink}>{t.ref}</OpenItem></Cell>
                <Cell className="text-ink">{t.title}</Cell>
                <Cell className="font-mono text-xs">{t.acs.join(", ") || "—"}</Cell>
                <Cell><StatusChip status={tone(t.status)} label={t.label} /></Cell>
              </Row>
            ))}
          </RelatedTable>
        </RecordSection>

        <RecordSection id="order" title="Order" hint="What must be built first, and what waits for this.">
          <div className="space-y-4">
            <div><p className="t-footnote mb-1.5 font-semibold text-muted-foreground">Depends on</p><Neighbours project={project} ids={u.dependsOn} label="Depends on" empty="Nothing: it can start now." openId={openId} onOpen={show} /></div>
            <div><p className="t-footnote mb-1.5 font-semibold text-muted-foreground">Enables</p><Neighbours project={project} ids={u.enables} label="Enables" empty="Nothing waits for it." openId={openId} onOpen={show} /></div>
          </div>
        </RecordSection>

        <RecordSection id="diagrams" title="Diagrams" count={drawings.length} hint="Every diagram drawn for this use case, shown here.">
          <RelatedTable label="Diagrams" empty="None drawn yet." columns={[{ name: "Kind", className: "w-44" }, { name: "What it shows" }, { name: "File" }]}>
            {drawings.map((d) => (
              <Row key={d.path} className={cn(diagramItem(d.path) && "cursor-pointer", diagramItem(d.path)?.id === openId && "bg-hover")} onClick={() => { const it = diagramItem(d.path); if (it) show(it.id) }}>
                <Cell><Badge>{d.kind}</Badge></Cell>
                <Cell className="text-ink">{d.title || muted("No title line")}</Cell>
                <Cell><OpenItem id={diagramItem(d.path)?.id} active={diagramItem(d.path)?.id === openId} onOpen={show} className="font-mono text-xs [overflow-wrap:anywhere]">{d.path.split("/").pop()}</OpenItem></Cell>
              </Row>
            ))}
          </RelatedTable>
          <div className="mt-4 space-y-4">
            {drawings.map((d) => (
              <Card key={`drawn-${d.path}`}>
                <CardContent className="space-y-3 py-5">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <p className="text-[15px] font-semibold text-ink"><Badge>{d.kind}</Badge> <span className="ml-1.5">{d.title || muted("No title line")}</span></p>
                    <Link to={`/diagrams?path=${encodeURIComponent(d.path)}`} className="text-[13px]">Open on its own page</Link>
                  </div>
                  <PlantUml path={d.path} />
                </CardContent>
              </Card>
            ))}
          </div>
        </RecordSection>

        <RecordSection id="context" title="In context" hint="The pictures, when you want them.">
          <div className="grid grid-cols-[minmax(0,1fr)] gap-3">
            <Visualise name="v" title="its V-cycle" hint="everything this use case holds, phase by phase"><VDiagram project={project} mode={{ kind: "uc", uc: u.id }} /></Visualise>
            <Visualise name="trace" title="the trace to the tests" hint="requirement, use case, tasks, criteria, tests"><TraceFlow project={project} uc={u.id} /></Visualise>
          </div>
        </RecordSection>

        <RecordSection id="spec" title="Specification" hint={u.path}>
          <Card>
            <CardContent className="py-5">
              {spec.error ? <p className="text-sm text-muted-foreground">The spec could not be read: {spec.error}.</p>
                : spec.text === null ? <Skeleton className="h-48 w-full" /> : <Markdown source={spec.text} basePath={u.path} />}
            </CardContent>
          </Card>
        </RecordSection>
      </RecordFrame>
      </div>
      {isOpen && (
        <aside aria-label="Opened beside the use case" className="min-w-0 xl:sticky xl:top-28 xl:max-h-[calc(100vh-8.5rem)] xl:overflow-y-auto xl:pr-1">
          <div className="mb-3 flex items-center justify-between gap-3">
            <p className="t-footnote text-muted-foreground">Opened from this use case</p>
            <button type="button" onClick={close} className="inline-flex min-h-9 items-center gap-1.5 rounded-control border border-input bg-surface px-3 text-[13px] font-medium text-ink hover:bg-hover">
              <X className="size-4" aria-hidden="true" />Close
            </button>
          </div>
          {opened && openedMeta ? <RecordFor project={project} phase={opened.phase} meta={openedMeta} item={opened} variant="pane" />
            : openedCriterion ? <CriterionPane project={project} criterion={openedCriterion} show={show} />
            : openedUc ? <UseCasePane project={project} uc={openedUc} /> : null}
        </aside>
      )}
      </div>
    </>
  )
}
