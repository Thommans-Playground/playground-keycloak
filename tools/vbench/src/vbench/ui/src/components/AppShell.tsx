import { useEffect } from "react"
import { Outlet, useLocation, useOutletContext } from "react-router-dom"

import { AssistantProvider } from "@/components/assistant/AssistantContext"
import { AssistantDock } from "@/components/assistant/AssistantPanel"
import { ChangeProvider } from "@/components/change/ChangeContext"
import { ErrorState } from "@/components/PageHeader"
import { Sidebar } from "@/components/Sidebar"
import { Topbar } from "@/components/Topbar"
import { Skeleton } from "@/components/ui/skeleton"
import { useApplyTheme } from "@/lib/theme"
import { useProjectState, type Loaded } from "@/lib/api"
import type { ProjectState } from "@/lib/types"

export function useProject(): ProjectState {
  return useOutletContext<{ project: ProjectState }>().project
}

export function AppShell() {
  useApplyTheme()
  const { hash, pathname } = useLocation()
  const state: Loaded<ProjectState> = useProjectState()
  const { data, error, loading, reload } = state
  const ready = Boolean(data)

  // A new page starts at the top; a link to #section scrolls to it once the page has its content (sections keep a margin
  // under the pinned bars).
  useEffect(() => {
    if (!hash) window.scrollTo({ top: 0 })
  }, [pathname, hash])
  useEffect(() => {
    if (!hash || !ready) return
    const t = window.setTimeout(() => document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView({ block: "start" }), 60)
    return () => window.clearTimeout(t)
  }, [hash, pathname, ready])

  return (
    <AssistantProvider>
    <div className="flex min-h-screen">
      <Sidebar
        phases={data?.v.phases ?? []}
        counts={
          data
            ? {
                "/use-cases": data.useCases.length, "/docs": data.docs.length, "/diagrams": data.diagrams.length,
                ...Object.fromEntries(data.v.phases.map((p) => [p.key, data.v.items.filter((i) => i.phase === p.key).length])),
              }
            : {}
        }
      />
      <div className="min-w-0 flex-1">
        <Topbar branch={data?.branch} gates={data?.gates} loading={loading} onRefresh={reload} />
        <main className="mx-auto max-w-[1360px] px-4 py-6 md:px-8 md:py-8">
          {error && !data ? (
            <ErrorState message={error} onRetry={reload} />
          ) : data ? (
            <ChangeProvider project={data} reload={reload}>
              <Outlet context={{ project: data }} />
            </ChangeProvider>
          ) : (
            <div className="space-y-4" aria-busy="true" aria-label="Loading the project">
              <Skeleton className="h-10 w-72" />
              <Skeleton className="h-40 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          )}
        </main>
      </div>
      <AssistantDock />
    </div>
    </AssistantProvider>
  )
}
