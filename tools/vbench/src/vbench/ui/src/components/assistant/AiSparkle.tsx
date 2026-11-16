// The mark for anything the assistant writes or is asked: a small four-point sparkle in the AI violet.
export function AiSparkle({ size = 14, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" className={className} fill="currentColor">
      <path d="M12 2c.6 4.9 2.8 7.1 8 8-5.2.9-7.4 3.1-8 8-.6-4.9-2.8-7.1-8-8 5.2-.9 7.4-3.1 8-8Z" />
      <path d="M19 15.5c.3 2 1.1 2.8 3 3.2-1.9.4-2.7 1.2-3 3.3-.3-2.1-1.1-2.9-3-3.3 1.9-.4 2.7-1.2 3-3.2Z" opacity=".7" />
    </svg>
  )
}
