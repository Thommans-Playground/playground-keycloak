import { useEffect, useRef, useState } from "react"
import type { LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"

export interface SpySection {
  id: string
  label: string
  icon?: LucideIcon
  badge?: number // a count shown on the right
}

// What stays in view above the page: the top bar (64px) and the pinned breadcrumb (44px).
export const PINNED = 108

const reduced = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches

// Which section the reader is in: the last one, in document order, whose top has crossed a line just under the pinned
// bars. One scan, one answer per frame, so it cannot flicker the way comparing visible ratios does when sections are tall.
export function useActiveSection(ids: string[], offset = PINNED): [string | null, (id: string) => void] {
  const [active, setActive] = useState<string | null>(ids[0] ?? null)
  const holdUntil = useRef(0) // a jump keeps its choice while the page scrolls there
  const key = ids.join("|")

  useEffect(() => {
    const list = key ? key.split("|") : []
    const line = offset + 16
    let ticking = false
    const compute = () => {
      ticking = false
      if (Date.now() < holdUntil.current) return
      // At the foot of the page the last sections cannot reach the line, so the last one in view counts instead.
      const atFoot = window.scrollY > 0 && window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2
      let current: string | null = null
      for (const id of list) {
        const top = document.getElementById(id)?.getBoundingClientRect().top
        if (top !== undefined && (top <= line || (atFoot && top < window.innerHeight - 120))) current = id
      }
      setActive(current ?? list[0] ?? null)
    }
    const onScroll = () => {
      if (ticking) return
      ticking = true
      window.requestAnimationFrame(compute)
    }
    compute()
    window.addEventListener("scroll", onScroll, { passive: true })
    window.addEventListener("resize", onScroll)
    return () => {
      window.removeEventListener("scroll", onScroll)
      window.removeEventListener("resize", onScroll)
    }
  }, [key, offset])

  const jump = (id: string) => {
    const el = document.getElementById(id)
    if (!el) return
    holdUntil.current = Date.now() + 900
    window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - offset, behavior: reduced() ? "auto" : "smooth" })
    setActive(id)
  }
  return [active, jump]
}

// The section rail: it follows the reader down the page and jumps to a section. It sits in its own column beside the
// content on a wide window (the layout decides); below that, SectionChips does the same job in a row.
export function Scrollspy({ sections, active, jump }: { sections: SpySection[]; active: string | null; jump: (id: string) => void }) {
  return (
    <nav aria-label="On this page" className="sticky top-30 self-start">
      <p className="t-overline mb-2 px-3">On this page</p>
      <ul className="space-y-0.5">
        {sections.map((s) => {
          const on = active === s.id
          const Icon = s.icon
          return (
            <li key={s.id}>
              <a
                href={`#${s.id}`} aria-current={on ? "true" : undefined}
                onClick={(e) => { e.preventDefault(); jump(s.id) }}
                className={cn(
                  "flex min-h-9 select-none items-center justify-between gap-2 rounded-control px-3 text-[13px] no-underline transition-colors",
                  on ? "bg-hover font-semibold text-ink shadow-[inset_2px_0_0_var(--brand)]" : "text-muted-foreground hover:bg-hover hover:text-ink",
                )}
              >
                <span className="flex min-w-0 items-center gap-2">
                  {Icon && <Icon className="size-3.5 shrink-0" aria-hidden="true" />}
                  <span className="truncate">{s.label}</span>
                </span>
                {s.badge !== undefined && <span className="font-mono text-xs text-muted-foreground">{s.badge}</span>}
              </a>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

export function SectionChips({ sections, active, jump }: { sections: SpySection[]; active: string | null; jump: (id: string) => void }) {
  return (
    <nav aria-label="On this page" className="flex flex-wrap gap-2">
      {sections.map((s) => (
        <a
          key={s.id} href={`#${s.id}`} aria-current={active === s.id ? "true" : undefined}
          onClick={(e) => { e.preventDefault(); jump(s.id) }}
          className={cn(
            "inline-flex min-h-9 items-center gap-1.5 rounded-full px-3.5 text-[13px] font-medium no-underline",
            active === s.id ? "bg-charcoal text-white" : "bg-hover text-ink-2 hover:text-ink",
          )}
        >
          {s.label}{s.badge !== undefined && <span className="font-mono text-xs opacity-70">{s.badge}</span>}
        </a>
      ))}
    </nav>
  )
}
