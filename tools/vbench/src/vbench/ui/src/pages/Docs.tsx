import { Link, useSearchParams } from "react-router-dom"

import { useProject } from "@/components/AppShell"
import { Markdown } from "@/components/Markdown"
import { EmptyState, PageHeader } from "@/components/PageHeader"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { getFile, useText } from "@/lib/api"
import { cn } from "@/lib/utils"

export default function Docs() {
  const { docs } = useProject()
  const [params] = useSearchParams()
  const chosen = docs.find((d) => d.path === params.get("path")) ?? docs[0]
  const body = useText(chosen ? () => getFile(chosen.path) : null, chosen?.path ?? "")

  return (
    <>
      <PageHeader title="Docs" description="The project's documents, read straight from its files. Blocks marked as generated are rewritten by vbench sync." />
      {docs.length === 0 ? (
        <EmptyState>No documents were found. Run <code className="font-mono">vbench init</code> to create the docs folder.</EmptyState>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)]">
          <nav aria-label="Documents">
            <ul className="space-y-0.5">
              {docs.map((d) => (
                <li key={d.path}>
                  <Link
                    to={`/docs?path=${encodeURIComponent(d.path)}`}
                    aria-current={d.path === chosen?.path ? "page" : undefined}
                    className={cn(
                      "block min-h-11 rounded-control px-3 py-1.5 no-underline",
                      d.path === chosen?.path ? "bg-hover shadow-[inset_3px_0_0_var(--brand)]" : "hover:bg-hover",
                    )}
                  >
                    <span className="block truncate text-[13px] font-medium text-ink">{d.title}</span>
                    <span className="block truncate font-mono text-xs text-muted-foreground">{d.path}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          <Card className="min-w-0">
            <CardContent>
              {body.error ? <p className="text-sm text-muted-foreground">This document could not be read: {body.error}.</p>
                : body.text === null ? <Skeleton className="h-64 w-full" /> : <Markdown source={body.text} basePath={chosen.path} />}
            </CardContent>
          </Card>
        </div>
      )}
    </>
  )
}
