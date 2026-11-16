import { Ellipsis } from "lucide-react"
import { Fragment } from "react"

import { useChanges } from "@/components/change/ChangeContext"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { actionsFor, type ActionSpec, type Target } from "@/lib/actions"

const GROUP = { add: "Add", change: "Change" } as const

// The three dots at the end of a row or in a record's header: one quiet button that opens what can be done there. It is
// not drawn at all unless the server was started with --write, so a read-only page has nothing extra on it.
export function ActionsMenu({ target, name }: { target: Target; name: string }) {
  const { session, open } = useChanges()
  if (!session.write) return null
  const specs = actionsFor(target)
  const groups = (["add", "change"] as const).map((g) => ({ g, items: specs.filter((s) => s.group === g) })).filter((x) => x.items.length)

  const item = (s: ActionSpec) => (
    <DropdownMenuItem key={s.key} variant={s.destructive ? "destructive" : "default"} disabled={Boolean(s.unavailable)} onClick={() => open(s.intent)}>
      <span className="min-w-0">
        <span className="block">{s.label}</span>
        {s.unavailable && <span className="t-caption block text-muted-foreground">{s.unavailable}</span>}
      </span>
    </DropdownMenuItem>
  )

  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant="ghost" size="icon" aria-label={`Actions for ${name}`} title="Actions" />}>
        <Ellipsis aria-hidden="true" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {groups.map(({ g, items }, i) => (
          <Fragment key={g}>
            {i > 0 && <DropdownMenuSeparator />}
            <DropdownMenuGroup>
              <DropdownMenuLabel>{GROUP[g]}</DropdownMenuLabel>
              {items.map(item)}
            </DropdownMenuGroup>
          </Fragment>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
