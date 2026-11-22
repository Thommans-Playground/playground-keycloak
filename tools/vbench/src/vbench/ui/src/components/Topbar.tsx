import { GitBranch, RefreshCw } from "lucide-react"

import { ProfileMenu } from "@/components/ProfileMenu"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { Gate } from "@/lib/types"

export function Topbar({ branch, gates, loading, onRefresh }: { branch?: string; gates?: Gate[]; loading: boolean; onRefresh: () => void }) {
  const failing = gates?.filter((g) => !g.ok).length ?? 0
  return (
    <div className="sticky top-0 z-30 flex min-h-16 items-center justify-between gap-3 border-b border-border bg-surface/85 px-4 backdrop-blur-md md:px-8">
      <p className="flex min-w-0 items-center gap-2 text-[13px] text-muted-foreground">
        <GitBranch className="size-4" aria-hidden="true" />
        {branch ? <span className="truncate font-mono text-ink-2">{branch}</span> : "No git branch"}
      </p>
      <div className="flex shrink-0 items-center gap-2 md:gap-3">
        {gates && (
          <Badge tone={failing ? "risk" : "ok"}>
            {failing ? `${failing} of ${gates.length} gates failing` : `All ${gates.length} gates passing`}
          </Badge>
        )}
        <Button variant="ghost" size="icon" onClick={onRefresh} aria-label="Refresh from the project files" title="Refresh from the project files">
          <RefreshCw className={loading ? "animate-spin" : ""} aria-hidden="true" />
        </Button>
        <ProfileMenu />
      </div>
    </div>
  )
}
