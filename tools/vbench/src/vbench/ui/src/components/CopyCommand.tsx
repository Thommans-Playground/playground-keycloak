import { useState } from "react"
import { Check, Copy } from "lucide-react"

import { Button } from "@/components/ui/button"

export function CopyCommand({ command, primary = false }: { command: string; primary?: boolean }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(command)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      /* the command stays visible and selectable */
    }
  }
  return (
    <div className="flex flex-wrap items-center gap-3">
      <code className="rounded-control border border-border bg-surface-2 px-3 py-2 font-mono text-[13px] text-ink">{command}</code>
      <Button variant={primary ? "default" : "secondary"} onClick={copy} aria-live="polite">
        {copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}
        {copied ? "Copied" : "Copy command"}
      </Button>
    </div>
  )
}
