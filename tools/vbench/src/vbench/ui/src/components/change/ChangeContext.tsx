import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react"
import { Plus } from "lucide-react"

import { ChangeSheet, type Intent } from "@/components/change/ChangeSheet"
import { Button } from "@/components/ui/button"
import type { Session } from "@/lib/changes"
import type { ProjectState } from "@/lib/types"
import { READ_ONLY, useSession } from "@/lib/write"

interface Changes {
  session: Session
  open: (intent: Intent) => void
}

const Ctx = createContext<Changes>({ session: READ_ONLY, open: () => {} })
export const useChanges = () => useContext(Ctx)

// Holds the one change panel, and whether the server lets the page write at all.
export function ChangeProvider({ project, reload, children }: { project: ProjectState; reload: () => void; children: ReactNode }) {
  const session = useSession()
  const [intent, setIntent] = useState<Intent | null>(null)
  const open = useCallback((i: Intent) => session.write && setIntent(i), [session.write])
  const value = useMemo(() => ({ session, open }), [session, open])
  return (
    <Ctx.Provider value={value}>
      {children}
      {intent && <ChangeSheet key={`${intent.op}-${intent.kind}-${intent.id ?? "new"}`} intent={intent} project={project} session={session} reload={reload} onClose={() => setIntent(null)} />}
    </Ctx.Provider>
  )
}

// A button that opens the panel. It is not shown at all unless the server was started with --write.
export function ChangeButton({ intent, label, variant = "secondary", add = false }: { intent: Intent; label: string; variant?: "secondary" | "default" | "destructive" | "ghost"; add?: boolean }) {
  const { session, open } = useChanges()
  if (!session.write) return null
  return (
    <Button variant={variant} size="sm" onClick={() => open(intent)}>
      {add && <Plus aria-hidden="true" />}{label}
    </Button>
  )
}
