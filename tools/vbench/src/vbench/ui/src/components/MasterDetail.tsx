import { useRef, type KeyboardEvent, type ReactNode } from "react"

import { cn } from "@/lib/utils"

export interface Group<T> {
  key: string
  label: string
  items: T[]
}

// A list that stays in view on the left and the chosen entry in full on the right; the page is what scrolls.
// The reader moves by choosing: a click, or the arrow keys, Home and End inside the list (one stop for Tab).
// Scrolling never changes what is shown. On a narrow window the two stack.
export function MasterDetail<T>({ groups, getId, selectedId, onSelect, row, toolbar, detail, empty, label }: {
  groups: Group<T>[]
  getId: (item: T) => string
  selectedId: string | undefined
  onSelect: (item: T) => void
  row: (item: T, selected: boolean) => ReactNode
  toolbar?: ReactNode
  detail: ReactNode
  empty: ReactNode
  label: string
}) {
  const list = useRef<HTMLDivElement>(null)
  const flat = groups.flatMap((g) => g.items)

  const move = (e: KeyboardEvent) => {
    const keys = ["ArrowDown", "ArrowUp", "Home", "End"]
    if (!keys.includes(e.key) || flat.length === 0) return
    e.preventDefault()
    const at = flat.findIndex((i) => getId(i) === selectedId)
    const to = e.key === "Home" ? 0 : e.key === "End" ? flat.length - 1 : Math.min(flat.length - 1, Math.max(0, at + (e.key === "ArrowDown" ? 1 : -1)))
    const next = flat[to]
    onSelect(next)
    const id = getId(next)
    requestAnimationFrame(() => list.current?.querySelector<HTMLElement>(`[data-id="${CSS.escape(id)}"]`)?.focus())
  }

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <section aria-label={label} className="min-w-0 overflow-hidden rounded-card border border-border bg-surface shadow-e1 lg:sticky lg:top-28 lg:flex lg:max-h-[calc(100vh-8.5rem)] lg:flex-col">
        {toolbar && <div className="border-b border-border p-3">{toolbar}</div>}
        {flat.length === 0 ? (
          <div className="p-4 text-[13px] text-muted-foreground">{empty}</div>
        ) : (
          <div ref={list} role="listbox" aria-label={label} onKeyDown={move} className="min-h-0 overflow-y-auto">
            {groups.filter((g) => g.items.length).map((g) => (
              <div key={g.key} role="group" aria-label={g.label}>
                <p className="sticky top-0 z-[1] border-b border-border bg-surface-2 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  {g.label} <span className="font-mono normal-case">{g.items.length}</span>
                </p>
                {g.items.map((item) => {
                  const id = getId(item)
                  const selected = id === selectedId
                  return (
                    <button
                      key={id} type="button" role="option" aria-selected={selected} data-id={id}
                      tabIndex={selected || (!selectedId && item === flat[0]) ? 0 : -1}
                      onClick={() => onSelect(item)}
                      className={cn(
                        "flex min-h-11 w-full items-center gap-3 border-b border-border px-4 py-2 text-left text-[13px] last:border-b-0 hover:bg-hover focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring",
                        selected && "bg-hover shadow-[inset_3px_0_0_var(--brand)]",
                      )}
                    >
                      {row(item, selected)}
                    </button>
                  )
                })}
              </div>
            ))}
          </div>
        )}
      </section>
      <div className="min-w-0">{detail}</div>
    </div>
  )
}
