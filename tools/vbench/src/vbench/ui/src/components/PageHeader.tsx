import type { ReactNode } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Check, ChevronDown, ChevronRight, LayoutGrid } from "lucide-react"

import type { Switch } from "@/lib/crumbs"
import { usePopover } from "@/lib/usePopover"
import { cn } from "@/lib/utils"

export interface Crumb {
  label: string
  title?: string // the longer name, shown on hover
  to?: string
  switch?: Switch // a menu beside the crumb to go to another of the same kind
}

// The menu beside a breadcrumb: other records of the same kind, the current one marked, and a way to the whole list.
// It only navigates; nothing is set. Escape or a click elsewhere closes it; the arrow keys move through it.
function CrumbSwitch({ current, switcher }: { current: string; switcher: Switch }) {
  const { open, setOpen, root } = usePopover()
  const navigate = useNavigate()

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
        aria-label={`${current}. Go to another ${switcher.noun}`} title={`Go to another ${switcher.noun}`}
        className="grid size-8 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-hover hover:text-ink"
      >
        <ChevronDown className="size-4" aria-hidden="true" />
      </button>
      {open && (
        <div role="menu" aria-label={`Go to another ${switcher.noun}`} className="absolute left-0 top-9 z-40 max-h-80 w-80 overflow-y-auto rounded-card border border-border bg-popover p-1.5 shadow-e3">
          {switcher.items.map((item) => {
            const here = item.id === switcher.currentId
            return (
              <button
                key={item.id} role="menuitem" type="button" autoFocus={here}
                onClick={() => { setOpen(false); if (!here) navigate(item.to) }}
                className="flex min-h-11 w-full items-center gap-2.5 rounded-control px-2.5 py-1.5 text-left hover:bg-hover focus-visible:bg-hover"
              >
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[13px] font-medium text-ink">{item.label}</span>
                  {item.detail && <span className="block truncate text-xs text-muted-foreground">{item.detail}</span>}
                </span>
                {here && <Check className="size-4 shrink-0 text-ink" aria-label={`This ${switcher.noun}`} />}
              </button>
            )
          })}
          {switcher.items.length > 0 && <div className="my-1 h-px bg-divider" role="separator" />}
          <button
            role="menuitem" type="button" onClick={() => { setOpen(false); navigate(switcher.all.to) }}
            className="flex min-h-11 w-full items-center gap-2.5 rounded-control px-2.5 text-left text-[13px] text-ink hover:bg-hover focus-visible:bg-hover"
          >
            <LayoutGrid className="size-4 text-muted-foreground" aria-hidden="true" />{switcher.all.label}
          </button>
        </div>
      )}
    </div>
  )
}

// The breadcrumb stays in view under the top bar as the page scrolls, so the reader always knows where they are and
// can go up. It uses the sidebar's names; the last crumb is the page, with a menu to go to a sibling.
export function Breadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <div data-pinned-crumb className="sticky top-16 z-20 -mx-4 mb-2 flex h-11 items-center bg-page/85 px-4 backdrop-blur-md md:-mx-8 md:px-8">
      <nav aria-label="Breadcrumb" className="min-w-0">
        <ol className="flex min-w-0 flex-wrap items-center gap-1.5 text-[13px] text-muted-foreground">
          {items.map((c, i) => {
            const last = i === items.length - 1
            return (
              <li key={`${i}-${c.label}`} className="flex min-w-0 items-center gap-1.5">
                {i > 0 && <ChevronRight className="size-3.5 shrink-0" aria-hidden="true" />}
                {c.to && !last ? (
                  <Link to={c.to} className="rounded-sm text-muted-foreground no-underline transition-colors hover:text-ink" title={c.title}>{c.label}</Link>
                ) : (
                  <span aria-current={last ? "page" : undefined} className={cn("truncate", last ? "font-medium text-ink" : "")} title={c.title ?? c.label}>{c.label}</span>
                )}
                {c.switch && <CrumbSwitch current={c.label} switcher={c.switch} />}
              </li>
            )
          })}
        </ol>
      </nav>
    </div>
  )
}

export function PageHeader({ title, description, crumbs, actions }: {
  title?: ReactNode
  description?: ReactNode
  crumbs?: Crumb[]
  actions?: ReactNode
}) {
  return (
    <>
      {crumbs && <Breadcrumbs items={crumbs} />}
      {title !== undefined && (
      <header className="mb-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h1 className="t-large-title text-ink [overflow-wrap:anywhere]">{title}</h1>
            {description && <p className="t-body mt-2 max-w-3xl text-muted-foreground">{description}</p>}
          </div>
          {actions}
        </div>
      </header>
      )}
    </>
  )
}

export function EmptyState({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="rounded-card border border-dashed border-border-input bg-surface px-6 py-10 text-center">
      <p className="mx-auto max-w-md text-sm text-ink-2">{children}</p>
      {action && <div className="mt-4 flex justify-center">{action}</div>}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-card border border-border bg-surface p-5 shadow-e1">
      <p className="flex items-center gap-2 text-sm font-semibold text-ink">
        <span className="rounded-full bg-risk-bg px-2 py-0.5 text-xs text-risk-text">Could not load</span>
        The project state is not available.
      </p>
      <p className="mt-2 text-[13px] text-muted-foreground">
        {message}. Check that <code className="font-mono">vbench serve</code> is running in the project folder, then try again.
      </p>
      {onRetry && (
        <button onClick={onRetry} className="mt-3 text-[13px] font-medium text-link underline-offset-2 hover:underline">
          Try again
        </button>
      )}
    </div>
  )
}
