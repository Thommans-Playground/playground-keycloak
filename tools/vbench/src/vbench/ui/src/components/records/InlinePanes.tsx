import { Link } from "react-router-dom"

import { CopyCommand } from "@/components/CopyCommand"
import { Cell, RecordHeader, RecordSection, RelatedTable, Row, StateChip, muted } from "@/components/Record"
import { StageChip } from "@/components/StageChip"
import type { Criterion, ProjectState, UseCase } from "@/lib/types"
import { itemPath } from "@/lib/v"

// An acceptance criterion in full: its sentence, the requirements it satisfies, the tests that prove it and the tasks it closes.
export function CriterionPane({ project, criterion, show }: { project: ProjectState; criterion: Criterion; show: (id: string) => void }) {
  const proof = project.v.items.filter((i) => i.kind === "test" && i.acs.includes(criterion.id))
  const tasks = project.v.items.filter((i) => i.kind === "task" && i.acs.includes(criterion.id))
  return (
    <div className="space-y-8">
      <RecordHeader
        overline="Acceptance criterion" id={criterion.id} title={criterion.text || "No sentence written yet."}
        chips={<StateChip state={criterion.state} />}
        facts={[
          { label: "Use case", value: criterion.uc ? <Link to={`/use-cases/${criterion.uc}`} className="font-mono text-xs">{criterion.uc}</Link> : "None" },
          { label: "Satisfies", value: criterion.satisfies.length ? criterion.satisfies.join(", ") : "Nothing named" },
          { label: "Spec", value: <span className="font-mono text-xs">{criterion.spec}</span> },
          { label: "Tests", value: proof.length },
        ]}
      />
      <RecordSection id="proof" title="Proved by" count={proof.length} hint="The tests that carry this criterion's tag.">
        <RelatedTable label="Tests" empty="No test proves it yet." columns={[{ name: "Test", className: "w-56" }, { name: "What it checks" }]}>
          {proof.map((t) => (
            <Row key={t.id} className="cursor-pointer" onClick={() => show(t.id)}>
              <Cell><button type="button" onClick={() => show(t.id)} className="whitespace-nowrap text-left font-mono text-xs font-semibold text-link hover:underline">{t.ref}</button></Cell>
              <Cell className="text-ink-2">{t.description || muted("No description")}</Cell>
            </Row>
          ))}
        </RelatedTable>
      </RecordSection>
      <RecordSection id="closes" title="Closed by tasks" count={tasks.length} hint="The delivery tasks that name this criterion.">
        <RelatedTable label="Tasks" empty="No task names it." columns={[{ name: "Task", className: "w-56" }, { name: "What it delivers" }]}>
          {tasks.map((t) => (
            <Row key={t.id} className="cursor-pointer" onClick={() => show(t.id)}>
              <Cell><Link to={itemPath(t)} onClick={(e) => e.stopPropagation()} className="whitespace-nowrap font-mono text-xs font-semibold">{t.ref}</Link></Cell>
              <Cell className="text-ink">{t.title}</Cell>
            </Row>
          ))}
        </RelatedTable>
      </RecordSection>
    </div>
  )
}

// A neighbouring use case in brief, with the way into its own page.
export function UseCasePane({ project, uc }: { project: ProjectState; uc: UseCase }) {
  const criteria = project.criteria.filter((c) => c.uc === uc.id)
  return (
    <div className="space-y-8">
      <RecordHeader
        overline="Use case" id={uc.id} title={uc.title}
        chips={<StageChip stage={uc.stage} />}
        actions={<Link to={`/use-cases/${uc.id}`} className="t-footnote font-medium">Open as a page</Link>}
        facts={[
          { label: "Actor", value: uc.actor ?? "Not said" },
          { label: "Bounded context", value: uc.context ?? "Unassigned" },
          { label: "Wave", value: `${uc.wave} · ${uc.covered} of ${uc.enforced} criteria covered` },
          { label: "Tasks", value: `${uc.tasksClosed} of ${uc.tasks} closed` },
        ]}
      />
      <RecordSection id="next" title="Next step" hint="The one command that moves it on.">
        <CopyCommand command={uc.next} primary />
      </RecordSection>
      <RecordSection id="acs" title="Acceptance criteria" count={criteria.length}>
        <RelatedTable label="Acceptance criteria" empty="No criteria are written yet." columns={[{ name: "Criterion", className: "w-44" }, { name: "What must hold" }, { name: "State" }]}>
          {criteria.map((c) => (
            <Row key={c.id}>
              <Cell><span className="whitespace-nowrap font-mono text-[13px] font-semibold text-ink">{c.id}</span></Cell>
              <Cell className="text-ink-2">{c.text || muted("No sentence written yet.")}</Cell>
              <Cell><StateChip state={c.state} /></Cell>
            </Row>
          ))}
        </RelatedTable>
      </RecordSection>
    </div>
  )
}
