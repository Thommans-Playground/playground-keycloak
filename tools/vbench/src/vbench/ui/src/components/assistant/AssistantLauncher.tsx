import { AiSparkle } from "@/components/assistant/AiSparkle"
import { LAUNCHER_ATTRIBUTE, useAssistant } from "@/components/assistant/AssistantContext"
import { isMac, shortcutLabel } from "@/lib/assistant"
import { cn } from "@/lib/utils"

// The pill in the top bar that opens and closes the panel. It is not on the page at all when the server has no assistant.
export function AssistantLauncher() {
  const { available, isOpen, toggle } = useAssistant()
  if (!available) return null
  const keys = shortcutLabel(isMac())
  return (
    <button
      type="button" onClick={toggle} {...{ [LAUNCHER_ATTRIBUTE]: "" }}
      aria-expanded={isOpen} aria-controls="assistant-panel" aria-keyshortcuts="Control+/ Meta+/"
      title={`Ask the assistant (${keys})`}
      className={cn(
        "inline-flex min-h-9 items-center gap-2 rounded-full border border-transparent bg-[var(--ai-bg)] px-3.5 text-[13px] font-medium text-[var(--ai)] transition-colors hover:border-[var(--ai-spark)] focus-visible:outline-2 focus-visible:outline-ring",
        isOpen && "border-[var(--ai-spark)]",
      )}
    >
      <AiSparkle size={14} />
      <span>Ask</span>
      <kbd className="hidden rounded border border-border bg-surface px-1.5 py-px font-mono text-[11px] font-normal text-muted-foreground md:inline">{keys}</kbd>
    </button>
  )
}
