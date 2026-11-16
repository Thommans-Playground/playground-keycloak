import { useCallback, useSyncExternalStore } from "react"

// Preferences kept in this browser only. Storage can be blocked or full (a private window, site data cleared), so every
// read and write is guarded and the page works without it. A change is announced so every component that shows the
// preference updates, in this tab and in another.
const CHANGED = "vbench-pref"
const memory = new Map<string, string>() // what storage could not keep: the choice lasts until the page is closed

export function readPref(key: string): string | null {
  try {
    return localStorage.getItem(key)
  } catch {
    return memory.get(key) ?? null
  }
}

export function writePref(key: string, value: string): void {
  if (value) memory.set(key, value)
  else memory.delete(key)
  try {
    if (value) localStorage.setItem(key, value)
    else localStorage.removeItem(key)
  } catch {
    /* kept in memory above */
  }
  window.dispatchEvent(new CustomEvent(CHANGED, { detail: key }))
}

export function usePref(key: string): [string, (value: string) => void] {
  const subscribe = useCallback(
    (notify: () => void) => {
      const on = (e: Event) => (e instanceof StorageEvent ? e.key === key || e.key === null : (e as CustomEvent).detail === key) && notify()
      window.addEventListener(CHANGED, on)
      window.addEventListener("storage", on)
      return () => {
        window.removeEventListener(CHANGED, on)
        window.removeEventListener("storage", on)
      }
    },
    [key],
  )
  const value = useSyncExternalStore(subscribe, () => readPref(key) ?? "", () => "")
  return [value, useCallback((v: string) => writePref(key, v), [key])]
}
