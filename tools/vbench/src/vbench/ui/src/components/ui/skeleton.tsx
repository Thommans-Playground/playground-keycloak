import { cn } from "@/lib/utils"

// Loading is a skeleton in the hover grey, never a spinner over content.
function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return <div data-slot="skeleton" aria-hidden="true" className={cn("animate-pulse rounded-control bg-hover", className)} {...props} />
}

export { Skeleton }
