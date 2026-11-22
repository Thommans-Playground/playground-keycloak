import { Link } from "react-router-dom"
import { BookOpen, ClipboardList, FlaskConical, GitBranch, Layers, ListChecks, Quote, Target } from "lucide-react"

import { EmptyState } from "@/components/PageHeader"
import { Cell, IdLink, RecordFrame, RecordHeader, RecordSection, RelatedTable, Row, StateChip, StatusChip, muted, type Variant } from "@/components/Record"
import type { SpySection } from "@/components/Scrollspy"
import { StageChip } from "@/components/StageChip"
import { becameOf, findRequirement, originOf, testsOf, type Requirement } from "@/lib/records"
import type { ProjectState, SheetCriterion, SheetFunctional, SheetProblem, SheetQuality, SheetRequest, SheetTest } from "@/lib/types"

const to = (id: string) => `/v/requirements/${encodeURIComponent(id)}`
const KIND = { problem: "Problem", request: "Request", functional: "Functional requirement", quality: "Quality requirement" } as const

function Problems({ list }: { list: SheetProblem[] }) {
  return (
    <RelatedTable label="Problems" empty="No problem is named." columns={[{ name: "Id", className: "w-44" }, { name: "Problem" }, { name: "Who is affected" }, { name: "Cost of leaving it" }]}>
      {list.map((p) => (
        <Row key={p.id}>
          <Cell><IdLink to={to(p.id)}>{p.id}</IdLink></Cell>
          <Cell className="font-medium text-ink">{p.text}</Cell><Cell>{p.who}</Cell><Cell>{p.cost}</Cell>
        </Row>
      ))}
    </RelatedTable>
  )
}

function Requests({ list }: { list: SheetRequest[] }) {
  return (
    <RelatedTable label="Requests" empty="No request yet." columns={[{ name: "Id", className: "w-44" }, { name: "The ask" }, { name: "Raised by" }, { name: "Problem" }]}>
      {list.map((r) => (
        <Row key={r.id}>
          <Cell><IdLink to={to(r.id)}>{r.id}</IdLink></Cell>
          <Cell className="text-ink">{r.text}</Cell>
          <Cell className="whitespace-nowrap font-mono text-xs">{r.raisedBy || "—"}</Cell>
          <Cell>{r.problems.length ? r.problems.map((p) => <Link key={p} to={to(p)} className="mr-2 whitespace-nowrap font-mono text-xs">{p}</Link>) : muted("None named")}</Cell>
        </Row>
      ))}
    </RelatedTable>
  )
}

function Requirements({ list }: { list: (SheetFunctional | SheetQuality)[] }) {
  return (
    <RelatedTable label="Requirements" empty="Nothing has been derived from it yet." columns={[{ name: "Id", className: "w-44" }, { name: "Requirement" }, { name: "Status" }]}>
      {list.map((r) => (
        <Row key={r.id}>
          <Cell><IdLink to={to(r.id)}>{r.id}</IdLink></Cell>
          <Cell className="text-ink">{"text" in r ? r.text : <><span className="font-medium">{r.quality}</span>{r.measure ? `: ${r.measure}` : ""}</>}</Cell>
          <Cell><StatusChip status={r.status} label={r.label} /></Cell>
        </Row>
      ))}
    </RelatedTable>
  )
}

function UseCases({ project, ids }: { project: ProjectState; ids: { id: string; title: string }[] }) {
  return (
    <RelatedTable label="Use cases" empty="No use case realises it yet." columns={[{ name: "Id", className: "w-44" }, { name: "Use case" }, { name: "Stage" }, { name: "Next step" }]}>
      {ids.map((u) => {
        const full = project.useCases.find((x) => x.id === u.id)
        return (
          <Row key={u.id}>
            <Cell><IdLink to={`/use-cases/${u.id}`}>{u.id}</IdLink></Cell>
            <Cell className="font-medium text-ink">{u.title}</Cell>
            <Cell>{full ? <StageChip stage={full.stage} /> : null}</Cell>
            <Cell className="font-mono text-xs">{full?.next}</Cell>
          </Row>
        )
      })}
    </RelatedTable>
  )
}

function Proof({ tests }: { tests: SheetTest[] }) {
  if (!tests.length) return muted("None")
  return (
    <ul className="space-y-1">
      {tests.map((t) => (
        <li key={t.id}>
          <Link to={`/v/${t.phase}/${encodeURIComponent(t.id)}`} className="whitespace-nowrap font-mono text-xs font-semibold">{t.ref}</Link> <span className="text-ink-2">{t.title}</span>
        </li>
      ))}
    </ul>
  )
}

function Criteria({ list }: { list: SheetCriterion[] }) {
  return (
    <RelatedTable label="Acceptance criteria" empty="No criterion is written yet; they are written in the use case's spec." columns={[{ name: "Criterion", className: "w-44" }, { name: "What must hold", className: "min-w-72" }, { name: "State" }, { name: "Proved by", className: "min-w-64" }]}>
      {list.map((c) => (
        <Row key={c.id}>
          <Cell>{c.uc ? <IdLink to={`/use-cases/${c.uc}#criteria`}>{c.id}</IdLink> : <span className="font-mono text-[13px] font-semibold text-ink">{c.id}</span>}</Cell>
          <Cell className="text-ink-2">{c.text || muted("No sentence written yet.")}</Cell>
          <Cell><StateChip state={c.state} /></Cell>
          <Cell><Proof tests={c.tests} /></Cell>
        </Row>
      ))}
    </RelatedTable>
  )
}

function Tests({ criteria }: { criteria: SheetCriterion[] }) {
  const tests = testsOf(criteria)
  return (
    <RelatedTable label="Tests" empty="No test proves it yet." columns={[{ name: "Id", className: "w-44" }, { name: "What it checks" }, { name: "Level" }, { name: "Proves" }]}>
      {tests.map((t) => (
        <Row key={t.id}>
          <Cell><IdLink to={`/v/${t.phase}/${encodeURIComponent(t.id)}`}>{t.ref}</IdLink></Cell>
          <Cell className="text-ink">{t.title}</Cell>
          <Cell className="capitalize">{t.phase}</Cell>
          <Cell className="font-mono text-xs">{t.proves.join(", ")}</Cell>
        </Row>
      ))}
    </RelatedTable>
  )
}

function Scenario({ q }: { q: SheetQuality }) {
  const parts: [string, string][] = [["Source", q.source], ["Stimulus", q.stimulus], ["Artifact", q.artifact], ["Environment", q.environment], ["Response", q.response], ["Response measure", q.measure]]
  return (
    <RelatedTable label="Scenario" empty="No scenario is written yet." columns={[{ name: "Part", className: "w-44" }, { name: "In this requirement" }]}>
      {parts.filter(([, v]) => v).map(([k, v]) => (
        <Row key={k}><Cell className={k === "Response measure" ? "font-semibold text-ink" : "text-muted-foreground"}>{k}</Cell><Cell className={k === "Response measure" ? "font-semibold text-ink" : "text-ink"}>{v}</Cell></Row>
      ))}
    </RelatedTable>
  )
}

function Where({ file }: { file: string | null | undefined }) {
  return (
    <RelatedTable label="Where it is written" columns={[{ name: "Part", className: "w-44" }, { name: "Location" }]}>
      <Row>
        <Cell className="text-muted-foreground">Document</Cell>
        <Cell>{file ? <Link to={`/docs?path=${encodeURIComponent(file)}`} className="font-mono text-xs">{file}</Link> : muted("Not found")}</Cell>
      </Row>
    </RelatedTable>
  )
}

// A problem, request or requirement as a record: where it came from, what it says, what realises it and what proves it.
export function RequirementRecord({ project, id, variant }: { project: ProjectState; id: string; variant: Variant }) {
  const sheet = project.requirements
  const req: Requirement | null = findRequirement(sheet, id)
  if (!req) return <EmptyState>That requirement is not in the requirements doc any more.</EmptyState>
  const file = project.v.items.find((i) => i.id === id && i.phase === "requirements")?.file
  const open = () => (
    <div className="flex items-center gap-2">
      {variant === "pane" && <Link to={to(id)} className="t-footnote font-medium">Open as a page</Link>}
    </div>
  )
  const docLink = file ? <Link to={`/docs?path=${encodeURIComponent(file)}`} className="font-mono text-xs">{file.split("/").pop()}</Link> : "—"

  let header, sections: SpySection[], body
  if (req.kind === "problem") {
    const p = req.problem
    const became = becameOf(sheet, req)
    const requests = sheet.requests.filter((r) => p.requests.includes(r.id))
    header = <RecordHeader overline={KIND.problem} id={p.id || undefined} title={p.text} chips={<StatusChip status={p.status} label={p.label} />} actions={open()}
      facts={[{ label: "Who is affected", value: p.who || "Not said" }, { label: "Cost of leaving it", value: p.cost || "Not said" }, { label: "Requests", value: requests.length }, { label: "Requirements", value: became.length }]} />
    sections = [{ id: "requests", label: "Requests", icon: Quote, badge: requests.length }, { id: "became", label: "Requirements", icon: ClipboardList, badge: became.length }, { id: "where", label: "Where it is written", icon: BookOpen }]
    body = (
      <>
        <RecordSection id="requests" title="Requests" count={requests.length} hint="What was asked for, in the stakeholder's words, to solve it."><Requests list={requests} /></RecordSection>
        <RecordSection id="became" title="Requirements" count={became.length} hint="What those requests became."><Requirements list={became} /></RecordSection>
        <RecordSection id="where" title="Where it is written"><Where file={file} /></RecordSection>
      </>
    )
  } else if (req.kind === "request") {
    const r = req.request
    const problems = sheet.problems.filter((p) => r.problems.includes(p.id))
    const became = becameOf(sheet, req)
    header = <RecordHeader overline={KIND.request} id={r.id} title={`“${r.text}”`} actions={open()}
      facts={[{ label: "Raised by", value: r.raisedBy || "—" }, { label: "Problems", value: problems.length }, { label: "Requirements", value: became.length }, { label: "Written in", value: docLink }]} />
    sections = [{ id: "problems", label: "Problems", icon: Target, badge: problems.length }, { id: "became", label: "Requirements", icon: ClipboardList, badge: became.length }, { id: "where", label: "Where it is written", icon: BookOpen }]
    body = (
      <>
        <RecordSection id="problems" title="Problems" count={problems.length} hint="What this request is meant to solve."><Problems list={problems} /></RecordSection>
        <RecordSection id="became" title="Requirements" count={became.length} hint="What the request became."><Requirements list={became} /></RecordSection>
        <RecordSection id="where" title="Where it is written"><Where file={file} /></RecordSection>
      </>
    )
  } else {
    const r = req.kind === "functional" ? req.fr : req.nfr
    const fr = req.kind === "functional" ? req.fr : null
    const nfr = req.kind === "quality" ? req.nfr : null
    const { requests, problems } = originOf(sheet, id)
    const covered = r.criteria.filter((c) => c.state === "covered").length
    const tests = testsOf(r.criteria)
    header = (
      <RecordHeader
        overline={KIND[req.kind]} id={id} title={fr ? fr.text : `${nfr!.quality}${nfr!.outline ? `: ${nfr!.outline}` : ""}`}
        description={fr?.story} chips={<StatusChip status={r.status} label={r.label} />} actions={open()}
        facts={[
          { label: "Realised by", value: `${r.ucs.length} use case${r.ucs.length === 1 ? "" : "s"}` },
          { label: "Criteria covered", value: `${covered} of ${r.criteria.length}` },
          { label: "Tests", value: tests.length },
          { label: "Written in", value: docLink },
        ]}
      />
    )
    sections = [
      { id: "origin", label: "Where it came from", icon: GitBranch, badge: requests.length + problems.length },
      { id: "statement", label: nfr ? "Scenario" : "Statement", icon: Quote },
      { id: "usecases", label: "Use cases", icon: Layers, badge: r.ucs.length },
      { id: "criteria", label: "Criteria", icon: ListChecks, badge: r.criteria.length },
      { id: "tests", label: "Tests", icon: FlaskConical, badge: tests.length },
    ]
    body = (
      <>
        <RecordSection id="origin" title="Where it came from" hint="The problem, then the request that asked for it.">
          <div className="space-y-4"><Problems list={problems} /><Requests list={requests} /></div>
        </RecordSection>
        <RecordSection id="statement" title={nfr ? "Scenario" : "Statement"} hint={nfr ? "Six parts; the response measure is what a test or a measurement checks." : "What the system shall do, and why."}>
          {nfr ? <Scenario q={nfr} /> : (
            <RelatedTable label="Statement" columns={[{ name: "Part", className: "w-44" }, { name: "In this requirement" }]}>
              <Row><Cell className="text-muted-foreground">Requirement</Cell><Cell className="font-medium text-ink">{fr!.text}</Cell></Row>
              <Row><Cell className="text-muted-foreground">User story</Cell><Cell className="text-ink">{fr!.story || muted("No story written yet.")}</Cell></Row>
              <Row><Cell className="text-muted-foreground">Satisfies</Cell><Cell>{fr!.satisfies.length ? fr!.satisfies.map((s) => <Link key={s} to={to(s)} className="mr-2 whitespace-nowrap font-mono text-xs">{s}</Link>) : muted("No request named")}</Cell></Row>
            </RelatedTable>
          )}
        </RecordSection>
        <RecordSection id="usecases" title="Use cases" count={r.ucs.length} hint="What realises it."><UseCases project={project} ids={r.ucs} /></RecordSection>
        <RecordSection id="criteria" title="Acceptance criteria" count={r.criteria.length} hint="What must hold for it to count as done."><Criteria list={r.criteria} /></RecordSection>
        <RecordSection id="tests" title="Tests" count={tests.length} hint="What proves the criteria."><Tests criteria={r.criteria} /></RecordSection>
      </>
    )
  }
  return <RecordFrame variant={variant} sections={sections} header={header}>{body}</RecordFrame>
}

