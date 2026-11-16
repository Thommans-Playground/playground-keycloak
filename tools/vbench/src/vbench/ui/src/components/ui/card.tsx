import * as React from "react"

import { cn } from "@/lib/utils"

// Cards rest at elevation 1. Only interactive cards lift on hover.
function Card({ className, interactive, ...props }: React.ComponentProps<"div"> & { interactive?: boolean }) {
  return (
    <div
      data-slot="card"
      className={cn(
        "rounded-card border border-border bg-card text-card-foreground shadow-e1",
        interactive && "transition-[box-shadow,transform] duration-200 hover:-translate-y-px hover:shadow-e2",
        className,
      )}
      {...props}
    />
  )
}

function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div data-slot="card-header" className={cn("flex items-start justify-between gap-3 px-5 pt-5", className)} {...props} />
}

function CardTitle({ className, ...props }: React.ComponentProps<"h3">) {
  return <h3 data-slot="card-title" className={cn("text-[15px] font-semibold text-ink", className)} {...props} />
}

function CardDescription({ className, ...props }: React.ComponentProps<"p">) {
  return <p data-slot="card-description" className={cn("text-[13px] text-muted-foreground", className)} {...props} />
}

function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return <div data-slot="card-content" className={cn("px-5 py-4", className)} {...props} />
}

export { Card, CardHeader, CardTitle, CardDescription, CardContent }
