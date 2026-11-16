import { Link } from "react-router-dom"
import { BookOpen, FileText, GitCompare, Layers, ListChecks, Shapes } from "lucide-react"

import { Cell, IdLink, RecordFrame, RecordHeader, RecordSection, RelatedTable, Row, StateChip, StatusChip, muted, type Variant } from "@/components/Record"
import type { SpySection } from "@/components/Scrollspy"
import { StageChip } from "@/components/StageChip"
import { VDiagram } from "@/components/VDiagram"
import { Visualise } from "@/components/Visualise"
import type { ProjectState, VItem, VPhase } from "@/lib/types"
import { itemPath, itemsOfUc, tone } from "@/lib/v"
import { cn } from "@/lib/utils"

// Kinds whose name comes from the repo (a file, a function, a diagram) rather than being a sentence.
const NAMED = new Set(["test", "code", "sequence diagram", "class diagram", "state diagram"])
const word = (kind: string) => kind.charAt(0).toUpperCase() + kind.slice(1)

// Any item that is not a requirement (code, a test, a diagram, a task, a context, a domain model), as a record: what it
// is, how it relates to the use cases and to the item it is paired with, and where it lives.
export function ItemRecord({ project, phase, meta, found, variant }: { project: ProjectState; phase: string; meta: VPhase; found: VItem; variant: Variant }) {
  const partner = project.v.phases.find((p) => p.key === meta.pairs)
  const paired = (meta.arm === "vertex"
    ? found.ucs.flatMap((u) => itemsOfUc(project, u).filter((i) => i.kind === "test"))
    : partner ? found.ucs.flatMap((u) => itemsOfUc(project, u).filter((i) => i.phase === partner.key)) : [])
    .filter((i, n, all) => all.findIndex((x) => x.id === i.id) === n)
  const pairedTitle = meta.arm === "vertex" ? "Tests that verify it" : partner ? `${meta.arm === "left" ? "Proved by" : "Proves"} ${partner.label.toLowerCase()}` : "Paired with"
  const criteria = project.criteria.filter((c) => found.acs.includes(c.id))
  const ucs = found.ucs.map((u) => project.useCases.find((x) => x.id === u)).filter((u): u is NonNullable<typeof u> => Boolean(u))
  const location = found.file ? `${found.file}${found.line ? `:${found.line}` : ""}` : ""
  const target = !found.file ? null
    : found.file.endsWith(".puml") ? { to: `/diagrams?path=${encodeURIComponent(found.file)}`, how: "Open the diagram" }
    : found.file.endsWith(".md") ? { to: `/docs?path=${encodeURIComponent(found.file)}`, how: "Read the document" } : null

  const header = (
    <RecordHeader
      overline={word(found.kind)} id={found.ref}
      title={<span className={cn(NAMED.has(found.kind) && "font-mono text-xl")}>{found.title}</span>}
      description={found.description}
      chips={<StatusChip status={found.status} label={found.label} />}
      actions={variant === "pane" ? <Link to={itemPath(found)} className="t-footnote font-medium">Open as a page</Link> : undefined}
      facts={[
        { label: "Phase", value: <Link to={`/v/${found.phase === "unplaced" ? phase : found.phase}`} className="font-medium">{meta.label}</Link> },
        { label: "Use cases", value: found.ucs.length ? found.ucs.map((u) => <Link key={u} to={`/use-cases/${u}`} className="mr-2 font-mono text-xs">{u}</Link>) : "None" },
        { label: "Criteria", value: found.acs.length ? found.acs.length : "None" },
        { label: "Location", value: location ? <span className="font-mono text-xs">{location}</span> : "—" },
      ]}
    />
  )

  const sections: SpySection[] = [
    { id: "usecases", label: "Use cases", icon: Layers, badge: ucs.length },
    { id: "paired", label: pairedTitle, icon: GitCompare, badge: paired.length },
    ...(found.acs.length ? [{ id: "criteria", label: "Criteria", icon: ListChecks, badge: criteria.length }] : []),
    { id: "where", label: "Where it is", icon: BookOpen },
    { id: "context", label: "In context", icon: Shapes },
  ]

  return (
    <RecordFrame variant={variant} sections={sections} header={header}>
      <RecordSection id="usecases" title="Use cases" count={ucs.length} hint="The use cases this belongs to.">
        <RelatedTable label="Use cases" empty="No use case names it, so it is not on any V yet." columns={[{ name: "Id", className: "w-44" }, { name: "Use case" }, { name: "Stage" }, { name: "Next step" }]}>
          {ucs.map((u) => (
            <Row key={u.id}>
              <Cell><IdLink to={`/use-cases/${u.id}`}>{u.id}</IdLink></Cell>
              <Cell className="font-medium text-ink">{u.title}</Cell>
              <Cell><StageChip stage={u.stage} /></Cell>
              <Cell className="font-mono text-xs">{u.next}</Cell>
            </Row>
          ))}
        </RelatedTable>
      </RecordSection>

      <RecordSection id="paired" title={pairedTitle} count={paired.length} hint="The item on the other side of the V, so each thing specified has what proves it.">
        <RelatedTable label={pairedTitle} empty="Nothing is recorded on the other side yet." columns={[{ name: "Id", className: "w-44" }, { name: "What it is" }, { name: "Status" }]}>
          {paired.map((i) => (
            <Row key={i.id}>
              <Cell><IdLink to={itemPath(i)}>{i.ref}</IdLink></Cell>
              <Cell>
                <p className="text-ink">{i.description || i.title}</p>
                {i.description && <p className={cn("text-xs text-muted-foreground [overflow-wrap:anywhere]", NAMED.has(i.kind) && "font-mono")}>{i.title}</p>}
              </Cell>
              <Cell><StatusChip status={tone(i.status)} label={i.label} /></Cell>
            </Row>
          ))}
        </RelatedTable>
      </RecordSection>

      {found.acs.length > 0 && (
        <RecordSection id="criteria" title="Acceptance criteria" count={criteria.length} hint="The criteria it closes or proves.">
          <RelatedTable label="Acceptance criteria" empty="They are not in a spec." columns={[{ name: "Criterion", className: "w-44" }, { name: "What must hold", className: "min-w-72" }, { name: "State" }]}>
            {criteria.map((c) => (
              <Row key={c.id}>
                <Cell>{c.uc ? <IdLink to={`/use-cases/${c.uc}#criteria`}>{c.id}</IdLink> : <span className="font-mono text-[13px] font-semibold">{c.id}</span>}</Cell>
                <Cell className="text-ink-2">{c.text || muted("No sentence written yet.")}</Cell>
                <Cell><StateChip state={c.state} /></Cell>
              </Row>
            ))}
          </RelatedTable>
        </RecordSection>
      )}

      <RecordSection id="where" title="Where it is" hint="Its place in the repository.">
        <RelatedTable label="Where it is" columns={[{ name: "Part", className: "w-44" }, { name: "Location" }]}>
          <Row><Cell className="text-muted-foreground">Id in the registry</Cell><Cell className="font-mono text-xs font-semibold text-ink">{found.ref}</Cell></Row>
          <Row><Cell className="text-muted-foreground">Name</Cell><Cell className="font-mono text-xs [overflow-wrap:anywhere]">{found.title}</Cell></Row>
          <Row>
            <Cell className="text-muted-foreground">File</Cell>
            <Cell>{location ? <span className="font-mono text-xs [overflow-wrap:anywhere]">{location}</span> : muted("Not drawn or written yet")}{target && <>{"  "}<Link to={target.to} className="text-[13px]"><FileText className="mr-1 inline size-3.5" aria-hidden="true" />{target.how}</Link></>}</Cell>
          </Row>
        </RelatedTable>
      </RecordSection>

      <RecordSection id="context" title="In context" hint="The V of each use case, with this item outlined.">
        {found.ucs.length === 0 ? (
          <p className="text-sm text-muted-foreground">Add <span className="font-mono">Verifies UC-… · unit rung.</span> to a test, or <span className="font-mono">Realises UC-…</span> to code, to place it on a V.</p>
        ) : (
          <div className="grid grid-cols-[minmax(0,1fr)] gap-3">
            {found.ucs.map((u) => (
              <Visualise key={u} name={`v-${u}`} title={`the V of ${u}`} hint={project.useCases.find((x) => x.id === u)?.title}>
                <VDiagram project={project} mode={{ kind: "uc", uc: u }} highlight={{ phase: found.phase === "unplaced" ? phase : found.phase, id: found.id }} />
              </Visualise>
            ))}
          </div>
        )}
      </RecordSection>
    </RecordFrame>
  )
}
