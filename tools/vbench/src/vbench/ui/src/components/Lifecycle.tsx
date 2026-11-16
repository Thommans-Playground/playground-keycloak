import { Check } from "lucide-react"

import { cn } from "@/lib/utils"
import { STAGES } from "@/lib/stages"
import type { Stage } from "@/lib/types"

// Numbered steps: done steps are green, the current step has a charcoal ring, future steps are grey.
export function Lifecycle({ stage }: { stage: Stage }) {
  const current = STAGES.findIndex((s) => s.key === stage)
  return (
    <ol className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:grid-cols-5" aria-label="Where this use case is on the V-cycle">
      {STAGES.map((s, i) => {
        const done = i < current || (stage === "verify" && i === current)
        const now = i === current && stage !== "verify"
        return (
          <li key={s.key} className="min-w-0" aria-current={now ? "step" : undefined}>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "grid size-7 shrink-0 place-items-center rounded-full border text-xs font-semibold",
                  done && "border-ok bg-ok text-white",
                  now && "border-charcoal bg-surface text-ink ring-2 ring-charcoal ring-offset-1",
                  !done && !now && "border-border-input bg-hover text-muted-foreground",
                )}
              >
                {done ? <Check className="size-4" aria-hidden="true" /> : i + 1}
              </span>
              <span className={cn("truncate text-[13px] font-semibold", now ? "text-ink" : "text-ink-2")}>{s.step}</span>
            </div>
            <p className="mt-1 pl-9 text-xs text-muted-foreground">{done ? "Done" : now ? s.hint : "Not started"}</p>
          </li>
        )
      })}
    </ol>
  )
}
