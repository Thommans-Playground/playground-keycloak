import { describe, expect, it } from "vitest"

import { initials } from "@/lib/profile"
import { parseTheme, resolveTheme } from "@/lib/theme"

describe("theme", () => {
  it("is light unless dark or system was chosen, whatever else is stored", () => {
    expect(parseTheme("dark")).toBe("dark")
    expect(parseTheme("system")).toBe("system")
    for (const v of ["", null, undefined, "light", "auto", "DARK", 3]) expect(parseTheme(v)).toBe("light")
  })

  it("resolves system to what the device prefers, and the others to themselves", () => {
    expect(resolveTheme("light", true)).toBe("light")
    expect(resolveTheme("dark", false)).toBe("dark")
    expect(resolveTheme("system", true)).toBe("dark")
    expect(resolveTheme("system", false)).toBe("light")
  })
})

describe("profile initials", () => {
  it("takes the first and last word, or the first two letters of one", () => {
    expect(initials("Sree R One")).toBe("SO")
    expect(initials("  thom  ")).toBe("TH")
    expect(initials("Ada Lovelace")).toBe("AL")
    expect(initials("")).toBe("")
    expect(initials("   ")).toBe("")
  })
})
