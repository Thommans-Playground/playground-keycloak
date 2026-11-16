import { Link, useSearchParams } from "react-router-dom"

import { useProject } from "@/components/AppShell"
import { EmptyState, PageHeader } from "@/components/PageHeader"
import { PlantUml } from "@/components/PlantUml"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export default function Diagrams() {
  const { diagrams } = useProject()
  const [params] = useSearchParams()
  const chosen = diagrams.find((d) => d.path === params.get("path")) ?? diagrams[0]
  const system = diagrams.filter((d) => !d.uc)
  const perUc = diagrams.filter((d) => d.uc)

  return (
    <>
      <PageHeader title="Diagrams" description="PlantUML files from the project, drawn by the renderer service. The use-case map is generated from the spec headers." />
      {diagrams.length === 0 ? (
        <EmptyState>No diagrams yet. They appear as use cases are designed.</EmptyState>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)]">
          <nav aria-label="Diagrams" className="space-y-4">
            <Group title="System" items={system} chosen={chosen?.path} />
            <Group title="Use cases" items={perUc} chosen={chosen?.path} />
          </nav>
          <Card className="min-w-0">
            <CardContent>
              {chosen && (
                <>
                  <div className="mb-4 flex flex-wrap items-center gap-2">
                    {chosen.title && <h2 className="t-headline basis-full text-ink">{chosen.title}</h2>}
                    <Badge>{chosen.kind}</Badge>
                    {chosen.generated && <Badge tone="warn">Generated, do not edit</Badge>}
                    <span className="font-mono text-xs text-muted-foreground">{chosen.path}</span>
                  </div>
                  {chosen.generated && (
                    <p className="mb-4 text-[13px] text-muted-foreground">Change a spec header (actor, bounded context, dependencies) and run <code className="font-mono">vbench sync</code> instead.</p>
                  )}
                  <PlantUml path={chosen.path} />
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
}

function Group({ title, items, chosen }: { title: string; items: { path: string; kind: string; title: string }[]; chosen?: string }) {
  if (items.length === 0) return null
  return (
    <div>
      <p className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wide text-subtle">{title}</p>
      <ul className="space-y-0.5">
        {items.map((d) => (
          <li key={d.path}>
            <Link
              to={`/diagrams?path=${encodeURIComponent(d.path)}`}
              aria-current={d.path === chosen ? "page" : undefined}
              className={cn(
                "block min-h-11 rounded-control px-3 py-1.5 no-underline",
                d.path === chosen ? "bg-hover shadow-[inset_3px_0_0_var(--brand)]" : "hover:bg-hover",
              )}
            >
              <span className="block truncate text-[13px] font-medium text-ink">{d.title || d.path.split("/").pop()}</span>
              <span className="block truncate font-mono text-xs text-muted-foreground">{d.path.split("/").pop()}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
