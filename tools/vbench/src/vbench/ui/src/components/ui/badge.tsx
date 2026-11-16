import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

// Chips carry status and always pair colour with a word. There are four tones: neutral, ok, warn and risk.
// New states reuse a tone with a different word; do not add hues.
const badgeVariants = cva(
  "inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold [&_svg]:size-3",
  {
    variants: {
      tone: {
        neutral: "bg-hover text-ink-2",
        ok: "bg-ok-bg text-ok-text",
        warn: "bg-warn-bg text-warn-text",
        risk: "bg-risk-bg text-risk-text",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
)

function Badge({ className, tone, ...props }: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return <span data-slot="badge" className={cn(badgeVariants({ tone }), className)} {...props} />
}

export { Badge, badgeVariants }
