import { ringArcs, type RingSlice } from "@/lib/ring"
import { cn } from "@/lib/utils"

const R = 40

/**
 * A donut for one whole in a few parts, with the number that matters in the middle and the parts as buttons under
 * it. Pressing a slice or its button calls `onSelect` (pressing the one in force again clears it); the slices a
 * filter leaves out are faded. Meant to drive a list: the ring says how the whole divides, the list shows the parts.
 */
export function Ring({ slices, centre, selected, onSelect, description, size = 132, compact = false }: {
  slices: RingSlice[]
  centre: { value: string | number; label: string }
  selected?: string | null
  onSelect?: (key: string | null) => void
  description: string
  size?: number
  compact?: boolean // hide the button legend (a small ring on a card)
}) {
  const arcs = ringArcs(slices, R)
  const pick = (key: string) => onSelect?.(selected === key ? null : key)
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative" style={{ width: size, height: size }}>
        <svg viewBox="0 0 100 100" role="img" aria-label={description} className="size-full -rotate-90">
          <circle cx="50" cy="50" r={R} fill="none" stroke="var(--hover)" strokeWidth="13" />
          {arcs.map((a) => (
            <circle
              key={a.key} cx="50" cy="50" r={R} fill="none" stroke={a.colour} strokeWidth="13" strokeDasharray={a.dash}
              strokeDashoffset={a.offset} onClick={onSelect ? () => pick(a.key) : undefined}
              className={cn("transition-[stroke-dasharray,opacity] duration-500 motion-reduce:transition-none", onSelect && "cursor-pointer")}
              style={{ opacity: selected && selected !== a.key ? 0.25 : 1 }}
            >
              <title>{`${a.label}: ${a.value}`}</title>
            </circle>
          ))}
        </svg>
        <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
          <div>
            <p className="font-mono text-2xl font-semibold leading-none text-ink">{centre.value}</p>
            <p className="mt-1 max-w-[6.5rem] text-[11px] leading-tight text-muted-foreground">{centre.label}</p>
          </div>
        </div>
      </div>
      {!compact && (
        <ul className="flex flex-wrap justify-center gap-1.5" aria-label="Parts of the whole">
          {slices.map((s) => (
            <li key={s.key}>
              <button
                type="button" onClick={onSelect ? () => pick(s.key) : undefined} aria-pressed={onSelect ? selected === s.key : undefined}
                disabled={!onSelect}
                className={cn(
                  "inline-flex min-h-8 items-center gap-1.5 rounded-full border px-2.5 text-xs font-medium",
                  selected === s.key ? "border-charcoal bg-hover text-ink" : "border-border bg-surface text-ink-2",
                  onSelect && "hover:bg-hover",
                  s.value === 0 && "opacity-50",
                )}
              >
                <span className="size-2.5 rounded-full" style={{ background: s.colour }} aria-hidden="true" />
                {s.label}
                <span className="font-mono text-muted-foreground">{s.value}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
