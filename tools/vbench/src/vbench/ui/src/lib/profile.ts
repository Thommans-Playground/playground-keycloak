import { usePref } from "@/lib/prefs"

export const NAME_KEY = "vbench-name"

// The name shown on the profile button. There are no accounts: the dashboard is local and read-only, so the name is a
// label the person gives themselves, kept in this browser.
export function useDisplayName(): [string, (name: string) => void] {
  const [name, set] = usePref(NAME_KEY)
  return [name, (n) => set(n.trim())]
}

export function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return ""
  const letters = words.length === 1 ? Array.from(words[0]).slice(0, 2) : [Array.from(words[0])[0], Array.from(words[words.length - 1])[0]]
  return letters.join("").toUpperCase()
}
