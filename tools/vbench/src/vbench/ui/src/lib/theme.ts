import { useEffect } from "react"

import { usePref } from "@/lib/prefs"

// Light is the default. "System" follows the device and is resolved to light or dark, so the stylesheet only ever
// needs to know two appearances (`data-theme` on the html element).
export type Theme = "light" | "dark" | "system"
export const THEME_KEY = "vbench-theme"
export const THEMES: Theme[] = ["light", "dark", "system"]

export function parseTheme(value: unknown): Theme {
  return value === "dark" || value === "system" ? value : "light"
}

export function resolveTheme(theme: Theme, systemDark: boolean): "light" | "dark" {
  return theme === "dark" || (theme === "system" && systemDark) ? "dark" : "light"
}

export function useTheme(): [Theme, (t: Theme) => void] {
  const [raw, set] = usePref(THEME_KEY)
  return [parseTheme(raw), (t) => set(t === "light" ? "" : t)]
}

// Keeps the html element in step with the choice, and with the device while the choice is "system".
export function useApplyTheme(): void {
  const [theme] = useTheme()
  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: dark)")
    const apply = () => {
      document.documentElement.dataset.theme = resolveTheme(theme, query.matches)
    }
    apply()
    if (theme !== "system") return
    query.addEventListener("change", apply)
    return () => query.removeEventListener("change", apply)
  }, [theme])
}
