import { Settings, User } from "lucide-react"
import { Link } from "react-router-dom"

import { initials, useDisplayName } from "@/lib/profile"
import { useTheme } from "@/lib/theme"
import { usePopover } from "@/lib/usePopover"

const APPEARANCE = { light: "Light", dark: "Dark", system: "Follows your device" }

// The profile button at the end of the top bar and the menu under it. There are no accounts, so the profile is a name
// the person chooses (kept in this browser); the menu leads to Settings, where the appearance is chosen.
export function ProfileMenu() {
  const { open, setOpen, root } = usePopover()
  const [name] = useDisplayName()
  const [theme] = useTheme()
  const who = initials(name)

  const arrows = (e: React.KeyboardEvent) => {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return
    e.preventDefault()
    const rows = Array.from(root.current?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? [])
    const at = rows.indexOf(document.activeElement as HTMLElement)
    rows[(at + (e.key === "ArrowDown" ? 1 : -1) + rows.length) % rows.length]?.focus()
  }

  return (
    <div ref={root} className="relative" onKeyDown={arrows}>
      <button
        type="button" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}
        aria-label={name ? `Profile menu for ${name}` : "Profile menu"} title="Profile and settings"
        className="grid size-10 place-items-center rounded-full bg-hover text-[13px] font-semibold text-ink transition-colors hover:bg-border"
      >
        {who || <User className="size-4" aria-hidden="true" />}
      </button>
      {open && (
        <div role="menu" aria-label="Profile" className="absolute right-0 top-12 z-40 w-72 rounded-card border border-border bg-popover p-1.5 shadow-e3">
          <div className="px-2.5 py-2">
            <p className="truncate text-[15px] font-semibold text-ink">{name || "Your profile"}</p>
            <p className="text-xs text-muted-foreground">Appearance: {APPEARANCE[theme]}</p>
          </div>
          <div className="my-1 h-px bg-divider" role="separator" />
          <Link
            to="/settings" role="menuitem" autoFocus onClick={() => setOpen(false)}
            className="flex min-h-11 items-center gap-2.5 rounded-control px-2.5 text-[13px] text-ink no-underline hover:bg-hover focus-visible:bg-hover"
          >
            <Settings className="size-4 text-muted-foreground" aria-hidden="true" />Settings
          </Link>
        </div>
      )}
    </div>
  )
}
