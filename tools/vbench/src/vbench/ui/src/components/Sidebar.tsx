import { useEffect, useState } from "react"
import { NavLink } from "react-router-dom"
import { FileText, LayoutDashboard, ListChecks, Network, PanelLeftClose, PanelLeftOpen, Shapes, Table2, type LucideIcon } from "lucide-react"

import { PHASE_UI } from "@/lib/phases"

import { cn } from "@/lib/utils"

type NavItem = { to: string; label: string; icon: LucideIcon; end?: boolean; countKey?: string }
const GROUPS: { label: string; sub?: string; items: NavItem[] }[] = [
  { label: "", items: [{ to: "/", label: "Overview", icon: LayoutDashboard, end: true }] },
  {
    label: "V-cycle", sub: "Specify",
    items: ["requirements", "system-design", "architecture", "module-design"].map((k) => ({ to: `/v/${k}`, label: "", icon: PHASE_UI[k].icon, countKey: k })),
  },
  { label: "", sub: "Build", items: [{ to: "/v/code", label: "", icon: PHASE_UI.code.icon, countKey: "code" }] },
  {
    label: "", sub: "Prove",
    items: ["unit", "integration", "system", "acceptance"].map((k) => ({ to: `/v/${k}`, label: "", icon: PHASE_UI[k].icon, countKey: k })),
  },
  {
    label: "Explore",
    items: [
      { to: "/use-cases", label: "Use cases", icon: ListChecks },
      { to: "/build-order", label: "Build order", icon: Network },
      { to: "/traceability", label: "Traceability", icon: Table2 },
      { to: "/diagrams", label: "Diagrams", icon: Shapes },
      { to: "/docs", label: "Docs", icon: FileText },
    ],
  },
]

export function VMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="shrink-0">
      <rect width="32" height="32" rx="8" fill="#23272F" />
      <path d="M8 9l8 15 8-15" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

const NARROW = "(max-width: 1023px)"

// On narrow screens the sidebar starts at 64px, as the design language asks; crossing the breakpoint resets it.
function useCollapsed(): [boolean, (v: boolean) => void] {
  const [collapsed, setCollapsed] = useState(() => window.matchMedia(NARROW).matches)
  useEffect(() => {
    const mq = window.matchMedia(NARROW)
    const on = (e: MediaQueryListEvent) => setCollapsed(e.matches)
    mq.addEventListener("change", on)
    return () => mq.removeEventListener("change", on)
  }, [])
  return [collapsed, setCollapsed]
}

export function Sidebar({ counts, phases }: { counts: Record<string, number>; phases: { key: string; label: string }[] }) {
  const [collapsed, setCollapsed] = useCollapsed()
  return (
    <aside
      aria-label="Main navigation"
      className={cn(
        "sticky top-0 flex max-h-screen min-h-screen shrink-0 flex-col self-start overflow-y-auto border-r border-border bg-surface transition-[width] duration-150",
        collapsed ? "w-16" : "w-60",
      )}
    >
      <div className="flex min-h-16 items-center gap-2.5 border-b border-border px-[17px]">
        <VMark />
        {!collapsed && <span className="text-[17px] font-semibold tracking-[-0.2px] text-ink">vbench</span>}
      </div>

      <nav className="flex-1 px-2.5 py-3">
        {GROUPS.map((g, gi) => (
          <div key={`${g.label}-${g.sub}-${gi}`} className={cn(gi > 0 && (g.label || g.sub ? "mt-3" : ""))}>
            {collapsed ? (
              gi > 0 && <hr className="mx-2 mb-2 border-divider" />
            ) : (
              <>
                {g.label && <p className="px-3 pb-1 pt-1 text-[11px] font-semibold uppercase tracking-wide text-subtle">{g.label}</p>}
                {g.sub && <p className="px-3 pb-0.5 text-xs font-medium text-muted-foreground">{g.sub}</p>}
              </>
            )}
            <ul className="space-y-0.5">
              {g.items.map(({ to, label, icon: Icon, end, countKey }) => {
                const text = label || phases.find((p) => p.key === countKey)?.label || ""
                const n = countKey ? counts[countKey] : counts[to]
                return (
                  <li key={to}>
                    <NavLink
                      to={to}
                      end={end}
                      title={collapsed ? text : undefined}
                      aria-label={collapsed ? text : undefined}
                      className={({ isActive }) =>
                        cn(
                          "flex min-h-11 items-center gap-3 rounded-control px-3 text-sm no-underline transition-colors",
                          isActive ? "bg-hover font-semibold text-ink shadow-[inset_3px_0_0_var(--brand)]" : "font-medium text-ink-2 hover:bg-hover hover:text-ink",
                        )
                      }
                    >
                      <Icon className="size-5 shrink-0" aria-hidden="true" />
                      {!collapsed && <span className="flex-1 truncate">{text}</span>}
                      {!collapsed && n !== undefined && (
                        <span className="rounded-full bg-hover px-2 text-xs font-semibold text-muted-foreground">{n}</span>
                      )}
                    </NavLink>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-border p-2.5">
        <button
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          aria-expanded={!collapsed}
          title={collapsed ? "Expand navigation" : "Collapse navigation"}
          className="flex min-h-11 w-full items-center gap-3 rounded-control px-3 text-sm font-medium text-ink-2 hover:bg-hover"
        >
          {collapsed ? <PanelLeftOpen className="size-5" aria-hidden="true" /> : <PanelLeftClose className="size-5" aria-hidden="true" />}
          {!collapsed && "Collapse"}
        </button>
      </div>
    </aside>
  )
}
